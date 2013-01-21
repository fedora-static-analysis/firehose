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
from firehose.report import Report, Sut

FAKE_ANALYZER_VERSION = 'clang-3.0-14.fc17.x86_64'
FAKE_SUT = Sut()

class TestParsePlist(unittest.TestCase):
    def test_example_001(self):
        ret = list(parse_plist(os.path.join(os.path.dirname(__file__),
                                            'example-output/clanganalyzer/report-001.plist'),
                               analyzerversion=FAKE_ANALYZER_VERSION,
                               sut=FAKE_SUT))
        self.assertEqual(len(ret), 2)
        r0 = ret[0]
        self.assertEqual(r0.cwe, None)
        self.assertEqual(r0.metadata.generator.name, 'clang-analyzer')
        self.assertEqual(r0.metadata.generator.version,
                         FAKE_ANALYZER_VERSION)
        self.assertEqual(r0.metadata.generator.internalid, None)
        self.assertEqual(r0.message.text,
                         "Value stored to 'ret' is never read")
        self.assertEqual(r0.notes, None)
        self.assertEqual(r0.location.file.name,
                         'python-ethtool/ethtool.c')
        self.assertEqual(r0.location.function, None)
        self.assertEqual(r0.location.line, 130)
        self.assertEqual(r0.location.column, 2)
        self.assertNotEqual(r0.trace, None)
        self.assertEqual(len(r0.trace.states), 1)
        s0 = r0.trace.states[0]
        self.assertEqual(s0.location.file.name,
                         'python-ethtool/ethtool.c')
        self.assertEqual(s0.location.function.name, '')
        self.assertEqual(s0.location.line, 130)
        self.assertEqual(s0.location.column, 2)
        self.assertEqual(s0.notes.text,
                         "Value stored to 'ret' is never read")
