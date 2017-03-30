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

Motivation
==========

Motivation: http://lists.fedoraproject.org/pipermail/devel/2012-December/175232.html

We want to slurp the results from static code analysis into a database,
which means coercing all of the results into some common interchange format,
codenamed "firehose" (which could also be the name of the database).

The idea is a common XML format that all tools can emit that:

  * describes a warning

  * gives source-code location of the warning: filename, function,
    line number.

  * optionally with a `CWE <http://cwe.mitre.org/about/index.html>`_
    identifier

  * potentially with other IDs and URLs, e.g. the ID "SIG30-C" with URL
    https://www.securecoding.cert.org/confluence/display/seccode/SIG30-C.+Call+only+asynchronous-safe+functions+within+signal+handlers

  * optionally describes code path to get there (potentially
    interprocedural across source files), potentially with "state"
    annotations (e.g. in the case of a reference-counting bug, it's useful
    to be able to annotate the changes to the refcount).

together with a simple Python API for working with the format as a
collection of Python objects (creating, write to XML, read from XML,
modification, etc)

The data can be round-tripped through both XML and JSON.

There is a
`RELAX-NG schema <https://github.com/fedora-static-analysis/firehose/blob/master/firehose.rng>`_
for validating XML files.

References to source files in the format can include a hash of the source
file itself (e.g. SHA-1) so that you can uniquely identify which source file
you were talking about.

This format would be slurped into the DB for the web UI, and can have other
things done to it without needing a server:
e.g.:

  * convert it to the textual form of a gcc compilation error, so that
    Emacs etc can parse it and take you to the source
  * be turned into a simple HTML report locally on your workstation

Projects using Firehose:

  * `mock-with-analysis <https://github.com/fedora-static-analysis/mock-with-analysis>`_
    can rebuild a source RPM, capturing the results of 4 different code
    analysis tools in Firehose format (along with all source files that
    were mentioned in any report).
  * The `"firehose" branch
    <http://git.fedorahosted.org/cgit/gcc-python-plugin.git/log/?h=firehose>`_
    of
    `cpychecker <https://gcc-python-plugin.readthedocs.org/en/latest/cpychecker.html>`_
    can natively emit Firehose XML reports
  * https://github.com/paultag/storz/blob/master/wrappers/storz-lintian
