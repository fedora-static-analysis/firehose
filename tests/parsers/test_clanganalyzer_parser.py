#   Copyright 2013, 2017 Red Hat, Inc.
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

from firehose.parsers.clanganalyzer import parse_plist
from firehose.model import Analysis, Issue, Sut, Trace

class TestParsePlist(unittest.TestCase):
    def parse_example(self, filename):
        a = parse_plist(os.path.join(os.path.dirname(__file__),
                                     'example-output/clanganalyzer',
                                     filename),
                        file_=None,
                        stats=None)
        return a

    def test_example_001(self):
        a = self.parse_example('report-001.plist')
        self.assertEqual(a.metadata.generator.name, 'clang-analyzer')
        self.assertEqual(a.metadata.generator.version, None)

        self.assertEqual(len(a.results), 2)

        w0 = a.results[0]
        self.assertEqual(w0.cwe, None)
        self.assertEqual(w0.testid, 'Dead assignment')
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

    def test_example_002(self):
        a = self.parse_example('report-002.plist')
        self.assertEqual(a.metadata.generator.name, 'clang-analyzer')
        self.assertEqual(a.metadata.generator.version, None)

        self.assertEqual(len(a.results), 4)

        w0 = a.results[0]
        self.assertEqual(w0.testid, 'Dead assignment')
        self.assertEqual(w0.message.text,
                         "Value stored to 'error' is never read")
        self.assertEqual(w0.location.file.givenpath, 'search.c')
        self.assertEqual(w0.location.line, 454)
        self.assertEqual(w0.location.column, 3)

        w1 = a.results[1]
        self.assertEqual(w1.testid, 'Dead increment')
        self.assertEqual(w1.message.text,
                         "Value stored to 'pol_opt' is never read")
        self.assertEqual(w1.location.file.givenpath, 'search.c')
        self.assertEqual(w1.location.line, 824)
        self.assertEqual(w1.location.column, 2)

        w2 = a.results[2]
        self.assertEqual(w2.testid, 'Dereference of null pointer')
        self.assertEqual(w2.message.text,
                         "Access to field 'ob_refcnt' results in a dereference of a null pointer (loaded from variable 'dict')")
        self.assertEqual(w2.location.file.givenpath, 'search.c')
        self.assertEqual(w2.location.line, 215)
        self.assertEqual(w2.location.column, 2)
        trace2 = w2.trace
        self.assertIsInstance(trace2, Trace)

        self.assertEqual(len(trace2.states), 13)

        # s0 and s1 come from the first control edge in the input file:
        #         'path': [{'edges': [{'end': [{'col': 9,
        #                                       'file': 0,
        #                                       'line': 161},
        #                                      {'col': 9,
        #                                       'file': 0,
        #                                       'line': 161}],
        #                              'start': [{'col': 2,
        #                                         'file': 0,
        #                                         'line': 161},
        #                                        {'col': 2,
        #                                         'file': 0,
        #                                         'line': 161}]}],
        #                   'kind': 'control'},

        s0 = trace2.states[0]
        self.assertEqual(s0.location.point.line, 161)
        self.assertEqual(s0.location.point.column, 2)
        self.assertEqual(s0.location.range_, None)


        s1 = trace2.states[1]
        self.assertEqual(s1.location.point.line, 161)
        self.assertEqual(s1.location.point.column, 9)
        self.assertEqual(s1.location.range_, None)

        # s2 comes from the endpoint of the second control edge in the
        # input file (the startpoint == s1).
        #                  {'edges': [{'end': [{'col': 18,
        #                                       'file': 0,
        #                                       'line': 165},
        #                                      {'col': 21,
        #                                       'file': 0,
        #                                       'line': 165}],
        #                              'start': [{'col': 9,
        #                                         'file': 0,
        #                                         'line': 161},
        #                                        {'col': 9,
        #                                         'file': 0,
        #                                         'line': 161}]}],
        #                   'kind': 'control'},
        #
        # It is a range rather than a point:
        s2 = trace2.states[2]
        self.assertEqual(s2.location.point, None)
        self.assertEqual(s2.location.range_.start.line, 165)
        self.assertEqual(s2.location.range_.start.column, 18)
        self.assertEqual(s2.location.range_.end.line, 165)
        self.assertEqual(s2.location.range_.end.column, 21)

        # s3 comes from the next entry in the input file, which is the first
        # "event" in the trace:
        #                  {'extended_message': "Variable 'dict' initialized to a null pointer value",
        #                   'kind': 'event',
        #                   'location': {'col': 18,
        #                                'file': 0,
        #                                'line': 165},
        #                   'message': "Variable 'dict' initialized to a null pointer value",
        #                   'ranges': [[{'col': 18,
        #                                'file': 0,
        #                                'line': 165},
        #                               {'col': 21,
        #                                'file': 0,
        #                                'line': 165}]]},
        s3 = trace2.states[3]
        # The importer uses the 'location' point for the event, and hence
        # is treated as a different location.  However, as an event, it is
        # always given its own state in the imported data:
        self.assertEqual(s3.location.point.line, 165)
        self.assertEqual(s3.location.point.column, 18)
        self.assertEqual(s3.notes.text,
                         "Variable 'dict' initialized to a null pointer value")
        self.assertEqual(s3.location.range_, None)

        # The next entry in the input file is another kind == 'control':
        #                  {'edges': [{'end': [{'col': 2,
        #                                       'file': 0,
        #                                       'line': 171},
        #                                      {'col': 2,
        #                                       'file': 0,
        #                                       'line': 171}],
        #                              'start': [{'col': 18,
        #                                         'file': 0,
        #                                         'line': 165},
        #                                        {'col': 21,
        #                                         'file': 0,
        #                                         'line': 165}]}],
        #                   'kind': 'control'},
        # The "start" is range-based, whereas the previous event was
        # handled as a point, so the importer will treat it as two
        # different locations (s3 and s4):
        s4 = trace2.states[4]
        self.assertEqual(s4.location.point, None)
        self.assertEqual(s4.location.range_.start.line, 165)
        self.assertEqual(s4.location.range_.start.column, 18)
        self.assertEqual(s4.location.range_.end.line, 165)
        self.assertEqual(s4.location.range_.end.column, 21)

        s5 = trace2.states[5]
        self.assertEqual(s5.location.point.line, 171)
        self.assertEqual(s5.location.point.column, 2)
        self.assertEqual(s5.location.range_, None)

        # etc

    def test_example_003(self):
        a = self.parse_example('report-003.plist')
        self.assertEqual(a.metadata.generator.name, 'clang-analyzer')

        # This example has a version
        self.assertEqual(a.metadata.generator.version,
                         'clang version 3.4.2 (tags/RELEASE_34/dot2-final)')

        self.assertEqual(len(a.results), 1)

        w0 = a.results[0]
        self.assertEqual(w0.testid, 'Garbage return value')
        self.assertEqual(w0.message.text,
                         "Undefined or garbage value returned to caller")
        self.assertEqual(w0.location.file.givenpath,
                         '../../src/test-sources/out-of-bounds.c')
        self.assertEqual(w0.location.line, 5)
        self.assertEqual(w0.location.column, 3)

        # Verify that we capture various clang-specific per-issue metadata
        self.assertEqual(w0.customfields['category'], 'Logic error')
        self.assertEqual(w0.customfields['issue_context'], 'out_of_bounds')
        self.assertEqual(w0.customfields['issue_context_kind'], 'function')

if __name__ == '__main__':
    unittest.main()
