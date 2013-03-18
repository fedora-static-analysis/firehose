#   Copyright 2013 Red Hat, Inc.
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

from firehose.model import Issue, Failure

from firehose.parsers.cppcheck import parse_file

class TestParseXml(unittest.TestCase):
    def parse_example(self, filename):
        a = parse_file(os.path.join(os.path.dirname(__file__),
                                    'example-output',
                                    'cppcheck-xml-v2',
                                    filename))
        return a

    def test_example_001(self):
        a = self.parse_example('example-001.xml')
        self.assertEqual(a.metadata.generator.name, 'cppcheck')
        self.assertEqual(a.metadata.generator.version, '1.57')
        self.assertEqual(a.metadata.sut, None)
        self.assertEqual(a.metadata.file_, None)
        self.assertEqual(a.metadata.stats, None)
        self.assertEqual(len(a.results), 7)
        r0 = a.results[0]
        self.assertIsInstance(r0, Issue)
        self.assertEqual(r0.cwe, None)
        self.assertEqual(r0.testid, 'uninitvar')
        self.assertEqual(r0.message.text, 'Uninitialized variable: ret')
        self.assertEqual(r0.notes, None)
        self.assertEqual(r0.location.file.givenpath,
                         'python-ethtool/etherinfo_obj.c')
        self.assertEqual(r0.location.file.abspath, None)
        self.assertEqual(r0.location.function, None)
        self.assertEqual(r0.location.line, 185)
        self.assertEqual(r0.trace, None)
        self.assertEqual(r0.severity, 'error')

    def test_example_002(self):
        a = self.parse_example('example-002.xml')
        self.assertEqual(a.metadata.generator.name, 'cppcheck')
        self.assertEqual(a.metadata.generator.version, '1.58')
        self.assertEqual(a.metadata.sut, None)
        self.assertEqual(a.metadata.file_, None)
        self.assertEqual(a.metadata.stats, None)
        self.assertEqual(len(a.results), 1)
        r0 = a.results[0]
        self.assertIsInstance(r0, Failure)
        self.assertEqual(r0.failureid, 'toomanyconfigs')
        self.assertEqual(r0.location, None)
        self.assertEqual(r0.message.text,
                         ('Too many #ifdef configurations - cppcheck only'
                          ' checks 12 configurations. Use --force to check'
                          ' all configurations. For more details, use'
                          ' --enable=information.'))
        self.assertEqual(r0.customfields['verbose'],
                         ('The checking of the file will be interrupted because'
                          ' there are too many #ifdef configurations. Checking of'
                          ' all #ifdef configurations can be forced by --force'
                          ' command line option or from GUI preferences. However'
                          ' that may increase the checking time. For more details,'
                          ' use --enable=information.'))
