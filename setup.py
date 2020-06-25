import os
from setuptools import setup

setup(name='protofuzz',
      version='0.2',
      description='Google protobuf message generator',
      long_description=""""ProtoFuzz is a generic fuzzer for Google’s Protocol Buffers format.
Instead of defining a new fuzzer generator for custom binary formats, protofuzz automatically creates a fuzzer based on
the same format definition that programs use. ProtoFuzz is implemented as a stand-alone Python3 program.""",
      url='https://github.com/trailofbits/protofuzz',
      author='Trail of Bits',
      license='MIT',
      packages=['protofuzz'],
      install_requires=['protobuf>=2.6.0'],
      test_suite='nose.collector',
      tests_require=['nose'],
      zip_safe=False,
      package_data={'protofuzz': [os.path.join('fuzzdb', '**', '*')]},
      include_package_data=True,
)
