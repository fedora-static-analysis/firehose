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
import sys
import xml.etree.ElementTree as ET

class XmlWrapper:
    """
    Wrapper around an XML node
    """
    def __init__(self, _node):
        assert _node is not None
        self._node = _node

    def __eq__(self, other):
        if not isinstance(other, XmlWrapper):
            return False
        return self._node == other._node

class Report(XmlWrapper):
    @classmethod
    def from_xml(cls, fileobj):
        tree = ET.parse(fileobj)
        return Report(tree.getroot())

    @property
    def cwe(self):
        return self._node.get('cwe')

    @property
    def location(self):
        return Location(self._node.find('location'))

    @property
    def message(self):
        return Message(self._node.find('message'))

    @property
    def notes(self):
        notes_node = self._node.find('notes')
        if notes_node is not None:
            return Notes(notes_node)
        else:
            return None

    @property
    def trace(self):
        trace_node = self._node.find('trace')
        if trace_node is not None:
            return Trace(trace_node)
        else:
            return None

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
            for state in self.trace:
                notes = state.notes
                diagnostic(filename=state.location.file.name,
                           line=state.location.line,
                           column=state.location.column,
                           kind='note',
                           msg=notes.text if notes else '')

class Message(XmlWrapper):
    @property
    def text(self):
        return self._node.text

class Notes(XmlWrapper):
    @property
    def text(self):
        return self._node.text

class Trace(XmlWrapper):
    def __iter__(self):
        for state_node in self._node.findall('state'):
            yield State(state_node)

class State(XmlWrapper):
    @property
    def location(self):
        return Location(self._node.find('location'))

    @property
    def notes(self):
        notes_node = self._node.find('notes')
        if notes_node is not None:
            return Notes(notes_node)
        else:
            return None

class Location(XmlWrapper):
    @property
    def file(self):
        return File(self._node.find('file'))

    @property
    def function(self):
        return Function(self._node.find('function'))

    @property
    def line(self):
        p = Point(self._node.find('point'))
        return p.line

    @property
    def column(self):
        p = Point(self._node.find('point'))
        return p.column

class File(XmlWrapper):
    @property
    def name(self):
        return self._node.get('name')

class Function(XmlWrapper):
    @property
    def name(self):
        return self._node.get('name')

class Point(XmlWrapper):
    @property
    def line(self):
        return int(self._node.get('line'))

    @property
    def column(self):
        return int(self._node.get('column'))

def main():
    for filename in sorted(glob.glob('examples/*.xml')):
        print('%s as gcc output:' % filename)
        with open(filename) as f:
            r = Report.from_xml(f)
            r.write_as_gcc_output(sys.stderr)

if __name__ == '__main__':
    main()
