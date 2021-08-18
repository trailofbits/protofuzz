#!/usr/bin/env python3

from protofuzz import gen

import unittest


class TestGenerators(unittest.TestCase):
    def test_name(self):
        """Test setting a name"""
        name = "A Name"
        generator = gen.IterValueGenerator("name", [])
        generator.set_name(name)

        self.assertEqual(generator.name(), name)

    def test_basic_gen(self):
        """Test a basic generator"""
        source_vals = [1, 2, 3, 4]
        numbers = gen.IterValueGenerator("iter", source_vals)
        produced_vals = []

        for x in numbers:
            produced_vals.append(x)

        self.assertEqual(produced_vals, source_vals)

    def test_gen_init(self):
        """Test that we can't get a value from a non-iterated generator"""
        values = gen.IterValueGenerator("iter", [1, 2, 3, 4])

        with self.assertRaises(RuntimeError):
            values.get()

    def test_dependent_values(self):
        """Make sure dependent values are correctly resolved"""

        def is_even(x):
            return x % 2 == 0

        values = gen.IterValueGenerator("name", [1, 2, 3, 4])
        dependent = gen.DependentValueGenerator(
            "depends", target=values, action=is_even
        )

        for x in values:
            generated_val, generated_dependency = values.get(), dependent.get()
            self.assertEqual(generated_dependency, is_even(generated_val))

    def test_repeated_gets(self):
        """Make sure that calling get() twice on a generator does not advance it"""

        def plus_one(x):
            return x + 1

        values = gen.IterValueGenerator("name", [1, 2, 3, 4])
        dependent = gen.DependentValueGenerator(
            "dependent", target=values, action=plus_one
        )

        # Request an actual item
        next(iter(values))

        values.get()

        first = dependent.get()
        second = dependent.get()

        self.assertEqual(first, second)

    def test_permuted_generators(self):
        """Test basic Product() permuter"""
        values1 = gen.IterValueGenerator("a", [1, 2])
        values2 = gen.IterValueGenerator("b", [1, 2])
        produced_vals = []

        for x in gen.Product("name", values1, values2):
            x = tuple(map(lambda e: e[1], x))
            produced_vals.append(x)

        self.assertEqual(produced_vals, [(1, 1), (1, 2), (2, 1), (2, 2)])

    def test_permuted_generators_with_dependent_values(self):
        """Test that Product permuter works with dependent values"""

        def is_even(x):
            return x % 2 == 0

        values1 = gen.IterValueGenerator("a", [1, 2, 3])
        values2 = gen.IterValueGenerator("b", [1, 2, 3])
        values3 = gen.IterValueGenerator("c", [1, 2, 3])
        dependent = gen.DependentValueGenerator("v1", target=values1, action=is_even)

        for x in gen.Product("name", values1, values2, values3, dependent):
            v1, v2, v3, dep = x
            self.assertEqual(is_even(values1.get()), dependent.get())

    def test_permuted_generators_with_via_make_dep(self):
        """Test creation of dependencies via Permuter.make_dependent()"""
        names = gen.IterValueGenerator("name", ["alice", "bob"])
        lengths = gen.IterValueGenerator("len", ["one", "two"])
        permuter = gen.Zip("Permute", names, lengths)

        permuter.make_dependent("len", "name", len)

        for tuples in permuter:
            values = dict(tuples)
            self.assertEqual(len(values["name"]), values["len"])

    def test_zip(self):
        """Test a basic Zip permuter"""
        source_vals = [1, 2, 3, 4]
        vals1 = gen.IterValueGenerator("key", source_vals)
        vals2 = gen.IterValueGenerator("val", source_vals)

        produced_via_zips = []
        for x, y in gen.Zip("name", vals1, vals2):
            produced_via_zips.append((x[1], y[1]))

        expected = list(zip(source_vals, source_vals))
        self.assertEqual(produced_via_zips, expected)

    def test_limited_gen(self):
        source_vals = list(range(4))
        limit = 3
        values = gen.IterValueGenerator("name", source_vals)
        values.set_limit(limit)

        produced_vals = [val for val in values]
        self.assertEqual(source_vals[:limit], produced_vals)

    def test_limited_zip(self):
        """Test limits on a basic Zip iterator"""
        source_vals = [1, 2, 3, 4]
        values = gen.IterValueGenerator("name", source_vals)
        produced_vals = []

        for x in gen.Zip("name", values, limit=len(source_vals) - 1):
            produced_vals.append(x[0][1])

        self.assertEqual(source_vals[:-1], produced_vals)

    def test_limited_product(self):
        """Test limits on a Product iterator"""
        source_vals = [1, 2, 3, 4]
        vals1 = gen.IterValueGenerator("key", source_vals)
        vals2 = gen.IterValueGenerator("values", source_vals)
        produced_vals = []

        for v1, v2 in gen.Product("name", vals1, vals2, limit=4):
            produced_vals.append((v1[1], v2[1]))

        self.assertEqual(produced_vals, [(1, 1), (1, 2), (1, 3), (1, 4)])

    def test_dual_permuters(self):
        """Test nested permuters"""
        source_vals = [1, 2]
        vals1 = gen.IterValueGenerator("key", source_vals)
        vals2 = gen.IterValueGenerator("val", source_vals)

        produced_via_zips = []
        produced_via_product = []

        for x in gen.Zip("name", vals1):
            for y in gen.Zip("name", vals2):
                produced_via_zips.append(x + y)

        for x in gen.Product("name", vals1, vals2):
            produced_via_product.append(x)

        self.assertEqual(produced_via_zips, produced_via_product)

    def test_make_dependent(self):
        source_vals = [1, 2, 3, 4]
        vals1 = gen.IterValueGenerator("key", source_vals)
        vals2 = gen.IterValueGenerator("values", source_vals)

        def increment_by_one(val):
            return val + 1

        permuter = gen.Zip("test", vals1, vals2)
        permuter.make_dependent("key", "values", increment_by_one)

        for values in permuter:
            res = dict(values)
            self.assertEqual(res["key"], increment_by_one(res["values"]))
