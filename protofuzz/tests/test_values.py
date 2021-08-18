#!/usr/bin/env python3

import unittest

from protofuzz import values


class TestValues(unittest.TestCase):
    def test_get_all_strings(self):
        """Get all strings from fuzzdb"""
        vals = list(values.get_strings())
        self.assertTrue(len(vals) > 0)

    def test_some_strings(self):
        """Get a few strings from fuzzdb"""
        vals = list(values.get_strings(limit=10))
        self.assertEqual(len(vals), 10)

    def test_floats(self):
        vals = values.get_floats(32)
        for val in vals:
            self.assertIsInstance(val, float)
