#   Copyright 2017 David Malcolm <dmalcolm@redhat.com>
#   Copyright 2017 Red Hat, Inc.
#
#   This library is free software; you can redistribute it and/or
#   modify it under the terms of the GNU Lesser General Public
#   License as published by the Free Software Foundation; either
#   version 2.1 of the License, or (at your option) any later version.
#
#   This library is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   Lesser General Public License for more details.
#
#   You should have received a copy of the GNU Lesser General Public
#   License along with this library; if not, write to the Free Software
#   Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301
#   USA

import os
import unittest

from firehose.model import Issue

from firehose.parsers.splint import parse_splint_csv, parse_splint_stderr

class TestParser(unittest.TestCase):
    def locate_filename(self, filename):
        return os.path.join(os.path.dirname(__file__),
                            'example-output',
                            'splint',
                            filename)

    def parse_example_csv(self, filename):
        return parse_splint_csv(self.locate_filename(filename))

    def test_unconditional_file_leak(self):
        a = self.parse_example_csv('unconditional-file-leak.csv')
        self.assertEqual(a.metadata.generator.name, 'splint')
        self.assertEqual(a.metadata.generator.version, None) # FIXME
        self.assertEqual(a.metadata.sut, None)
        self.assertEqual(a.metadata.file_, None)
        self.assertEqual(a.metadata.stats, None)
        self.assertEqual(len(a.results), 8)
        r0 = a.results[0]
        self.assertIsInstance(r0, Issue)
        self.assertEqual(r0.cwe, None)
        self.assertEqual(r0.testid, 'internalglobs')
        self.assertEqual(r0.message.text,
                         'Called procedure fopen may access file system'
                         ' state, but globals list does not include globals'
                         ' fileSystem')
        self.assertEqual(r0.notes.text,
                         'A called function uses internal state, but the'
                         ' globals list for the function being checked does'
                         ' not include internalState')
        self.assertEqual(r0.location.file.givenpath,
                         'examples/unconditional-file-leak.c')
        self.assertEqual(r0.location.file.abspath, None)
        self.assertEqual(r0.location.function, None)
        self.assertEqual(r0.trace, None)
        self.assertEqual(r0.severity, '1')

        # Verify that rows with unescaped quotes are correctly worked around
        # In this example, this affects warnings #4 and #6 (these are 1-based,
        # so index 3 and 5 in the list).
        r3 = a.results[3]
        self.assertEqual(r3.location.line, 9)
        self.assertEqual(r3.location.column, 5)
        # Quote-handling is not quite perfect, we've lost the open quote of
        # the format string, and there an erroneous trailing quote in this
        # message.
        self.assertEqual(r3.message.text,
                         'Undocumented modification of file system state'
                         ' possible from call to fprintf:'
                         ' fprintf(f, %i: %i", i, i * i)"')

        r5 = a.results[5]
        # Similar issues here:
        self.assertEqual(r5.message.text,
                         'Body of for statement is not a block:'
                         ' fprintf(f, %i: %i", i, i * i);"')

    def parse_example_stderr(self, filename):
        with open(self.locate_filename(filename)) as f:
            stderr = f.read()
        return parse_splint_stderr(stderr)

    def test_parse_stderr(self):
        v = self.parse_example_stderr('unconditional-file-leak.stderr')
        self.assertEqual(v, '3.1.2')
