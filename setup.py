from setuptools import setup

setup(name='protofuzz',
      version='0.1',
      description='Google protobuf message generator',
      url='http://github.com/trailofbits/protofuzz',
      author='Yan Ivnitskiy',
      author_email='yan@trailofbits.com',
      license='MIT',
      packages=['protofuzz'],
      install_requires=['py3-protobuffers'],
      include_package_data=True,
      test_suite='nose.collector',
      tests_require=['nose'],
      zip_safe=False)
