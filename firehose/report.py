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

# Python module for working with Firehose XML files, also, potentially,
# a command-line tool

import glob
import os
import hashlib
import StringIO
from subprocess import Popen, PIPE
import sys
import xml.etree.ElementTree as ET

class Analysis(object):
    __slots__ = ('metadata',
                 'results')

    def __init__(self, metadata, results):
        assert isinstance(metadata, Metadata)
        assert isinstance(results, list)
        for result in results:
            assert isinstance(result, Issue)

        self.metadata = metadata
        self.results = results

    @classmethod
    def from_xml(cls, fileobj):
        tree = ET.parse(fileobj)
        root = tree.getroot()

        metadata = Metadata.from_xml(root.find('metadata'))
        results_node = root.find('results')
        results = []
        for result_node in results_node.findall('issue'):
            results.append(Issue.from_xml(result_node))
        return Analysis(metadata, results)

    def to_xml(self):
        tree = ET.ElementTree()
        node = ET.Element('analysis')
        tree._setroot(node)
        node.append(self.metadata.to_xml())
        results_node = ET.Element('results')
        node.append(results_node)
        for result in self.results:
            results_node.append(result.to_xml())
        return tree

    def to_xml_str(self):
        xml = self.to_xml()
        output = StringIO.StringIO()
        xml.write(output)
        return output.getvalue()

    def __repr__(self):
        return ('Analysis(metadata=%r, results=%r)'
                % (self.metadata, self.results))

    def accept(self, visitor):
        visitor.visit_analysis(self)
        self.metadata.accept(visitor)
        for result in self.results:
            result.accept(visitor)

    def fixup_files(self, relativedir=None, hashalg=None):
        """
        Record the absolute path of each file, and record the digest of the
        file content
        """
        class FixupFiles(Visitor):
            def __init__(self, relativedir, hashalg):
                self.relativedir = relativedir
                self.hashalg = hashalg

            def visit_file(self, file_):
                if self.relativedir is not None:
                    file_.abspath = os.path.normpath(os.path.join(self.relativedir,
                                                                  file_.givenpath))

                if hashalg is not None:
                    bestpath = file_.abspath \
                        if file_.abspath else file_.givenpath

                    with open(bestpath) as f:
                        h = hashlib.new(hashalg)
                        h.update(f.read())
                        file_.hash_ = Hash(alg=hashalg, hexdigest=h.hexdigest())

        visitor = FixupFiles(relativedir, hashalg)
        self.accept(visitor)

class Issue(object):
    __slots__ = ('cwe',
                 'testid',
                 'location',
                 'message',
                 'notes',
                 'trace')
    def __init__(self,
                 cwe,
                 testid,
                 location,
                 message,
                 notes,
                 trace):
        if cwe is not None:
            assert isinstance(cwe, int)
        if testid is not None:
            assert isinstance(testid, str)
        assert isinstance(location, Location)
        assert isinstance(message, Message)
        if notes:
            assert isinstance(notes, Notes)
        if trace:
            assert isinstance(trace, Trace)
        self.cwe = cwe
        self.testid = testid
        self.location = location
        self.message = message
        self.notes = notes
        self.trace = trace

    @classmethod
    def from_xml(cls, node):
        cwe = node.get('cwe')
        if cwe is not None:
            cwe = int(cwe)
        testid = node.get('test-id')
        location = Location.from_xml(node.find('location'))
        message = Message.from_xml(node.find('message'))
        notes_node = node.find('notes')
        if notes_node is not None:
            notes = Notes.from_xml(notes_node)
        else:
            notes = None
        trace_node = node.find('trace')
        if trace_node is not None:
            trace = Trace.from_xml(trace_node)
        else:
            trace = None
        return Issue(cwe, testid, location, message, notes, trace)

    def to_xml(self):
        node = ET.Element('issue')
        if self.cwe is not None:
            node.set('cwe', str(self.cwe))
        node.append(self.location.to_xml())
        node.append(self.message.to_xml())
        if self.notes:
            node.append(self.notes.to_xml())
        if self.trace:
            node.append(self.trace.to_xml())
        return node

    def write_as_gcc_output(self, out):
        """
        Write the report in the style of a GCC warning to the given
        file-like object
        """
        def writeln(msg):
            out.write('%s\n' % msg)
        def diagnostic(filename, line, column, kind, msg):
            out.write('%s:%i:%i: %s: %s\n'
                      % (filename, line, column,
                         kind, msg))
        if self.location.function is not None:
            writeln("%s: In function '%s':"
                    % (self.location.file.givenpath,
                       self.location.function.name))
        if self.cwe:
            cwetext = ' [%s]' % self.get_cwe_str()
        else:
            cwetext = ''
        diagnostic(filename=self.location.file.givenpath,
                   line=self.location.line,
                   column=self.location.column,
                   kind='warning',
                   msg='%s%s' % (self.message.text, cwetext))
        if self.notes:
            writeln(self.notes.text.rstrip())
        if self.trace:
            for state in self.trace.states:
                notes = state.notes
                diagnostic(filename=state.location.file.givenpath,
                           line=state.location.line,
                           column=state.location.column,
                           kind='note',
                           msg=notes.text if notes else '')

    def __repr__(self):
        return ('Report(cwe=%r, location=%r, message=%r, notes=%r, trace=%r)'
                % (self.cwe, self.location, self.message, self.notes, self.trace))

    def accept(self, visitor):
        visitor.visit_warning(self)
        self.location.accept(visitor)
        self.message.accept(visitor)
        if self.notes:
            self.notes.accept(visitor)
        if self.trace:
            self.trace.accept(visitor)

    def get_cwe_str(self):
        if self.cwe is not None:
            return 'CWE-%i' % self.cwe

    def get_cwe_url(self):
        if self.cwe is not None:
            return 'http://cwe.mitre.org/data/definitions/%i.html' % self.cwe

