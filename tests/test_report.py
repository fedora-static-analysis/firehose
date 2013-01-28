#   Copyright 2013 David Malcolm <dmalcolm@redhat.com>
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

import glob
import StringIO
import unittest

from firehose.report import Analysis, Issue, Metadata, Generator, Sut, \
    Location, File, Function, Point, Message, Notes, Trace, State, Stats

class AnalysisTests(unittest.TestCase):
    def make_simple_analysis(self):
        """
        Construct a minimal Analysis instance
        """
        a = Analysis(metadata=Metadata(generator=Generator(name='cpychecker'),
                                       sut=None,
                                       file_=None,
                                       stats=None),
                     results=[Issue(cwe=None,
                                    testid=None,
                                    location=Location(file=File('foo.c', None),
                                                      function=None,
                                                      point=Point(10, 15)),
                                    message=Message(text='something bad involving pointers'),
                                    notes=None,
                                    trace=None)])
        return a, a.results[0]

    def make_complex_analysis(self):
        """
        Construct a Analysis instance that uses all features
        """
        a = Analysis(metadata=Metadata(generator=Generator(name='cpychecker',
                                                           version='0.11'),
                                       sut=Sut(),
                                       file_=File(givenpath='foo.c',
                                                  abspath='/home/david/coding/foo.c'),
                                       stats=Stats(wallclocktime=0.4)),
                     results=[Issue(cwe=681,
                                    testid='refcount-too-high',
                                    location=Location(file=File(givenpath='foo.c',
                                                                abspath='/home/david/coding/foo.c'),
                                                      function=Function('bar'),
                                                      point=Point(10, 15)),
                                    message=Message(text='something bad involving pointers'),
                                    notes=Notes('here is some explanatory text'),
                                    trace=Trace([State(location=Location(file=File('foo.c', None),
                                                                         function=Function('bar'),
                                                                         point=Point(7, 12)),
                                                       notes=Notes('first we do this')),
                                                 State(location=Location(file=File('foo.c', None),
                                                                         function=Function('bar'),
                                                                         point=Point(8, 10)),
                                                       notes=Notes('then we do that')),
                                                 State(location=Location(file=File('foo.c', None),
                                                                         function=Function('bar'),
                                                                         point=Point(10, 15)),
                                                       notes=Notes('then it crashes here'))
                                                 ]))
                              ]
                     )
        return a, a.results[0]

    def test_creating_simple_analysis(self):
        a, w = self.make_simple_analysis()
        self.assertEqual(a.metadata.generator.name, 'cpychecker')
        self.assertEqual(a.metadata.generator.version, None)
        self.assertEqual(a.metadata.sut, None)
        self.assertEqual(a.metadata.file_, None)
        self.assertEqual(a.metadata.stats, None)
        self.assertEqual(w.cwe, None)
        self.assertEqual(w.testid, None)
        self.assertEqual(w.location.file.givenpath, 'foo.c')
        self.assertEqual(w.location.file.abspath, None)
        self.assertEqual(w.location.function, None)
        self.assertEqual(w.location.line, 10)
        self.assertEqual(w.location.column, 15)
        self.assertEqual(w.message.text, 'something bad involving pointers')
        self.assertEqual(w.notes, None)
        self.assertEqual(w.trace, None)

    def test_creating_complex_analysis(self):
        a, w = self.make_complex_analysis()
        self.assertEqual(a.metadata.generator.name, 'cpychecker')
        self.assertEqual(a.metadata.generator.version, '0.11')
        # FIXME: sut
        self.assertEqual(a.metadata.file_.givenpath, 'foo.c')
        self.assertEqual(a.metadata.file_.abspath, '/home/david/coding/foo.c')
        self.assertEqual(a.metadata.stats.wallclocktime, 0.4)
        self.assertEqual(w.cwe, 681)
        self.assertEqual(w.testid, 'refcount-too-high')
        self.assertEqual(w.location.file.givenpath, 'foo.c')
        self.assertEqual(w.location.file.abspath, '/home/david/coding/foo.c')
        self.assertEqual(w.location.function.name, 'bar')
        self.assertEqual(w.location.line, 10)
        self.assertEqual(w.location.column, 15)
        self.assertEqual(w.message.text, 'something bad involving pointers')
        self.assertEqual(w.notes.text, 'here is some explanatory text')

        self.assertIsInstance(w.trace, Trace)
        self.assertEqual(len(w.trace.states), 3)
        s0 = w.trace.states[0]
        self.assertIsInstance(s0, State)
        self.assertEqual(s0.location.file.givenpath, 'foo.c')
        self.assertEqual(s0.location.function.name, 'bar')
        self.assertEqual(s0.location.line, 7)
        self.assertEqual(s0.location.column, 12)
        self.assertEqual(s0.notes.text, 'first we do this')

    def test_from_xml(self):
        num_analyses = 0
        for filename in sorted(glob.glob('examples/example-*.xml')):
            with open(filename) as f:
                r = Analysis.from_xml(f)
                num_analyses += 1
        # Ensure that all of the reports were indeed parsed:
        self.assertEqual(num_analyses, 2)

        # Verify that the parser works:
        with open('examples/example-2.xml') as f:
            a = Analysis.from_xml(f)
            self.assertEqual(a.metadata.generator.name, 'cpychecker')
            self.assertEqual(a.metadata.generator.version, '0.11')
            # FIXME: sut

            self.assertEqual(len(a.results), 1)
            w = a.results[0]
            self.assertEqual(w.cwe, 401)
            self.assertEqual(w.testid, 'refcount-too-high')
            self.assertEqual(w.location.file.givenpath, 'examples/python-src-example.c')
            self.assertEqual(w.location.file.abspath, None)
            self.assertEqual(w.location.file.hash_.alg, 'sha1')
            self.assertEqual(w.location.file.hash_.hexdigest,
                             '6ba29daa94d64b48071e299a79f2a00dcd99eeb1')
            self.assertEqual(w.location.function.name, 'make_a_list_of_random_ints_badly')
            self.assertEqual(w.location.line, 21)
            self.assertEqual(w.location.column, 4)
            self.assertEqual(w.message.text, "ob_refcnt of '*item' is 1 too high")
            self.assertMultiLineEqual(w.notes.text,
                ("was expecting final item->ob_refcnt to be N + 1 (for some unknown N)\n"
                 "due to object being referenced by: PyListObject.ob_item[0]\n"
                 "but final item->ob_refcnt is N + 2"))

            self.assertIsInstance(w.trace, Trace)
            self.assertEqual(len(w.trace.states), 3)
            s0 = w.trace.states[0]
            self.assertIsInstance(s0, State)
            self.assertEqual(s0.location.file.givenpath, 'examples/python-src-example.c')
            self.assertEqual(s0.location.function.name, 'make_a_list_of_random_ints_badly')
            self.assertEqual(s0.location.line, 17)
            self.assertEqual(s0.location.column, 14)
            self.assertEqual(s0.notes.text,
                'PyLongObject allocated at:         item = PyLong_FromLong(random());')

    def test_to_xml(self):
        a, w = self.make_simple_analysis()
        a.to_xml()

        a, w = self.make_complex_analysis()
        a.to_xml()

        # FIXME: do they roundtrip?

        # TODO: Does it validate?
        # r.write_xml('foo.xml')
        # p = Popen(['xmllint', '--relaxng', 'firehose.rng', 'foo.xml'])
        # p.communicate()

    def test_repr(self):
        # Verify that the various __repr__ methods are sane:
        a, w = self.make_simple_analysis()
        self.assertIn('Analysis(', repr(a))

        a, w = self.make_complex_analysis()
        self.assertIn('Analysis(', repr(a))

    def test_cwe(self):
        # Verify that the CWE methods are sane:
        a, w = self.make_complex_analysis()
        self.assertIsInstance(w.cwe, int)
        self.assertEqual(w.get_cwe_str(), 'CWE-681')
        self.assertEqual(w.get_cwe_url(),
                         'http://cwe.mitre.org/data/definitions/681.html')

        # Verify that they are sane for a warning without a CWE:
        a, w = self.make_simple_analysis()
        self.assertEqual(w.cwe, None)
        self.assertEqual(w.get_cwe_str(), None)
        self.assertEqual(w.get_cwe_url(), None)

    def test_fixup_paths(self):
        # Verify that Report.fixup_files() can make paths absolute:
        a, w = self.make_simple_analysis()

        self.assertEqual(w.location.file.abspath, None)
        a.fixup_files(relativedir='/home/david/coding/test')
        self.assertEqual(w.location.file.abspath, '/home/david/coding/test/foo.c')

    def test_fixup_hashes(self):
        # Verify that Report.fixup_files() can add hashes to files:
        a, w = self.make_simple_analysis()
        w.location.file.givenpath = 'examples/python-src-example.c'
        w.location.file.abspath = None
        self.assertEqual(w.location.file.hash_, None)

        a.fixup_files(hashalg='sha1')
        self.assertEqual(w.location.file.hash_.alg, 'sha1')
        self.assertEqual(w.location.file.hash_.hexdigest,
                         '6ba29daa94d64b48071e299a79f2a00dcd99eeb1')

    def test_gcc_output(self):
        a, w = self.make_simple_analysis()

        output = StringIO.StringIO()
        w.write_as_gcc_output(output)
        self.assertEqual(output.getvalue(),
                         'foo.c:10:15: warning: something bad involving pointers\n')

        a, w = self.make_complex_analysis()
        output = StringIO.StringIO()
        w.write_as_gcc_output(output)
        self.assertMultiLineEqual(output.getvalue(),
            ("foo.c: In function 'bar':\n"
             "foo.c:10:15: warning: something bad involving pointers [CWE-681]\n"
             "here is some explanatory text\n"
             "foo.c:7:12: note: first we do this\n"
             "foo.c:8:10: note: then we do that\n"
             "foo.c:10:15: note: then it crashes here\n"))
