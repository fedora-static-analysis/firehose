#!/usr/bin/env python

from distutils.core import setup

setup(name='firehose',
    version='0.0.1',
    description='library for parsing gcc build output for warnings',
    packages=('firehose',),
    license='GPL3',
    author='David Malcolm',
    url='https://github.com/fedora-static-analysis/firehose',
    classifiers=(
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Topic :: Software Development :: Libraries',
    )
)
