#!/usr/bin/env python3

import os
import re
import stat
import shutil
import tempfile
import unittest

from protofuzz import pbimport, _compile_proto


class TestPbimport(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_find_protoc(self):
        """
        Can we can find protoc?
        """
        binary = os.path.join(self.tempdir, 'protoc')
        with open(binary, 'wb+') as f:
            pass
        mode = os.stat(binary)
        os.chmod(binary, mode.st_mode | stat.S_IEXEC)

        found_binary = pbimport.find_protoc(self.tempdir)
        self.assertEqual(found_binary, binary)

    def test_from_string(self):
        """
        Get a protobuf module from string
        """
        name = 'Msg'
        contents = 'message {} {{ required int32 var = 1; }}\n'.format(name)

        module = pbimport.from_string(contents)
        self.assertTrue(hasattr(module, name))

    def test_from_generated(self):
        """
        Get a protobuf module from generated file
        """
        name = 'Msg'
        contents = 'message {} {{ required int32 var = 1; }}\n'.format(name)

        filename = os.path.join(self.tempdir, "test.proto")
        with open(filename, 'w') as f:
            f.write(contents)
    
        dest = self.tempdir
        full_path = os.path.abspath(proto_file)
        _compile_proto(full_path, dest)

        filename = os.path.split(full_path)[-1]
        name = re.search(r'^(.*)\.proto$', filename).group(1)
        target = os.path.join(dest, name+'_pb2.py')

        module = pbimport.from_file(target)
        self.assertTrue(hasattr(module, name))

    def test_failing_import(self):
        """
        Test the failing of malformed generated protobuf file
        """
        contents = 'malformed generated code'

        filename = os.path.join(self.tempdir, "test_pb2.py")
        with open(filename, 'w') as f:
            f.write(contents)
    
        with self.assertRaises(AttributeError):
            module = pbimport.from_file(filename)

    def test_failing_import_not_found(self):
        """
        Get a protobuf module from generated file
        """
        filename = os.path.join(self.tempdir, "test_pb2.py")
    
        with self.assertRaises(FileNotFoundError):
            module = pbimport.from_file(filename)

    def test_generate_and_import(self):
        """
        Test generation and loading of protobuf artifacts
        """
        name = 'Msg'
        contents = 'message {} {{ required int32 var = 1; }}\n'.format(name)

        filename = os.path.join(self.tempdir, "test.proto")
        with open(filename, 'w') as f:
            f.write(contents)

        module = pbimport.from_file(filename)
        self.assertTrue(hasattr(module, name))

    def test_failing_generate_and_import(self):
        """
        Test the failing of malformed protoc file
        """
        contents = 'malformed protoc'

        filename = os.path.join(self.tempdir, "test.proto")
        with open(filename, 'w') as f:
            f.write(contents)

        with self.assertRaises(pbimport.BadProtobuf):
            module = pbimport.from_file(filename)