class Metadata(object):
    __slots__ = ('generator', 'sut', 'file_', 'stats')

    def __init__(self, generator, sut, file_, stats):
        assert isinstance(generator, Generator)
        if sut is not None:
            assert isinstance(sut, Sut)
        if file_ is not None:
            assert isinstance(file_, File)
        if stats is not None:
            assert isinstance(stats, Stats)
        self.generator = generator
        self.sut = sut
        self.file_ = file_
        self.stats = stats

    @classmethod
    def from_xml(cls, node):
        generator = Generator.from_xml(node.find('generator'))
        sut_node = node.find('sut')
        if sut_node is not None:
            sut = Sut.from_xml(sut_node)
        else:
            sut = None
        file_node = node.find('file')
        if file_node is not None:
            file_ = File.from_xml(file_node)
        else:
            file_ = None
        stats_node = node.find('stats')
        if stats_node is not None:
            stats = Stats.from_xml(stats_node)
        else:
            stats = None
        result = Metadata(generator, sut, file_, stats)
        return result

    def to_xml(self):
        node = ET.Element('metadata')
        node.append(self.generator.to_xml())
        if self.sut is not None:
            node.append(self.sut.to_xml())
        if self.file_ is not None:
            node.append(self.file_.to_xml())
        if self.stats is not None:
            node.append(self.stats.to_xml())
        return node

    def __repr__(self):
        return ('Metadata(generator=%r, sut=%r, file_=%r, stats=%r)'
                % (self.generator, self.sut, self.file_, self.stats))

    def accept(self, visitor):
        visitor.visit_metadata(self)
        self.generator.accept(visitor)
        if self.sut:
            self.sut.accept(visitor)
        if self.file_:
            self.file_.accept(visitor)
        if self.stats:
            self.stats.accept(visitor)

class Generator(object):
    __slots__ = ('name', 'version', )

    def __init__(self, name, version=None):
        assert isinstance(name, str)
        if version is not None:
            assert isinstance(version, str)
        self.name = name
        self.version = version

    @classmethod
    def from_xml(cls, node):
        result = Generator(name=node.get('name'),
                           version=node.get('version')) # optional
        return result

    def to_xml(self):
        node = ET.Element('generator')
        node.set('name', self.name)
        if self.version is not None:
            node.set('version', self.version)
        return node

    def __repr__(self):
        return ('Generator(name=%r, version=%r)'
                % (self.name, self.version))

    def accept(self, visitor):
        visitor.visit_generator(self)

class Sut(object):
    # FIXME: this part of the schema needs more thought/work
    __slots__ = ('text', )

    def __init__(self, text=None):
        self.text = text

    @classmethod
    def from_xml(cls, node):
        result = Sut()
        result.text = node.text
        return result

    def to_xml(self):
        node = ET.Element('sut')
        node.text = self.text
        return node

    def accept(self, visitor):
        visitor.visit_sut(self)

