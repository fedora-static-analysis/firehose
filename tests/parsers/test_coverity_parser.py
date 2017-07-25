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

#   Coverity is a trademark of Synopsys, Inc. in the U.S. and/or other
#   countries.

import os
import unittest

from firehose.parsers.coverity import parse_json_v2
from firehose.model import Analysis, Issue, Sut, Trace

class TestParseJsonV2(unittest.TestCase):
    def parse_example(self, filename):
        a = parse_json_v2(os.path.join(os.path.dirname(__file__),
                                     'example-output/coverity',
                                     filename))
        return a

    def test_example(self):
        a = self.parse_example('json-v2-example-1.json')
        self.assertEqual(a.metadata.generator.name, 'coverity')
        self.assertEqual(a.metadata.generator.version, None)

        self.assertEqual(len(a.results), 6)

        w0 = a.results[0]
        self.assertEqual(w0.cwe, None)
        self.assertEqual(w0.testid, 'RESOURCE_LEAK')
        self.assertEqual(w0.message.text,
                         "Variable \"ptr_1\" going out of scope leaks the"
                         " storage it points to.")
        self.assertEqual(w0.notes, None)

        exp_path = '/home/david/coding-3/gcc-git-static-analysis/src/' \
                   'checkers/test-sources/conditional-leak.c'
        self.assertEqual(w0.location.file.givenpath, exp_path)
        self.assertEqual(w0.location.file.abspath, None)
        self.assertEqual(w0.location.function.name, 'test')
        self.assertEqual(w0.location.line, 13)
        self.assertEqual(w0.location.column, 0)
        self.assertNotEqual(w0.trace, None)
        self.assertEqual(len(w0.trace.states), 5)
        s0 = w0.trace.states[0]
        self.assertEqual(s0.location.file.givenpath, exp_path)
        self.assertEqual(s0.location.file.abspath, None)
        self.assertEqual(s0.location.function, None)
        self.assertEqual(s0.location.line, 8)
        self.assertEqual(s0.location.column, 0)
        self.assertEqual(s0.notes.text,
                         "Storage is returned from allocation"
                         " function \"malloc\".")

        self.assertEqual(w0.customfields['mergeKey'],
                         'b4ab4edbecd149e52d24b88c34236b11')
        self.assertEqual(w0.customfields['subcategory'], 'none')
        self.assertEqual(w0.customfields['domain'], 'STATIC_C')

if __name__ == '__main__':
    unittest.main()
