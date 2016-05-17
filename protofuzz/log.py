#!/usr/bin/env python3

'''
Utility logging class that is useful when running fuzzing campaigns.
'''

import os
import pickle

__all__ = ['Logger', 'LastNMessagesLogger']


class Logger(object):
    '''
    Base class for a fuzzing logger.
    '''
    def __init__(self, filename):
        self._filename = filename

    def log(self, item):
        '''
        Log the protobuf object |item|
        '''
        raise NotImplementedError("Must implement log()")

    def get(self):
        '''
        Return all the entries in the buffer
        '''
        raise NotImplementedError("Must implement get()")


class LastNMessagesLogger(Logger):
    '''
    Maintain the last N messages in a file. Ensure messages are persisted to
    disk during every write.
    '''
    def __init__(self, filename, size=0):
        super().__init__(filename)
        self._size = size

    def log(self, obj):
        '''
        Commit an arbitrary (picklable) object to the log
        '''
        entries = self.get()
        entries.append(obj)
        # Only log the last |n| entries if set
        if self._size > 0:
            entries = entries[-self._size:]
        self._write_entries(entries)

    def get(self):
        # First, read the contents of the file
        entries = []
        if not os.path.exists(self._filename):
            return entries

        log_file = open(self._filename, 'rb')
        while log_file.peek():
            entries.append(pickle.load(log_file))
        log_file.close()

        return entries

    def _write_entries(self, entries):
        log_file = open(self._filename, 'wb')
        try:
            log_file.seek(0)
            for entry in entries:
                pickle.dump(entry, log_file, pickle.HIGHEST_PROTOCOL)
            log_file.flush()
            os.fsync(log_file.fileno())
        finally:
            log_file.close()
