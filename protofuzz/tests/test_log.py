#!/usr/bin/env python3

import os
import shutil
import tempfile
import unittest

from protofuzz import log


class TestLog(unittest.TestCase):
    def setUp(self):
        self.fd, self.tempfile = tempfile.mkstemp()

    def _get_logger(self, n):
        return log.LastNMessagesLogger(self.tempfile, n)

    def tearDown(self):
        os.unlink(self.tempfile)

    def test_few_msgs(self):
        """Test logging a message"""
        logger = self._get_logger(4)

        original = ["hello"]

        for obj in original:
            logger.log(obj)

        retrieved = logger.get()

        self.assertEqual(original, retrieved)

    def test_many_msgs(self):
        """Test logging a few messages"""
        logger = self._get_logger(3)

        original = ["one", "two", "three", "four"]

        for obj in original:
            logger.log(obj)

        retrieved = logger.get()

        self.assertEqual(original[-3:], retrieved)

    def test_nones(self):
        """Test with None"""
        logger = self._get_logger(1)
        logger.log(None)
        retrieved = logger.get()
        self.assertIsNone(retrieved[0])