class Stats(object):
    __slots__ = ('wallclocktime', )

    def __init__(self, wallclocktime):
        assert isinstance(wallclocktime, float)
        self.wallclocktime = wallclocktime

    @classmethod
    def from_xml(cls, node):
        wallclocktime = float(node.get('wall-clock-time'))
        result = Stats(wallclocktime)
        return result

    def to_xml(self):
        node = ET.Element('stats')
        node.set('wall-clock-time', str(self.wallclocktime))
        return node

    def accept(self, visitor):
        visitor.visit_stats(self)

class Message(object):
    __slots__ = ('text', )

    def __init__(self, text):
        assert isinstance(text, str)
        self.text = text

    @classmethod
    def from_xml(cls, node):
        result = Message(node.text)
        return result

    def to_xml(self):
        node = ET.Element('message')
        node.text = self.text
        return node

    def __repr__(self):
        return 'Message(text=%r)' % (self.text, )

    def __eq__(self, other):
        return self.text == other.text

    def __ne__(self, other):
        return self.text != other.text

    def accept(self, visitor):
        visitor.visit_message(self)

class Notes(object):
    __slots__ = ('text', )

    def __init__(self, text):
        assert isinstance(text, str)
        self.text = text

    @classmethod
    def from_xml(cls, node):
        text = node.text
        result = Notes(text)
        return result

    def to_xml(self):
        node = ET.Element('notes')
        node.text = self.text
        return node

    def __repr__(self):
        return 'Notes(text=%r)' % (self.text, )

    def accept(self, visitor):
        visitor.visit_notes(self)

class Trace(object):
    __slots__ = ('states', )

    def __init__(self, states):
        assert isinstance(states, list)
        self.states = states

    def add_state(self, state):
        self.states.append(state)

    @classmethod
    def from_xml(cls, node):
        states = []
        for state_node in node.findall('state'):
            states.append(State.from_xml(state_node))
        result = Trace(states)
        return result

    def to_xml(self):
        node = ET.Element('trace')
        for state in self.states:
            node.append(state.to_xml())
        return node

    def __repr__(self):
        return 'Trace(states=%r)' % (self.states, )

    def accept(self, visitor):
        visitor.visit_notes(self)
        for state in self.states:
            state.accept(visitor)

class State(object):
    __slots__ = ('location', 'notes', )

    def __init__(self, location, notes):
        assert isinstance(location, Location)
        if notes is not None:
            assert isinstance(notes, Notes)
        self.location = location
        self.notes = notes

    @classmethod
    def from_xml(cls, node):
        location = Location.from_xml(node.find('location'))
        notes_node = node.find('notes')
        if notes_node is not None:
            notes = Notes.from_xml(notes_node)
        else:
            notes = None
        return State(location, notes)

    def to_xml(self):
        node = ET.Element('state')
        node.append(self.location.to_xml())
        if self.notes:
            node.append(self.notes.to_xml())
        return node

    def __repr__(self):
        return 'State(location=%r, notes=%r)' % (self.location, self.notes)

    def accept(self, visitor):
        visitor.visit_state(self)
        self.location.accept(visitor)
        self.notes.accept(visitor)

class Location(object):
    __slots__ = ('file', 'function', 'point', )

    def __init__(self, file, function, point):
        assert isinstance(file, File)
        if function is not None:
            assert isinstance(function, Function)
        assert isinstance(point, Point)
        self.file = file
        self.function = function
        self.point = point

    @classmethod
    def from_xml(cls, node):
        file = File.from_xml(node.find('file'))
        function_node = node.find('function')
        if function_node is not None:
            function = Function.from_xml(function_node)
        else:
            function = None
        point = Point.from_xml(node.find('point'))
        return Location(file, function, point)

    def to_xml(self):
        node = ET.Element('location')
        node.append(self.file.to_xml())
        if self.function is not None:
            node.append(self.function.to_xml())
        node.append(self.point.to_xml())
        return node

    def __repr__(self):
        return ('Location(file=%r, function=%r, point=%r)' %
                (self.file, self.function, self.point))

    def accept(self, visitor):
        visitor.visit_location(self)
        self.file.accept(visitor)
        if self.function:
            self.function.accept(visitor)
        self.point.accept(visitor)

    @property
    def line(self):
        return self.point.line

    @property
    def column(self):
        return self.point.column

