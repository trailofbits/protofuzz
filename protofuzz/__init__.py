#!/usr/bin/env protofuzz

'''
Protofuzz is a Google Protobuf data generator that uses fuzzdb. Usage:

  >>> from protofuzz import protofuzz, log

  >>> # Store the last 10 sent messages
  >>> logger = log.LastNMessagesLogger('logger', 10)
  >>> message_fuzzers = protofuzz.from_description_string("""
  ...     message Address {
  ...      required int32 house = 1;
  ...      required string street = 2;
  ...     }
  ... """)
  >>> fuzzer = message_fuzzers['Address']
  ... for obj in fuzzer.permute():
  ...     print("Generated object: {}".format(obj))
  ...     logger.log(obj)
  ...

'''

__all__ = ['gen', 'log', 'protofuzz', 'values']
