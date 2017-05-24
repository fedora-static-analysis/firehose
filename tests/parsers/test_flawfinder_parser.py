#!/usr/bin/env python
#
#   Copyright 2017 David Carlos  <ddavidcarlos1392@gmail.com>
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

from firehose.parsers.flawfinder import parse_file
from firehose.model import Analysis, Issue, Sut, Trace

class TestParseXml(unittest.TestCase):
    def parse_example(self, filename):
        try:
            path = os.path.join(os.path.dirname(__file__),
                    'example-output',
                    'flawfinder',
                    filename)
            with open(path) as infile:
                return parse_file(infile)
        except IOError:
            print("Example input not found")

    def test_flawfinder_report(self):
        a = self.parse_example('flawfinder-report-1')
        self.assertEqual(a.metadata.generator.name, 'flawfinder')
        self.assertEqual(a.metadata.generator.version, '1.31')
        self.assertEqual(a.metadata.sut, None)
        self.assertEqual(a.metadata.file_, None)
        self.assertEqual(a.metadata.stats, None)
        self.assertEqual(a.metadata.stats, None)

        self.assertEqual(len(a.results), 1804)

        w0 = a.results[0]
        self.assertEqual(w0.cwe, 78)
        expected_message = 'This causes a new program to execute ' \
                           'and is difficult to use safely (CWE-78). ' \
                           'try using a library call that implements ' \
                           'the same functionality if available.'
        self.assertEqual(w0.message.text, expected_message)
        self.assertEqual(w0.testid, 'shell')
        self.assertEqual(w0.location.file.givenpath , "./docs/examples/asiohiper.cpp")
        self.assertEqual(w0.location.point.line, 78)
        self.assertEqual(w0.location.point.column, 0)

        w3 = a.results[4]
        self.assertEqual(w3.location.file.givenpath , "./docs/examples/cookie_interface.c")
        self.assertEqual(w3.testid, 'format')
        some_w = a.results[1801]
        self.assertEqual(some_w.cwe, 126)
        self.assertEqual(some_w.testid, 'buffer')
        other_w = a.results[1802]
        self.assertEqual(other_w.cwe, None)
        self.assertEqual(other_w.location.file.givenpath,
                         "./tests/unit/unit1604.c")
        self.assertEqual(other_w.location.point.line, 49)
        self.assertEqual(other_w.location.point.column, 0)
