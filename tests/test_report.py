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

from firehose.report import Report, Metadata, Generator, Sut, Location, \
    File, Function, Point, Message, Notes, Trace, State

class ReportTests(unittest.TestCase):
    def make_simple_report(self):
        """
        Construct a minimal Report instance
        """
        r = Report(cwe=None,
                   metadata=Metadata(generator=Generator(name='cpychecker'),
                                     sut=None),
                   location=Location(file=File('foo.c', None),
                                     function=None,
                                     point=Point(10, 15)),
                   message=Message(text='something bad involving pointers'),
                   notes=None,
                   trace=None)
        return r

    def make_complex_report(self):
        """
        Construct a Report instance that uses all features
        """
        r = Report(cwe=681,
                   metadata=Metadata(generator=Generator(name='cpychecker',
                                                         version='0.11',
                                                         internalid='refcount-too-high'),
                                     sut=Sut()),
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
                                ])
                   )
        return r

    def test_creating_simple_report(self):
        r = self.make_simple_report()
        self.assertEqual(r.cwe, None)
        self.assertEqual(r.metadata.generator.name, 'cpychecker')
        self.assertEqual(r.metadata.generator.version, None)
        self.assertEqual(r.metadata.generator.internalid, None)
        self.assertEqual(r.metadata.sut, None)
        self.assertEqual(r.location.file.givenpath, 'foo.c')
        self.assertEqual(r.location.file.abspath, None)
        self.assertEqual(r.location.function, None)
        self.assertEqual(r.location.line, 10)
        self.assertEqual(r.location.column, 15)
        self.assertEqual(r.message.text, 'something bad involving pointers')
        self.assertEqual(r.notes, None)
        self.assertEqual(r.trace, None)

    def test_creating_complex_report(self):
        r = self.make_complex_report()
        self.assertEqual(r.cwe, 681)
        self.assertEqual(r.metadata.generator.name, 'cpychecker')
        self.assertEqual(r.metadata.generator.version, '0.11')
        self.assertEqual(r.metadata.generator.internalid, 'refcount-too-high')
        # FIXME: sut
        self.assertEqual(r.location.file.givenpath, 'foo.c')
        self.assertEqual(r.location.file.abspath, '/home/david/coding/foo.c')
        self.assertEqual(r.location.function.name, 'bar')
        self.assertEqual(r.location.line, 10)
        self.assertEqual(r.location.column, 15)
        self.assertEqual(r.message.text, 'something bad involving pointers')
        self.assertEqual(r.notes.text, 'here is some explanatory text')

        self.assertIsInstance(r.trace, Trace)
        self.assertEqual(len(r.trace.states), 3)
        s0 = r.trace.states[0]
        self.assertIsInstance(s0, State)
        self.assertEqual(s0.location.file.givenpath, 'foo.c')
        self.assertEqual(s0.location.function.name, 'bar')
        self.assertEqual(s0.location.line, 7)
        self.assertEqual(s0.location.column, 12)
        self.assertEqual(s0.notes.text, 'first we do this')

    def test_from_xml(self):
        num_reports = 0
        for filename in sorted(glob.glob('examples/example-*.xml')):
            with open(filename) as f:
                r = Report.from_xml(f)
                num_reports += 1
        # Ensure that all of the reports were indeed parsed:
        self.assertEqual(num_reports, 2)

        # Verify that the parser works:
        with open('examples/example-2.xml') as f:
            r = Report.from_xml(f)
            self.assertEqual(r.cwe, 401)
            self.assertEqual(r.metadata.generator.name, 'cpychecker')
            self.assertEqual(r.metadata.generator.version, '0.11')
            self.assertEqual(r.metadata.generator.internalid, 'refcount-too-high')
            # FIXME: sut
            self.assertEqual(r.location.file.givenpath, 'examples/python-src-example.c')
            self.assertEqual(r.location.file.abspath, None)
            self.assertEqual(r.location.file.hash_.alg, 'sha1')
            self.assertEqual(r.location.file.hash_.hexdigest,
                             '6ba29daa94d64b48071e299a79f2a00dcd99eeb1')
            self.assertEqual(r.location.function.name, 'make_a_list_of_random_ints_badly')
            self.assertEqual(r.location.line, 21)
            self.assertEqual(r.location.column, 4)
            self.assertEqual(r.message.text, "ob_refcnt of '*item' is 1 too high")
            self.assertMultiLineEqual(r.notes.text,
                ("was expecting final item->ob_refcnt to be N + 1 (for some unknown N)\n"
                 "due to object being referenced by: PyListObject.ob_item[0]\n"
                 "but final item->ob_refcnt is N + 2"))

            self.assertIsInstance(r.trace, Trace)
            self.assertEqual(len(r.trace.states), 3)
            s0 = r.trace.states[0]
            self.assertIsInstance(s0, State)
            self.assertEqual(s0.location.file.givenpath, 'examples/python-src-example.c')
            self.assertEqual(s0.location.function.name, 'make_a_list_of_random_ints_badly')
            self.assertEqual(s0.location.line, 17)
            self.assertEqual(s0.location.column, 14)
            self.assertEqual(s0.notes.text,
                'PyLongObject allocated at:         item = PyLong_FromLong(random());')

    def test_to_xml(self):
        r = self.make_simple_report()
        r.to_xml()

        r = self.make_complex_report()
        r.to_xml()

        # FIXME: do they roundtrip?

        # TODO: Does it validate?
        # r.write_xml('foo.xml')
        # p = Popen(['xmllint', '--relaxng', 'firehose.rng', 'foo.xml'])
        # p.communicate()

    def test_repr(self):
        # Verify that the various __repr__ methods are sane:
        r = self.make_simple_report()
        self.assertIn('Report(', repr(r))

        r = self.make_complex_report()
        self.assertIn('Report(', repr(r))

    def test_cwe(self):
        # Verify that the CWE methods are sane:
        r = self.make_complex_report()
        self.assertIsInstance(r.cwe, int)
        self.assertEqual(r.get_cwe_str(), 'CWE-681')
        self.assertEqual(r.get_cwe_url(),
                         'http://cwe.mitre.org/data/definitions/681.html')

        # Verify that they are sane for a report without a CWE:
        r = self.make_simple_report()
        self.assertEqual(r.cwe, None)
        self.assertEqual(r.get_cwe_str(), None)
        self.assertEqual(r.get_cwe_url(), None)

    def test_fixup_paths(self):
        # Verify that Report.fixup_files() can make paths absolute:
        r = self.make_simple_report()

        self.assertEqual(r.location.file.abspath, None)
        r.fixup_files(relativedir='/home/david/coding/test')
        self.assertEqual(r.location.file.abspath, '/home/david/coding/test/foo.c')

    def test_fixup_hashes(self):
        # Verify that Report.fixup_files() can add hashes to files:
        r = self.make_simple_report()
        r.location.file.givenpath = 'examples/python-src-example.c'
        r.location.file.abspath = None
        self.assertEqual(r.location.file.hash_, None)

        r.fixup_files(hashalg='sha1')
        self.assertEqual(r.location.file.hash_.alg, 'sha1')
        self.assertEqual(r.location.file.hash_.hexdigest,
                         '6ba29daa94d64b48071e299a79f2a00dcd99eeb1')

    def test_gcc_output(self):
        r = self.make_simple_report()

        output = StringIO.StringIO()
        r.write_as_gcc_output(output)
        self.assertEqual(output.getvalue(),
                         'foo.c:10:15: warning: something bad involving pointers\n')

        r = self.make_complex_report()
        output = StringIO.StringIO()
        r.write_as_gcc_output(output)
        self.assertMultiLineEqual(output.getvalue(),
            ("foo.c: In function 'bar':\n"
             "foo.c:10:15: warning: something bad involving pointers [CWE-681]\n"
             "here is some explanatory text\n"
             "foo.c:7:12: note: first we do this\n"
             "foo.c:8:10: note: then we do that\n"
             "foo.c:10:15: note: then it crashes here\n"))
