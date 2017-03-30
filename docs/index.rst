..  Copyright 2017 David Malcolm <dmalcolm@redhat.com>
    Copyright 2017 Red Hat, Inc.

    This library is free software; you can redistribute it and/or
    modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 2.1 of the License, or (at your option) any later version.

    This library is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with this library; if not, write to the Free Software
    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301
    USA

Welcome to firehose's documentation!
====================================

"firehose" is a Python package intended for managing the results from
code analysis tools (e.g. compiler warnings, static analysis, linters,
etc).

It currently provides parsers for the output of gcc, clang-analyzer, cppcheck,
and findbugs.  These parsers convert the results into a common data model of
Python objects, with methods for lossless roundtrips through a provided
XML format.  There is also a JSON equivalent.

It is available on pypi here:
  https://pypi.python.org/pypi/firehose

and via git from:
  https://github.com/fedora-static-analysis/firehose

The mailing list is:
  https://admin.fedoraproject.org/mailman/listinfo/firehose-devel

Firehose is Free Software, licensed under the LGPLv2.1 or (at your
option) any later version.

It requires Python 2.7 or 3.2 onwards, and has been successfully tested
with PyPy.

It is currently of alpha quality.

The API and serialization formats are not yet set in stone (and we're
keen on hearing feedback before we lock things down more).


Contents:

.. toctree::
   :maxdepth: 2

   motivation.rst
   examples.rst
   data-model.rst
   parsers.rst
   rng-schema.rst


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
