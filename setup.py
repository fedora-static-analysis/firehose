#!/usr/bin/env python

from distutils.core import setup

setup(name='firehose',
    version='0.2',
    description='Library for working with output from static code analyzers',
    packages=['firehose',
              'firehose.parsers'],
    license='LGPL2.1 or later',
    author='David Malcolm <dmalcolm@redhat.com>',
    url='https://github.com/fedora-static-analysis/firehose',
    classifiers=(
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries',
    )
)