class File(object):
    __slots__ = ('givenpath', 'abspath', 'hash_')

    def __init__(self, givenpath, abspath, hash_=None):
        assert isinstance(givenpath, str)
        if abspath is not None:
            assert isinstance(abspath, str)
        if hash_ is not None:
            assert isinstance(hash_, Hash)

        self.givenpath = givenpath
        self.abspath = abspath
        self.hash_ = hash_

    @classmethod
    def from_xml(cls, node):
        givenpath = node.get('given-path')
        abspath = node.get('absolute-path')
        hash_node = node.find('hash')
        if hash_node is not None:
            hash_ = Hash.from_xml(hash_node)
        else:
            hash_ = None
        result = File(givenpath, abspath, hash_)
        return result

    def to_xml(self):
        node = ET.Element('file')
        node.set('given-path', self.givenpath)
        if self.abspath:
            node.set('absolute-path', self.abspath)
        if self.hash_:
            node.append(self.hash_.to_xml())
        return node

    def __repr__(self):
        return ('File(givenpath=%r, abspath=%r hash_=%r)' %
                (self.givenpath, self.abspath, self.hash_))

    def accept(self, visitor):
        visitor.visit_file(self)

class Hash(object):
    __slots__ = ('alg', 'hexdigest')

    def __init__(self, alg, hexdigest):
        assert isinstance(alg, str)
        assert isinstance(hexdigest, str)
        self.alg = alg
        self.hexdigest = hexdigest

    @classmethod
    def from_xml(cls, node):
        alg = node.get('alg')
        hexdigest = node.get('hexdigest')
        result = Hash(alg, hexdigest)
        return result

    def to_xml(self):
        node = ET.Element('hash')
        node.set('alg', self.alg)
        node.set('hexdigest', self.hexdigest)
        return node

    def __repr__(self):
        return ('Hash(alg=%r, hexdigest=%r)' %
                (self.alg, self.hexdigest))

class Function(object):
    __slots__ = ('name', )

    def __init__(self, name):
        self.name = name

    @classmethod
    def from_xml(cls, node):
        name = node.get('name')
        result = Function(name)
        return result

    def to_xml(self):
        node = ET.Element('function')
        node.set('name', self.name)
        return node

    def __repr__(self):
        return 'Function(name=%r)' % self.name

    def __eq__(self, other):
        return self.name == other.name

    def __ne__(self, other):
        return self.name != other.name

    def accept(self, visitor):
        visitor.visit_function(self)

class Point(object):
    __slots__ = ('line', 'column', )

    def __init__(self, line, column):
        assert isinstance(line, int)
        assert isinstance(column, int)
        self.line = line
        self.column = column

    @classmethod
    def from_xml(cls, node):
        line = int(node.get('line'))
        column = int(node.get('column'))
        result = Point(line, column)
        return result

    def to_xml(self):
        node = ET.Element('point')
        node.set('line', str(self.line))
        node.set('column', str(self.column))
        return node

    def __repr__(self):
        return ('Location(line=%r, column=%r)' %
                (self.line, self.column))

    def __eq__(self, other):
        if self.line == other.line:
            if self.column == other.column:
                return True

    def __ne__(self, other):
        return not self == other

    def accept(self, visitor):
        visitor.visit_point(self)

#
# Traversal of the report structure
#

class Visitor:
    def visit_analysis(self, analysis):
        pass

    def visit_warning(self, warning):
        pass

    def visit_metadata(self, metadata):
        pass

    def visit_generator(self, generator):
        pass

    def visit_sut(self, sut):
        pass

    def visit_stats(self, stats):
        pass

    def visit_message(self, message):
        pass

    def visit_notes(self, notes):
        pass

    def visit_state(self, state):
        pass

    def visit_location(self, location):
        pass

    def visit_file(self, file_):
        pass

    def visit_function(self, function):
        pass

    def visit_point(self, point):
        pass

def main():
    for filename in sorted(glob.glob('examples/example-*.xml')):
        print('%s as gcc output:' % filename)
        with open(filename) as f:
            r = Analysis.from_xml(f)
            for w in r.results:
                w.write_as_gcc_output(sys.stderr)
            sys.stderr.write('  XML: %s\n' % r.to_xml_str())

if __name__ == '__main__':
    main()
