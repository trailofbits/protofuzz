#!/usr/bin/env python3

import os
import re
import secrets
import unittest
import tempfile

from protofuzz import protofuzz, pbimport, values


class TestProtofuzz(unittest.TestCase):
    def new_description(self):
        message = f"Message{secrets.token_hex(16)}"
        other = f"Other{secrets.token_hex(16)}"

        description = f"""
            message {message} {{
              required int32 one = 1;
              required int32 two = 2;
            }}

            message {other} {{
              required int32 one = 1;
              required int32 two = 2;
            }}
        """

        return (message, other, description)

    def test_from_string(self):
        """Make sure we can create protofuzz generators from string"""
        message, other, description = self.new_description()
        messages = protofuzz.from_description_string(description)

        self.assertIn(message, messages)
        self.assertIn(other, messages)

    def test_from_file(self):
        """Make sure we can create protofuzz generators from file"""
        message, other, description = self.new_description()
        fd, filename = tempfile.mkstemp(suffix=".proto")
        try:
            f = open(filename, "w")
            f.write(description)
            f.close()

            messages = protofuzz.from_file(filename)
        finally:
            os.unlink(filename)

        self.assertIn(message, messages)
        self.assertIn(other, messages)

    def test_from_file_generated(self):
        """Make sure we can create protofuzz generators from generated protobuf code"""
        message, other, description = self.new_description()
        fd, filename = tempfile.mkstemp(suffix=".proto")
        dest = tempfile.tempdir
        try:
            f = open(filename, "w")
            f.write(description)
            f.close()

            full_path = os.path.abspath(filename)
            pbimport._compile_proto(full_path, dest)
            temp_filename = os.path.split(full_path)[-1]
            name = re.search(r"^(.*)\.proto$", temp_filename).group(1)
            target = os.path.join(dest, name + "_pb2.py")

            messages = protofuzz.from_file(target)
            os.unlink(target)
        finally:
            os.unlink(filename)

        self.assertIn(message, messages)
        self.assertIn(other, messages)

    def test_failure_from_invalid_import_file(self):
        """Asserts invalid generated protobuf code throws exception"""
        message, other, description = self.new_description()
        fd, filename = tempfile.mkstemp(suffix="_pb2.py")
        try:
            f = open(filename, "w")
            f.write(description)
            f.close()

            with self.assertRaises(IndentationError):
                messages = protofuzz.from_file(filename)
        finally:
            os.unlink(filename)

    def test_failure_from_invalid_import_file_empty(self):
        """Asserts invalid generated protobuf code throws exception"""
        fd, filename = tempfile.mkstemp(suffix="_pb2.py")
        try:
            with self.assertRaises(AttributeError):
                messages = protofuzz.from_file(filename)
        finally:
            os.unlink(filename)

    def test_enum(self):
        """Make sure all enum values are enumerated in linear permutation"""
        enum_values = [0, 1, 2]
        definition = """
        message Message {{
            enum Colors {{ RED = {}; GREEN = {}; BLUE = {}; }}
            required Colors color = 1;
        }}
        """.format(
            *enum_values
        )

        messages = protofuzz.from_description_string(definition)

        all_values = [obj.color for obj in messages["Message"].linear()]

        # TODO(ww): Why do all_values come out in reversed order here?
        self.assertEqual(all_values, list(reversed(enum_values)))

    def test_floating_point(self):
        """Test basic doubles"""
        name = f"Msg{secrets.token_hex(16)}"
        definition = """
            message {} {{
                required double dbl = 1;
                required float fl = 2;
            }}""".format(
            name
        )
        messages = protofuzz.from_description_string(definition)
        for msg in messages[name].linear():
            self.assertIsInstance(msg.dbl, float)
            self.assertIsInstance(msg.fl, float)

    def _single_field_helper(self, field_type, field_name):
        name = f"Msg{secrets.token_hex(16)}"
        definition = """
            message {} {{
                required {} {} = 1;
            }}""".format(
            name, field_type, field_name
        )
        permuter = protofuzz.from_description_string(definition)[name]
        return permuter.linear(limit=10)

    def test_basic_types(self):
        """Test generation of strings, bools, and bytes values"""
        typemap = [("string", str), ("bool", bool), ("bytes", bytes)]
        for pbname, pyname in typemap:
            for msg in self._single_field_helper(pbname, "val"):
                self.assertIsInstance(msg.val, pyname)

    def test_repeated(self):
        name = f"Msg{secrets.token_hex(16)}"
        definition = "message {} {{ repeated string val = 1; }}".format(name)
        messages = protofuzz.from_description_string(definition)
        for msg in messages[name].linear(limit=10):
            self.assertIsInstance(msg.val[0], str)

    def test_repeated_msg(self):
        name = f"Msg{secrets.token_hex(16)}"
        definition = """
            message Inner {{ required int32 val = 1; }}
            message {} {{ repeated Inner val = 1; }}
        """.format(
            name
        )

        messages = protofuzz.from_description_string(definition)

        for msg in messages[name].linear(limit=10):
            self.assertIsInstance(msg.val[0].val, int)

    def test_optional(self):
        name = f"Msg{secrets.token_hex(16)}"
        definition = "message {} {{ optional string val = 1; }}".format(name)
        messages = protofuzz.from_description_string(definition)
        for msg in messages[name].linear(limit=10):
            self.assertIsInstance(msg.val, str)

    def permuter_helper(self, method):
        message, _, description = self.new_description()
        messages = protofuzz.from_description_string(description)
        permuter = messages[message]

        self.assertTrue(len(list(method(permuter))) > 0)

    def test_linear_fuzzing(self):
        """Linear fuzzing generates some results"""
        self.permuter_helper(lambda x: x.linear())

    def test_permuted_fuzzing(self):
        """Permuted fuzzing generates some results"""
        self.permuter_helper(lambda x: x.permute())

    def test_custom_ints(self):
        """Test a custom int generator"""
        old_intvalues = values._fuzzdb_integers
        try:
            custom_vals = [1, 2, 3, 4]

            def custom_ints(limit=0):
                return iter(custom_vals)

            values._fuzzdb_integers = custom_ints

            name = f"Msg{secrets.token_hex(16)}"
            definition = "message {} {{required int32 val = 1;}}".format(name)
            messages = protofuzz.from_description_string(definition)
            results = [x.val for x in messages[name].linear()]

            self.assertEqual(results, custom_vals)
        finally:
            values._fuzzdb_integers = old_intvalues
