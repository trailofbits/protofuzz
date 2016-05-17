#!/usr/bin/env python3

'''
  gen.py -- Define a set of value generators and permuters that create tuples
   of values.
'''

__all__ = ['IterValueGenerator', 'DependentValueGenerator', 'Zip', 'Product']


class ValueGenerator(object):
    'Base class of a value generators'
    def __init__(self, name, limit=float('inf')):
        self._name = name
        self._cached_value = None
        self._limit = limit

    def name(self):
        'Return the name of the generator'
        return self._name

    def set_name(self, name):
        'Set the name of the generator'
        self._name = name

    def __iter__(self):
        return self

    def __next__(self):
        if self._limit == 0:
            raise StopIteration
        self._limit = self._limit - 1
        return self.get()

    def get(self):
        'Return the most recent value generated. [abstract'
        raise NotImplementedError("Must override get()")

    def set_limit(self, limit):
        'Set a limit on how many values we should generate'
        self._limit = limit


class IterValueGenerator(ValueGenerator):
    'Basic generator that successively returns values it was initialized with.'
    def __init__(self, name, values):
        super().__init__(name)
        self._values = values
        self._iter = None

    def __iter__(self):
        self._iter = iter(self._values)
        return self

    def __next__(self):
        self._cached_value = next(self._iter)
        super().__next__()
        return self._cached_value

    def get(self):
        if self._cached_value is None:
            raise RuntimeError("Can't get a value on a generator that isn't " +
                               " being iterated")
        return self._cached_value


class DependentValueGenerator(ValueGenerator):
    'A generator that represents a dependent value via a callable action'
    def __init__(self, name, target, action):
        super().__init__(name)
        self._target = target
        self._action = action

    def get(self):
        return self._action(self._target.get())


class Permuter(ValueGenerator):
    '''
    Base class for generators that permute multiple ValueGenerator objects.
    '''

    class MessageNotFound(RuntimeError):
        '''
        Raised if attempted to reference an unknown child generator
        '''
        pass

    def __init__(self, name, *generators, limit=float('inf')):
        super().__init__(name, limit)
        self._generators = list(generators)
        self._update_independent_generators()

    @staticmethod
    def get_independent_generators(gens):
        '''
        Return only those generators that produce their own values (as opposed
        to those that are related
        '''
        return [_ for _ in gens if not isinstance(_, DependentValueGenerator)]

    def step_generator(self, generators):
        'The actual method responsible for the permutation strategy [abstract]'
        raise NotImplementedError("Implement step_generator() in a subclass")

    def _update_independent_generators(self):
        independents = self.get_independent_generators(self._generators)
        self._independent_iterators = [iter(_) for _ in independents]
        self._step = self.step_generator(self._independent_iterators)

    def _resolve_child(self, path):
        'Return a member generator by a dot-delimited path'
        obj = self

        for component in path.split('.'):
            ptr = obj
            if not isinstance(ptr, Permuter):
                raise self.MessageNotFound("Bad element path [wrong type]")

            # pylint: disable=protected-access
            found_gen = (_ for _ in ptr._generators if _.name() == component)

            obj = next(found_gen, None)

            if not obj:
                raise self.MessageNotFound("Path '{}' unresolved to member."
                                           .format(path))
        return ptr, obj

    def make_dependent(self, source, target, action):
        '''
        Create a dependency between path 'source' and path 'target' via the
        callable 'action'.

        >>> permuter._generators
        [IterValueGenerator(one), IterValueGenerator(two)]
        >>> permuter.make_dependent('one', 'two', lambda x: x + 1)

        Going forward, 'two' will only contain values that are (one+1)
        '''
        if not self._generators:
            return

        src_permuter, src = self._resolve_child(source)
        dest = self._resolve_child(target)[1]

        # pylint: disable=protected-access
        container = src_permuter._generators
        idx = container.index(src)
        container[idx] = DependentValueGenerator(src.name(), dest, action)

        self._update_independent_generators()

    def get(self):
        'Retrieve the most recent value generated'
        # If you attempt to use a generator comprehension below, it will
        # consume the StopIteration exception and just return an empty tuple,
        # instead of stopping iteration normally
        return tuple([(x.name(), x.get()) for x in self._generators])

    def __iter__(self):
        self._update_independent_generators()
        return self

    def __next__(self):
        next(self._step)

        if self._limit == 0:
            self._step.close()
            raise StopIteration
        self._limit = self._limit-1

        return self.get()


class Zip(Permuter):
    'A permuter that is equivalent to the zip() builtin'
    def step_generator(self, generators):
        try:
            while True:
                # Step every generator in sync
                for generator in generators:
                    next(generator)
                yield
        except (StopIteration, GeneratorExit):
            return


class Product(Permuter):
    'A permuter that is equivalent to itertools.product'
    def step_generator(self, generators):
        if len(generators) < 1:
            yield ()
        else:
            first, rest = generators[0], generators[1:]
            for item in first:
                for items in self.step_generator(rest):
                    yield (item, )+items
