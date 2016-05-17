#!/usr/bin/env python3

'''
A collection of values for other modules to use. If you wish to use a different
source of data, this is the place to modify.
'''

import os
import pkg_resources

BASE_PATH = 'fuzzdb/attack'

__all__ = ['get_strings', 'get_integers', 'get_floats']


def _open_fuzzdb_file(path):
    'Helper to access files within fuzzdb'
    return pkg_resources.resource_stream('protofuzz', path)


def _limit_helper(stream, limit):
    'Limit a stream depending on the "limit" parameter'
    for value in stream:
        yield value
        if limit == 1:
            return
        else:
            limit = limit - 1


def _fuzzdb_integers(limit=0):
    'Helper to grab some integers from fuzzdb'
    path = os.path.join(BASE_PATH, 'integer-overflow/integer-overflows.txt')
    stream = _open_fuzzdb_file(path)
    for line in _limit_helper(stream, limit):
        yield int(line.decode('utf-8'), 0)


def _fuzzdb_get_strings(max_len=0):
    'Helper to get all the strings from fuzzdb'

    ignored = ['integer-overflow']

    for subdir in pkg_resources.resource_listdir('protofuzz', BASE_PATH):
        if subdir in ignored:
            continue

        path = '{}/{}'.format(BASE_PATH, subdir)
        listing = pkg_resources.resource_listdir('protofuzz', path)
        for filename in listing:
            if not filename.endswith('.txt'):
                continue

            path = '{}/{}/{}'.format(BASE_PATH, subdir, filename)
            source = _open_fuzzdb_file(path)
            for line in source:
                string = line.decode('utf-8').strip()
                if not string or string.startswith('#'):
                    continue
                if max_len != 0 and len(line) > max_len:
                    continue

                yield string


def get_strings(max_len=0, limit=0):
    '''
    Get strings from the fuzzdb database.

      limit - Limit results to |limit| results, or 0 for unlimited.
      max_len - Maximum length of string required
    '''
    return _limit_helper(_fuzzdb_get_strings(max_len), limit)


def get_integers(bitwidth, unsigned, limit=0):
    '''
    Get integers from fuzzdb database

      bitwidth - The bitwidth that has to contain the integer
      unsigned - Whether the type is unsigned
      limit - Limit to |limit| results
    '''
    if unsigned:
        start, stop = 0, ((1 << bitwidth) - 1)
    else:
        start, stop = (-(1 << bitwidth-1)), (1 << (bitwidth-1)-1)

    for num in _fuzzdb_integers(limit):
        if num >= start and num <= stop:
            yield num


def get_floats(bitwidth, limit=0):
    '''
    Return a number of interesting floating point values
    '''
    assert bitwidth in (32, 64, 80)

    values = [0.0, -1.0, 1.0, -1231231231231.0123, 123123123123123.123]
    for val in _limit_helper(values, limit):
        yield val
