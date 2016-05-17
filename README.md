# ProtoFuzz

[![Build Status](https://travis-ci.org/trailofbits/protofuzz.svg?branch=master)](https://travis-ci.org/trailofbits/protofuzz)
[![Test Coverage](https://codeclimate.com/github/trailofbits/protofuzz/badges/coverage.svg)](https://codeclimate.com/github/trailofbits/protofuzz/coverage)
[![Issue Count](https://codeclimate.com/github/trailofbits/protofuzz/badges/issue_count.svg)](https://codeclimate.com/github/trailofbits/protofuzz)
[![PyPI version](https://badge.fury.io/py/protofuzz.svg)](https://badge.fury.io/py/protofuzz)

ProtoFuzz is a generic fuzzer for Google’s Protocol Buffers format. Instead of defining a new fuzzer generator for custom binary formats, protofuzz automatically creates a fuzzer based on the same format definition that programs use. ProtoFuzz is implemented as a stand-alone Python3 program.

# Installation

Make sure you have protobuf package installed and `protoc` is accessible from $PATH, and that `protoc` can generate Python3-compatible code.

    $ git clone --recursive git@github.com:trailofbits/protofuzz.git
    $ cd protofuzz
    $ python3 setup.py install

# Usage

    >>> from protofuzz import protofuzz
    >>> message_fuzzers = protofuzz.from_description_string("""
    ...     message Address {
    ...      required int32 house = 1;
    ...      required string street = 2;
    ...     }
    ... """)
    >>> for obj in message_fuzzers['Address'].permute():
    ...     print("Generated object: {}".format(obj))
    ...
    Generated object: house: -1
    street: "!"
    
    Generated object: house: 0
    street: "!"
    
    Generated object: house: 256
    street: "!"
    ...

You can also create dependencies between arbitrary fields that are resolved with
any callable object:

    >>> message_fuzzers = protofuzz.from_description_string("""
    ...     message Address {
    ...      required int32 house = 1;
    ...      required string street = 2;
    ...     }
    ...     message Other {
    ...       required Address addr = 1;
    ...       required uint32 foo = 2;
    ...     }
    ... """)
    >>> fuzzer = message_fuzzers['Other']
    >>> # The following creates a dependency that ensures Other.foo is always set
    >>> # to 1 greater than Other.addr.house
    >>> fuzzer.add_dependency('foo', 'addr.house', lambda x: x+1)
    >>> for obj in fuzzer.permute():
    ...     print("Generated object: {}".format(obj))
 
Note however, the values your lambda creates must be conformant to the destination
type.

# Caveats

Currently, we use [fuzzdb](https://github.com/fuzzdb-project/fuzzdb) for values. This might not be complete or appropriate for your use. Consider swapping it for your own values.
