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
import os
import StringIO
import subprocess
import tempfile
import unittest

from firehose.report import Analysis, Issue, Metadata, Generator, SourceRpm, \
    Location, File, Function, Point, Message, Notes, Trace, State, Stats, \
    Failure, Range

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
                                       sut=SourceRpm(name='python-ethtool',
                                                     version='0.7',
                                                     release='4.fc19',
                                                     buildarch='x86_64'),
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
                                                                         range_=Range(Point(10, 15),
                                                                                      Point(10, 25))),
                                                       notes=Notes('then it crashes here'))
                                                 ]),
                                    severity='really bad'),
                              ]
                     )
        return a, a.results[0]

    def make_failed_analysis(self):
        a = Analysis(metadata=Metadata(generator=Generator(name='yet-another-checker'),
                                       sut=None,
                                       file_=None,
                                       stats=None),
                     results=[Failure(location=Location(file=File('foo.c', None),
                                                        function=Function('something_complicated'),
                                                        point=Point(10, 15)),
                                      stdout='got here',
                                      stderr='out of memory',
                                      returncode=-9)]) # (killed)
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
        self.assertIsInstance(a.metadata.sut, SourceRpm)
        self.assertEqual(a.metadata.sut.name, 'python-ethtool')
        self.assertEqual(a.metadata.sut.version, '0.7')
        self.assertEqual(a.metadata.sut.release, '4.fc19')
        self.assertEqual(a.metadata.sut.buildarch, 'x86_64')
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
        self.assertEqual(w.severity, 'really bad')

        self.assertIsInstance(w.trace, Trace)
        self.assertEqual(len(w.trace.states), 3)
        s0 = w.trace.states[0]
        self.assertIsInstance(s0, State)
        self.assertEqual(s0.location.file.givenpath, 'foo.c')
        self.assertEqual(s0.location.function.name, 'bar')
        self.assertEqual(s0.location.line, 7)
        self.assertEqual(s0.location.column, 12)
        self.assertEqual(s0.notes.text, 'first we do this')

        # Verify the Range type within the final state in the trace:
        s2 = w.trace.states[2]
        self.assertIsInstance(s2, State)
        self.assertEqual(s2.location.line, 10)
        self.assertEqual(s2.location.column, 15)

    def test_making_failed_analysis(self):
        a, f = self.make_failed_analysis()

        self.assertIsInstance(f, Failure)
        self.assertEqual(f.location.file.givenpath, 'foo.c')
        self.assertEqual(f.location.function.name, 'something_complicated')
        self.assertEqual(f.location.line, 10)
        self.assertEqual(f.location.column, 15)
        self.assertEqual(f.stdout, 'got here')
        self.assertEqual(f.stderr, 'out of memory')
        self.assertEqual(f.returncode, -9)

    def test_from_xml(self):
        num_analyses = 0
        for filename in sorted(glob.glob('examples/example-*.xml')):
            with open(filename) as f:
                r = Analysis.from_xml(f)
                num_analyses += 1
        # Ensure that all of the reports were indeed parsed:
        self.assertEqual(num_analyses, 6)

    def test_example_2(self):
        # Verify that the parser works:
        with open('examples/example-2.xml') as f:
            a = Analysis.from_xml(f)
            self.assertEqual(a.metadata.generator.name, 'cpychecker')
            self.assertEqual(a.metadata.generator.version, '0.11')
            self.assertIsInstance(a.metadata.sut, SourceRpm)
            self.assertEqual(a.metadata.sut.name, 'python-ethtool')
            self.assertEqual(a.metadata.sut.version, '0.7')
            self.assertEqual(a.metadata.sut.release, '4.fc19')
            self.assertEqual(a.metadata.sut.buildarch, 'x86_64')

            self.assertEqual(len(a.results), 1)
            w = a.results[0]
            self.assertIsInstance(w, Issue)
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

    def test_example_3(self):
        # Verify that the parser works:
        with open('examples/example-3.xml') as f:
            a = Analysis.from_xml(f)
            self.assertEqual(a.metadata.generator.name, 'cpychecker')
            self.assertEqual(a.metadata.generator.version, '0.11')
            self.assertIsInstance(a.metadata.sut, SourceRpm)
            self.assertEqual(a.metadata.sut.name, 'python-ethtool')
            self.assertEqual(a.metadata.sut.version, '0.7')
            self.assertEqual(a.metadata.sut.release, '4.fc19')
            self.assertEqual(a.metadata.sut.buildarch, 'x86_64')

            self.assertEqual(len(a.results), 1)
            w = a.results[0]
            self.assertIsInstance(w, Failure)
            self.assertEqual(w.stdout, '')
            self.assertEqual(w.stderr, '')
            self.assertEqual(w.returncode, -11)

    def test_example_4(self):
        with open('examples/example-4.xml') as f:
            a = Analysis.from_xml(f)
            self.assertEqual(a.metadata.generator.name, 'cpychecker')
            self.assertEqual(a.metadata.generator.version, '0.11')
            self.assertIsInstance(a.metadata.sut, SourceRpm)
            self.assertEqual(a.metadata.sut.name, 'python-ethtool')
            self.assertEqual(a.metadata.sut.version, '0.7')
            self.assertEqual(a.metadata.sut.release, '4.fc19')
            self.assertEqual(a.metadata.sut.buildarch, 'x86_64')

            self.assertEqual(len(a.results), 1)
            w = a.results[0]
            self.assertIsInstance(w, Failure)
            self.assertEqual(w.stdout, '')
            self.assert_(w.stderr.startswith('wspy_register.c: In function \'register_all_py_protocols_func\':\n'))
            self.assertEqual(w.returncode, 0)

    def test_example_6(self):
        with open('examples/example-6.xml') as f:
            a = Analysis.from_xml(f)
            self.assertEqual(a.metadata.generator.name, 'cpychecker')

            self.assertEqual(len(a.results), 1)
            w = a.results[0]
            self.assertIsInstance(w, Failure)
            self.assertEqual(w.stdout, None)
            self.assertEqual(w.stderr,
                             'this function is too complicated for the'
                             ' reference-count checker to fully analyze:'
                             ' not all paths were analyzed')
            self.assertEqual(w.returncode, None)

    def test_to_xml(self):
        def validate(xmlstr):
            f = tempfile.NamedTemporaryFile(delete=False)
            f.write(xmlstr)
            f.flush()
            print
            p = subprocess.check_output(['xmllint',
                                         '--relaxng', 'firehose.rng',
                                         '--noout',
                                         f.name])
            # do this by hand: if a test fails, we'll want to inspect the
            # file:
            os.unlink(f.name)

        a, w = self.make_simple_analysis()
        validate(a.to_xml_str())

        a, w = self.make_complex_analysis()
        validate(a.to_xml_str())

    def test_xml_roundtrip(self):
        def roundtrip_through_xml(a):
            xmlstr = a.to_xml_str()

            buf = StringIO.StringIO(xmlstr)
            return Analysis.from_xml(buf)

        a1, w = self.make_simple_analysis()
        a2 = roundtrip_through_xml(a1)

        self.assertEqual(a1.metadata, a2.metadata)
        self.assertEqual(a1.results, a2.results)
        self.assertEqual(a1, a2)

        a3, w = self.make_complex_analysis()
        a4 = roundtrip_through_xml(a3)

        self.assertEqual(a3.metadata, a4.metadata)
        self.assertEqual(a3.results, a4.results)
        self.assertEqual(a3, a4)

        a5, f = self.make_failed_analysis()
        a6 = roundtrip_through_xml(a5)

        self.assertEqual(a5.metadata, a6.metadata)
        self.assertEqual(a5.results, a6.results)
        self.assertEqual(a5, a6)

    def test_repr(self):
        # Verify that the various __repr__ methods are sane:
        a, w = self.make_simple_analysis()
        self.assertIn('Analysis(', repr(a))
        self.assertIn('Issue(', repr(a))

        a, w = self.make_complex_analysis()
        self.assertIn('Analysis(', repr(a))
        self.assertIn('Issue(', repr(a))

        a, f = self.make_failed_analysis()
        self.assertIn('Analysis(', repr(a))
        self.assertIn('Failure(', repr(a))

    def test_hash(self):
        def compare_hashes(creator):
            a1, w1 = creator()
            a2, w2 = creator()
            self.assertEqual(hash(a1), hash(a2))
        compare_hashes(self.make_simple_analysis)
        compare_hashes(self.make_complex_analysis)
        compare_hashes(self.make_failed_analysis)

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
