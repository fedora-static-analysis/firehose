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
from subprocess import Popen, PIPE
import sys
import xml.etree.ElementTree as ET

class Report:
    __slots__ = ('cwe',
                 'metadata',
                 'location',
                 'message',
                 'notes',
                 'trace')
    def __init__(self,
                 cwe,
                 metadata,
                 location,
                 message,
                 notes,
                 trace):
        if cwe is not None:
            assert isinstance(cwe, str)
        assert isinstance(metadata, Metadata)
        assert isinstance(location, Location)
        assert isinstance(message, Message)
        if notes:
            assert isinstance(notes, Notes)
        if trace:
            assert isinstance(trace, Trace)
        self.cwe = cwe
        self.metadata = metadata
        self.location = location
        self.message = message
        self.notes = notes
        self.trace = trace

    @classmethod
    def from_xml(cls, fileobj):
        tree = ET.parse(fileobj)
        root = tree.getroot()

        cwe = root.get('cwe')
        metadata = Metadata.from_xml(root.find('metadata'))
        location = Location.from_xml(root.find('location'))
        message = Message.from_xml(root.find('message'))
        notes_node = root.find('notes')
        if notes_node is not None:
            notes = Notes.from_xml(notes_node)
        else:
            notes = None
        trace_node = root.find('trace')
        if trace_node is not None:
            trace = Trace.from_xml(trace_node)
        else:
            trace = None
        return Report(cwe, metadata, location, message, notes, trace)

    def to_xml(self):
        tree = ET.ElementTree()
        node = ET.Element('report')
        tree._setroot(node)
        if self.cwe is not None:
            node.set('cwe', self.cwe)
        node.append(self.metadata.to_xml())
        node.append(self.location.to_xml())
        node.append(self.message.to_xml())
        if self.notes:
            node.append(self.notes.to_xml())
        if self.trace:
            node.append(self.trace.to_xml())
        return tree

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
        if self.cwe:
            cwetext = ' [%s]' % self.cwe
        else:
            cwetext = ''
        if self.location.function is not None:
            writeln("%s: In function '%s':%s"
                    % (self.location.file.name,
                       self.location.function.name,
                       cwetext))
        diagnostic(filename=self.location.file.name,
                   line=self.location.line,
                   column=self.location.column,
                   kind='warning',
                   msg=self.message.text)
        if self.notes:
            writeln(self.notes.text.rstrip())
        if self.trace:
            for state in self.trace.states:
                notes = state.notes
                diagnostic(filename=state.location.file.name,
                           line=state.location.line,
                           column=state.location.column,
                           kind='note',
                           msg=notes.text if notes else '')

class Metadata:
    __slots__ = ('generator', 'sut', )

    def __init__(self, generator, sut):
        assert isinstance(generator, Generator)
        assert isinstance(sut, Sut)
        self.generator = generator
        self.sut = sut

    @classmethod
    def from_xml(cls, node):
        generator = Generator.from_xml(node.find('generator'))
        sut = Sut.from_xml(node.find('sut'))
        result = Metadata(generator, sut)
        return result

    def to_xml(self):
        node = ET.Element('metadata')
        node.append(self.generator.to_xml())
        node.append(self.sut.to_xml())
        return node

class Generator:
    __slots__ = ('name', 'version', 'internalid', )

    def __init__(self, name, version, internalid=None):
        assert isinstance(name, str)
        assert isinstance(version, str)
        if internalid is not None:
            assert isinstance(internalid, str)
        self.name = name
        self.version = version
        self.internalid = internalid

    @classmethod
    def from_xml(cls, node):
        result = Generator(node.get('name'),
                           node.get('version'),
                           node.get('internalid')) # FIXME: it's optional
        return result

    def to_xml(self):
        node = ET.Element('generator')
        node.set('name', self.name)
        node.set('version', self.version)
        if self.internalid is not None:
            node.set('internal-id', self.internalid)
        return node

class Sut:
    # FIXME: this part of the schema needs more thought/work
    __slots__ = ('text', )

    def __init__(self):
        pass

    @classmethod
    def from_xml(cls, node):
        result = Sut()
        return result

    def to_xml(self):
        node = ET.Element('sut')
        return node

class Message:
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

class Notes:
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

class Trace:
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

class State:
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

class Location:
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
        node.append(self.function.to_xml())
        node.append(self.point.to_xml())
        return node

    @property
    def line(self):
        return self.point.line

    @property
    def column(self):
        return self.point.column

class File:
    __slots__ = ('name', )

    def __init__(self, name):
        self.name = name

    @classmethod
    def from_xml(cls, node):
        name = node.get('name')
        result = File(name)
        return result

    def to_xml(self):
        node = ET.Element('file')
        node.set('name', self.name)
        return node

class Function:
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

class Point:
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

def test_creation():
    r = Report(cwe='CWE-681',
               metadata=Metadata(generator=Generator(name='cpychecker',
                                                     version='0.11',
                                                     internalid='refcount-too-high'),
                                 sut=Sut()),
               location=Location(file=File('foo.c'),
                                 function=Function('bar'),
                                 point=Point(10, 15)),
               message=Message(text='something bad involving pointers'),
               notes=Notes('foo'),
               trace=Trace([State(location=Location(file=File('foo.c'),
                                                    function=Function('bar'),
                                                    point=Point(10, 15)),
                                  notes=Notes('something')),
                            State(location=Location(file=File('foo.c'),
                                                    function=Function('bar'),
                                                    point=Point(10, 15)),
                                  notes=Notes('something')),
                            State(location=Location(file=File('foo.c'),
                                                    function=Function('bar'),
                                                    point=Point(10, 15)),
                                  notes=Notes('something'))
                            ])
               )
    r.write_as_gcc_output(sys.stderr)
    r.to_xml().write(sys.stdout)

    # TODO: Does it roundtrip?
    with open('test.xml', 'w') as f:
        r.to_xml().write(f)
    with open('test.xml', 'r') as f:
        r2 = Report.from_xml(f)

    # TODO: Does it validate?
    #r.write_xml('foo.xml')
    #p = Popen(['xmllint', '--relaxng', 'firehose.rng', 'foo.xml'])
    #p.communicate()

def main():
    for filename in sorted(glob.glob('examples/example-*.xml')):
        print('%s as gcc output:' % filename)
        with open(filename) as f:
            r = Report.from_xml(f)
            r.write_as_gcc_output(sys.stderr)

    test_creation()

if __name__ == '__main__':
    main()
