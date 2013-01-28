#   Copyright 2013 Red Hat, Inc.
#
#   This is free software: you can redistribute it and/or modify it
#   under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful, but
#   WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see
#   <http://www.gnu.org/licenses/>.

import os
import unittest

from firehose.parsers.clanganalyzer import parse_plist
from firehose.report import Analysis, Issue, Sut

FAKE_ANALYZER_VERSION = 'clang-3.0-14.fc17.x86_64'
FAKE_SUT = Sut()

class TestParsePlist(unittest.TestCase):
    def test_example_001(self):
        a = parse_plist(os.path.join(os.path.dirname(__file__),
                                     'example-output/clanganalyzer/report-001.plist'),
                        analyzerversion=FAKE_ANALYZER_VERSION,
                        sut=FAKE_SUT,
                        file_=None,
                        stats=None)
        self.assertEqual(a.metadata.generator.name, 'clang-analyzer')
        self.assertEqual(a.metadata.generator.version,
                         FAKE_ANALYZER_VERSION)

        self.assertEqual(len(a.results), 2)

        w0 = a.results[0]
        self.assertEqual(w0.cwe, None)
        self.assertEqual(w0.testid, None)
        self.assertEqual(w0.message.text,
                         "Value stored to 'ret' is never read")
        self.assertEqual(w0.notes, None)
        self.assertEqual(w0.location.file.givenpath,
                         'python-ethtool/ethtool.c')
        self.assertEqual(w0.location.file.abspath, None)
        self.assertEqual(w0.location.function, None)
        self.assertEqual(w0.location.line, 130)
        self.assertEqual(w0.location.column, 2)
        self.assertNotEqual(w0.trace, None)
        self.assertEqual(len(w0.trace.states), 1)
        s0 = w0.trace.states[0]
        self.assertEqual(s0.location.file.givenpath,
                         'python-ethtool/ethtool.c')
        self.assertEqual(s0.location.file.abspath, None)
        self.assertEqual(s0.location.function.name, '')
        self.assertEqual(s0.location.line, 130)
        self.assertEqual(s0.location.column, 2)
        self.assertEqual(s0.notes.text,
                         "Value stored to 'ret' is never read")
