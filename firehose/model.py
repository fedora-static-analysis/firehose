#   Copyright 2013 David Malcolm <dmalcolm@redhat.com>
#   Copyright 2013 Red Hat, Inc.
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

# Python module for working with Firehose XML files, also, potentially,
# a command-line tool

from collections import OrderedDict, namedtuple
from subprocess import Popen, PIPE
import xml.etree.ElementTree as ET
import hashlib
import glob
import sys
import os

from six import BytesIO, string_types, integer_types, iteritems

_string_type = string_types[0]


class Attribute(namedtuple('Attribute', ('name', 'type', 'nullable'))):
    """
    Description of an attribute of a class.

    name : the name of the attribute

    type : one of:
             * a string containing the name of the type (so that we can make
               forward-references to types)
             * int, float, _string_type, meaning this attribute is of that
               type
             * a list containing one string, meaning this attribute is a
               list of that (named) type

    nullable: boolean: can this attribute be None?
    """
    def __new__(self, name, type, nullable=False):
        return super(Attribute, self).__new__(self, name, type, nullable)

    def resolve_type(self):
        return globals()[self.type]

    def from_json(self, jsonobj):
        if jsonobj is None:
            return jsonobj
        if isinstance(self.type, list):
            # expect a 1-length string containing the internal type of the list
            innertypename = self.type[0]
            innertype = globals()[innertypename]
            return [innertype.from_json(jsonitem) for jsonitem in jsonobj]
        if self.type == _string_type:
            return jsonobj
        if self.type == int:
            return jsonobj
        if self.type == float:
            return jsonobj
        return self.resolve_type().from_json(jsonobj)

def to_json(obj):
    if hasattr(obj, 'to_json'):
        return obj.to_json()
    if isinstance(obj, list):
        return [to_json(item) for item in obj]
    if isinstance(obj, (int, _string_type, float, type(None))):
        return obj
    raise TypeError("don't know how to convert %r to JSON" % obj)

def from_json_using_attrs(cls, jsonobj):
    """
    Given a class cls and a jsonobj, construct an instance of cls, using
    its attrs metadata.
    """
    if jsonobj is None:
        return None
    kwargs = {}
    for attr in cls.attrs:
        attrjson = jsonobj[attr.name]
        kwargs[attr.name] = attr.from_json(attrjson)
    result = cls(**kwargs)
    return result

class JsonMixin(object):
    def to_json(self):
        result = {}
        for attr in self.attrs:
            result[attr.name] = to_json(getattr(self, attr.name))
        return result

    @classmethod
    def from_json(cls, jsonobj):
        return from_json_using_attrs(cls, jsonobj)

    def __eq__(self, other):
        for attr in self.attrs:
            try:
                if getattr(self, attr.name) != getattr(other, attr.name):
                    return False
            except AttributeError:
                return False

        return True

    def __ne__(self, other):
        return not (self == other)

class Analysis(JsonMixin):
    attrs = [Attribute('metadata', 'Metadata'),
             Attribute('results', ['Result']),
             Attribute('customfields', 'CustomFields', nullable=True)]

    def __init__(self, metadata, results, customfields=None):
        assert isinstance(metadata, Metadata)
        assert isinstance(results, list)
        if customfields is not None:
            assert isinstance(customfields, CustomFields)
        for result in results:
            assert isinstance(result, Result)

        self.metadata = metadata
        self.results = results
        self.customfields = customfields

    @classmethod
    def from_xml(cls, fileobj):
        tree = ET.parse(fileobj)
        root = tree.getroot()

        metadata = Metadata.from_xml(root.find('metadata'))
        results_node = root.find('results')
        results = []
        for result_node in results_node:
            if result_node.tag == 'issue':
                results.append(Issue.from_xml(result_node))
            elif result_node.tag == 'failure':
                results.append(Failure.from_xml(result_node))
            elif result_node.tag == 'info':
                results.append(Info.from_xml(result_node))
        customfields_node = root.find('custom-fields')
        if customfields_node is not None:
            customfields = CustomFields.from_xml(customfields_node)
        else:
            customfields = None
        return Analysis(metadata, results, customfields)

    def to_xml(self):
        tree = ET.ElementTree()
        node = ET.Element('analysis')
        tree._setroot(node)
        node.append(self.metadata.to_xml())
        results_node = ET.Element('results')
        node.append(results_node)
        for result in self.results:
            results_node.append(result.to_xml())
        if self.customfields is not None:
            node.append(self.customfields.to_xml())
        return tree

    def to_xml_bytes(self):
        xml = self.to_xml()
        output = BytesIO()
        xml.write(output, encoding='utf-8')
        return output.getvalue()

    def __repr__(self):
        return ('Analysis(metadata=%r, results=%r, customfields=%r)'
                % (self.metadata, self.results, self.customfields))

    def __hash__(self):
        # (self.results is a list and is thus not hashable)
        return hash(self.metadata)

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

                    with open(bestpath, 'rb') as f:
                        h = hashlib.new(hashalg)
                        h.update(f.read())
                        file_.hash_ = Hash(alg=hashalg, hexdigest=h.hexdigest())

        visitor = FixupFiles(relativedir, hashalg)
        self.accept(visitor)

    def set_custom_field(self, name, value):
        if self.customfields is None:
            self.customfields = CustomFields()
        self.customfields[name] = value

class Result(JsonMixin):
    @classmethod
    def from_json(cls, jsonobj):
        if jsonobj['type'] == 'Issue':
            return from_json_using_attrs(Issue, jsonobj)
        elif jsonobj['type'] == 'Failure':
            return from_json_using_attrs(Failure, jsonobj)
        elif jsonobj['type'] == 'Info':
            return from_json_using_attrs(Info, jsonobj)
        raise TypeError('unknown type: %r' % jsonobj['type'])

class Issue(Result):
    attrs = [Attribute('cwe', int, nullable=True),
             Attribute('testid', _string_type, nullable=True),
             Attribute('location', 'Location'),
             Attribute('message', 'Message'),
             Attribute('notes', 'Notes', nullable=True),
             Attribute('trace', 'Trace', nullable=True),
             Attribute('severity', _string_type, nullable=True),
             Attribute('customfields', 'CustomFields', nullable=True)]

    def __init__(self,
                 cwe,
                 testid,
                 location,
                 message,
                 notes,
                 trace,
                 severity=None,
                 customfields=None):
        if cwe is not None:
            assert isinstance(cwe, int)
        if testid is not None:
            assert isinstance(testid, _string_type)
        assert isinstance(location, Location)
        assert isinstance(message, Message)
        if notes:
            assert isinstance(notes, Notes)
        if trace:
            assert isinstance(trace, Trace)
        if severity is not None:
            assert isinstance(severity, _string_type)
        if customfields is not None:
            assert isinstance(customfields, CustomFields)
        self.cwe = cwe
        self.testid = testid
        self.location = location
        self.message = message
        self.notes = notes
        self.trace = trace
        self.severity = severity
        self.customfields = customfields

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
        severity = node.get('severity')
        customfields_node = node.find('custom-fields')
        if customfields_node is not None:
            customfields = CustomFields.from_xml(customfields_node)
        else:
            customfields = None
        return Issue(cwe, testid, location, message, notes, trace, severity, customfields)

    def to_xml(self):
        node = ET.Element('issue')
        if self.cwe is not None:
            node.set('cwe', str(self.cwe))
        if self.testid is not None:
            node.set('test-id', str(self.testid))
        node.append(self.message.to_xml())
        if self.notes:
            node.append(self.notes.to_xml())
        node.append(self.location.to_xml())
        if self.trace:
            node.append(self.trace.to_xml())
        if self.severity is not None:
            node.set('severity', str(self.severity))
        if self.customfields is not None:
            node.append(self.customfields.to_xml())
        return node

    def to_json(self):
        jsonobj = JsonMixin.to_json(self)
        jsonobj['type'] = 'Issue'
        return jsonobj

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
        return ('Issue(cwe=%r, testid=%r, location=%r, message=%r,'
                ' notes=%r, trace=%r, severity=%r, customfields=%r)'
                % (self.cwe, self.testid, self.location, self.message,
                   self.notes, self.trace, self.severity, self.customfields))

    def __hash__(self):
        return (hash(self.cwe) ^ hash(self.testid)
                ^ hash(self.location) ^ hash(self.message)
                ^ hash(self.notes) ^ hash(self.trace) ^ hash(self.severity))

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

class Failure(Result):
    attrs = [Attribute('failureid', _string_type, nullable=True),
             Attribute('location', 'Location'),
             Attribute('message', 'Message'),
             Attribute('customfields', 'CustomFields', nullable=True)]

    def __init__(self, failureid, location, message, customfields):
        if failureid is not None:
            assert isinstance(failureid, _string_type)
        if location is not None:
            assert isinstance(location, Location)
        if message is not None:
            assert isinstance(message, Message)
        if customfields is not None:
            assert isinstance(customfields, CustomFields)
        self.failureid = failureid
        self.location = location
        self.message = message
        self.customfields = customfields

    @classmethod
    def from_xml(cls, node):
        failureid = node.get('failure-id')
        location_node = node.find('location')
        if location_node is not None:
            location = Location.from_xml(location_node)
        else:
            location = None
        message_node = node.find('message')
        if message_node is not None:
            message = Message.from_xml(message_node)
        else:
            message = None
        customfields_node = node.find('custom-fields')
        if customfields_node is not None:
            customfields = CustomFields.from_xml(customfields_node)
        else:
            customfields = None
        return Failure(failureid, location, message, customfields)

    def to_xml(self):
        node = ET.Element('failure')

        if self.failureid is not None:
            node.set('failure-id', self.failureid)

        if self.location is not None:
            node.append(self.location.to_xml())

        if self.message is not None:
            node.append(self.message.to_xml())

        if self.customfields is not None:
            node.append(self.customfields.to_xml())

        return node

    def to_json(self):
        jsonobj = JsonMixin.to_json(self)
        jsonobj['type'] = 'Failure'
        return jsonobj

    def __repr__(self):
        return ('Failure(failureid=%r, location=%r, message=%r, customfields=%r)'
                % (self.failureid, self.location, self.message, self.customfields))

    def __hash__(self):
        return (hash(self.failureid) ^ hash(self.location)
                ^ hash(self.message) ^ hash(self.customfields))

    def accept(self, visitor):
        visitor.visit_failure(self)
        if self.location:
            self.location.accept(visitor)
        if self.message:
            self.message.accept(visitor)

class Info(Result):
    attrs = [Attribute('infoid', _string_type, nullable=True),
             Attribute('location', 'Location', nullable=True),
             Attribute('message', 'Message', nullable=True),
             Attribute('customfields', 'CustomFields', nullable=True)]

    def __init__(self, infoid, location, message, customfields):
        if infoid is not None:
            assert isinstance(infoid, _string_type)
        if location is not None:
            assert isinstance(location, Location)
        if message is not None:
            assert isinstance(message, Message)
        if customfields is not None:
            assert isinstance(customfields, CustomFields)
        self.infoid = infoid
        self.location = location
        self.message = message
        self.customfields = customfields

    @classmethod
    def from_xml(cls, node):
        infoid = node.get('info-id')
        location_node = node.find('location')
        if location_node is not None:
            location = Location.from_xml(location_node)
        else:
            location = None
        message_node = node.find('message')
        if message_node is not None:
            message = Message.from_xml(message_node)
        else:
            message = None
        customfields_node = node.find('custom-fields')
        if customfields_node is not None:
            customfields = CustomFields.from_xml(customfields_node)
        else:
            customfields = None
        return Info(infoid, location, message, customfields)

    def to_xml(self):
        node = ET.Element('info')

        if self.infoid is not None:
            node.set('info-id', self.infoid)

        if self.location is not None:
            node.append(self.location.to_xml())

        if self.message is not None:
            node.append(self.message.to_xml())

        if self.customfields is not None:
            node.append(self.customfields.to_xml())

        return node

    def to_json(self):
        jsonobj = JsonMixin.to_json(self)
        jsonobj['type'] = 'Info'
        return jsonobj

    def __repr__(self):
        return ('Info(infoid=%r, location=%r, message=%r, customfields=%r)'
                % (self.infoid, self.location, self.message, self.customfields))

    def __hash__(self):
        return (hash(self.infoid) ^ hash(self.location)
                ^ hash(self.message) ^ hash(self.customfields))

    def accept(self, visitor):
        visitor.visit_info(self)
        if self.location:
            self.location.accept(visitor)
        if self.message:
            self.message.accept(visitor)

class Metadata(JsonMixin):
    attrs = [Attribute('generator', 'Generator'),
             Attribute('sut', 'Sut', nullable=True),
             Attribute('file_', 'File', nullable=True),
             Attribute('stats', 'Stats', nullable=True)]

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

    def __hash__(self):
        return (hash(self.generator) ^ hash(self.sut)
                ^ hash(self.file_) ^ hash(self.stats))

    def accept(self, visitor):
        visitor.visit_metadata(self)
        self.generator.accept(visitor)
        if self.sut:
            self.sut.accept(visitor)
        if self.file_:
            self.file_.accept(visitor)
        if self.stats:
            self.stats.accept(visitor)

class Generator(JsonMixin):
    attrs = [Attribute('name', _string_type),
             Attribute('version', _string_type, nullable=True),
             ]

    def __init__(self, name, version=None):
        assert isinstance(name, _string_type)
        if version is not None:
            assert isinstance(version, _string_type)
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

    def __hash__(self):
        return hash(self.name) ^ hash(self.version)

    def accept(self, visitor):
        visitor.visit_generator(self)

class Sut(JsonMixin):
    # FIXME: this part of the schema needs more thought/work

    @classmethod
    def from_xml(cls, node):
        srpm_node = node.find('source-rpm')
        if srpm_node is not None:
            return SourceRpm.from_xml(srpm_node)

        dsc_node = node.find('debian-source')
        if dsc_node is not None:
            return DebianSource.from_xml(dsc_node)

        deb_node = node.find('debian-binary')
        if deb_node is not None:
            return DebianBinary.from_xml(deb_node)

        raise ValueError('unknown sut kind')

    def to_xml(self):
        innernode = self._to_xml_inner_node()
        node = ET.Element('sut')
        node.append(innernode)
        return node

    def _to_xml_inner_node(self):
        raise NotImplementedError

    @classmethod
    def from_json(cls, jsonobj):
        subclsname = jsonobj['type']
        subcls = globals()[subclsname]
        return from_json_using_attrs(subcls, jsonobj)

    def accept(self, visitor):
        visitor.visit_sut(self)

class SourceRpm(Sut):
    attrs = [Attribute('name', _string_type),
             Attribute('version', _string_type),
             Attribute('release', _string_type),
             Attribute('buildarch', _string_type),
             ]

    def __init__(self, name, version, release, buildarch):
        assert isinstance(name, _string_type)
        assert isinstance(version, _string_type)
        assert isinstance(release, _string_type)
        assert isinstance(buildarch, _string_type)
        self.name = name
        self.version = version
        self.release = release
        self.buildarch = buildarch

    @classmethod
    def from_xml(cls, node):
        result = SourceRpm(name=node.get('name'),
                           version=node.get('version'),
                           release=node.get('release'),
                           buildarch=node.get('build-arch'))
        return result

    def _to_xml_inner_node(self):
        node = ET.Element('source-rpm')
        node.set('name', self.name)
        node.set('version', self.version)
        node.set('release', self.release)
        node.set('build-arch', self.buildarch)
        return node

    def to_json(self):
        result = JsonMixin.to_json(self)
        result['type']= 'SourceRpm'
        return result

    def __repr__(self):
        return ('SourceRpm(name=%r, version=%r, release=%r, buildarch=%r)'
                % (self.name, self.version, self.release, self.buildarch))

    def __hash__(self):
        return (hash(self.name) ^ hash(self.version)
                ^ hash(self.release) ^ hash(self.buildarch))


class DebianBinary(Sut):
    """
    Internal Firehose represntation of a Debian binary package. This Object
    is extremely similar to a SourceRpm.
    """
    attrs = [Attribute('name', _string_type),
             Attribute('version', _string_type),
             Attribute('release', _string_type, nullable=True),
             Attribute('buildarch', _string_type)]

    def __init__(self, name, version, release, buildarch):
        """
        Simple constructor. Name should be the *binary* package name,
        version should match Upstream's version number, and release (if
        given) should be the Debian package local version. This should
        only be ommited if the package is a Debian Native package.

        buildarch is the Debian binary arch (like amd64, armhf, hurd-i386)
        """
        assert isinstance(name, _string_type)
        assert isinstance(version, _string_type)
        assert (isinstance(release, _string_type) or release is None)
        assert isinstance(buildarch, _string_type)

        if release is None and "-" in version:
            # XXX: Do we have a better Exception for here?
            raise Exception("Native package with dash in the version string")

        self.name = name
        self.version = version
        self.release = release
        self.buildarch = buildarch

    @classmethod
    def from_xml(cls, node):
        """
        Construct a DebianSource object from an XML payload.
        """
        result = DebianBinary(name=node.get('name'),
                              version=node.get('version'),
                              release=node.get('release'),
                              buildarch=node.get('build-arch'))
        return result

    def _to_xml_inner_node(self):
        """
        (internal use only)

        Produce a DebianSource XML ET for searlizing the data back down to
        XML again.
        """
        node = ET.Element('debian-binary')
        node.set('name', self.name)
        node.set('version', self.version)
        if not self.release is None:
            node.set('release', self.release)
        node.set('build-arch', self.buildarch)
        return node

    def to_json(self):
        result = JsonMixin.to_json(self)
        result['type']= 'DebianBinary'
        return result

    def __repr__(self):
        return ('DebianBinary(name=%r, version=%r, release=%r, arch=%r)'
                % (self.name, self.version, self.release, self.buildarch))

    def __hash__(self):
        return (hash(self.name) ^ hash(self.version)
                ^ hash(self.release) ^ hash(self.buildarch))


class DebianSource(Sut):
    """
    Internal Firehose represntation of a Debian source package. This Object
    is extremely similar to a SourceRpm, but does not include the `buildarch`
    attribute.
    """
    attrs = [Attribute('name', _string_type),
             Attribute('version', _string_type),
             Attribute('release', _string_type, nullable=True)]

    def __init__(self, name, version, release):
        """
        Simple constructor. Name should be the *source* package name,
        version should match Upstream's version number, and release (if
        given) should be the Debian package local version. This should
        only be ommited if the package is a Debian Native package.
        """
        assert isinstance(name, _string_type)
        assert isinstance(version, _string_type)
        assert (isinstance(release, _string_type) or release is None)
        if release is None and "-" in version:
            # XXX: Do we have a better Exception for here?
            raise Exception("Native package with dash in the version string")

        self.name = name
        self.version = version
        self.release = release

    @classmethod
    def from_xml(cls, node):
        """
        Construct a DebianSource object from an XML payload.
        """
        result = DebianSource(name=node.get('name'),
                              version=node.get('version'),
                              release=node.get('release'))
        return result

    def _to_xml_inner_node(self):
        """
        (internal use only)

        Produce a DebianSource XML ET for searlizing the data back down to
        XML again.
        """
        node = ET.Element('debian-source')
        node.set('name', self.name)
        node.set('version', self.version)
        if not self.release is None:
            node.set('release', self.release)
        return node

    def to_json(self):
        result = JsonMixin.to_json(self)
        result['type']= 'DebianSource'
        return result

    def __repr__(self):
        return ('DebianSource(name=%r, version=%r, release=%r)'
                % (self.name, self.version, self.release))

    def __hash__(self):
        return (hash(self.name) ^ hash(self.version)
                ^ hash(self.release))


class Stats(JsonMixin):
    attrs = [Attribute('wallclocktime', float)]

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

    def __repr__(self):
        return 'Stats(wallclocktime=%r)' % (self.wallclocktime, )

    def __hash__(self):
        return hash(self.wallclocktime)

    def accept(self, visitor):
        visitor.visit_stats(self)

class Message(JsonMixin):
    attrs = [Attribute('text', _string_type)]

    def __init__(self, text):
        assert isinstance(text, _string_type)
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

    def __hash__(self):
        return hash(self.text)

    def accept(self, visitor):
        visitor.visit_message(self)

class Notes(JsonMixin):
    attrs = [Attribute('text', _string_type)]

    def __init__(self, text):
        assert isinstance(text, _string_type)
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

    def __hash__(self):
        return hash(self.text)

    def accept(self, visitor):
        visitor.visit_notes(self)

class Trace(JsonMixin):
    attrs = [Attribute('states', ['State'])]

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

    def __hash__(self):
        result = 0
        for state in self.states:
            result ^= hash(state)
        return result

    def accept(self, visitor):
        visitor.visit_notes(self)
        for state in self.states:
            state.accept(visitor)

class State(JsonMixin):
    attrs = [Attribute('location', 'Location'),
             Attribute('notes', 'Notes', nullable=True)]

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

    def __hash__(self):
        return hash(self.location) ^ hash(self.notes)

    def accept(self, visitor):
        visitor.visit_state(self)
        self.location.accept(visitor)
        if self.notes:
            self.notes.accept(visitor)

class Location(JsonMixin):
    attrs = [Attribute('file', 'File'),
             Attribute('function', 'Function', nullable=True),
             Attribute('point', 'Point', nullable=True),
             Attribute('range_', 'Range', nullable=True)]

    def __init__(self, file, function, point=None, range_=None):
        assert isinstance(file, File)
        if function is not None:
            assert isinstance(function, Function)
        if point is not None:
            assert isinstance(point, Point)
        if range_ is not None:
            assert isinstance(range_, Range)
        self.file = file
        self.function = function
        self.point = point
        self.range_ = range_

    @classmethod
    def from_xml(cls, node):
        file = File.from_xml(node.find('file'))
        function_node = node.find('function')
        if function_node is not None:
            function = Function.from_xml(function_node)
        else:
            function = None
        point_node = node.find('point')
        if point_node is not None:
            point = Point.from_xml(point_node)
        else:
            point = None
        range_node = node.find('range')
        if range_node is not None:
            range_ = Range.from_xml(range_node)
        else:
            range_ = None
        return Location(file, function, point, range_)

    def to_xml(self):
        node = ET.Element('location')
        node.append(self.file.to_xml())
        if self.function is not None:
            node.append(self.function.to_xml())
        if self.point is not None:
            node.append(self.point.to_xml())
        if self.range_ is not None:
            node.append(self.range_.to_xml())
        return node

    def __repr__(self):
        return ('Location(file=%r, function=%r, point=%r, range_=%r)' %
                (self.file, self.function, self.point, self.range_))

    def __hash__(self):
        return (hash(self.file) ^ hash(self.function)
                ^ hash(self.point) ^ hash(self.range_))

    def accept(self, visitor):
        visitor.visit_location(self)
        self.file.accept(visitor)
        if self.function:
            self.function.accept(visitor)
        if self.point:
            self.point.accept(visitor)
        if self.range_:
            self.range_.accept(visitor)

    @property
    def line(self):
        if self.point is not None:
            return self.point.line
        if self.range_ is not None:
            return self.range_.start.line

    @property
    def column(self):
        if self.point is not None:
            return self.point.column
        if self.range_ is not None:
            return self.range_.start.column

class File(JsonMixin):
    attrs = [Attribute('givenpath', _string_type),
             Attribute('abspath',  _string_type, nullable=True),
             Attribute('hash_',  'Hash', nullable=True)]

    def __init__(self, givenpath, abspath, hash_=None):
        assert isinstance(givenpath, _string_type)
        if abspath is not None:
            assert isinstance(abspath, _string_type)
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
        return ('File(givenpath=%r, abspath=%r, hash_=%r)' %
                (self.givenpath, self.abspath, self.hash_))

    def __hash__(self):
        return hash(self.givenpath) ^ hash(self.abspath) ^ hash(self.hash_)

    def accept(self, visitor):
        visitor.visit_file(self)

class Hash(JsonMixin):
    attrs = [Attribute('alg', _string_type),
             Attribute('hexdigest',  _string_type)]

    def __init__(self, alg, hexdigest):
        assert isinstance(alg, _string_type)
        assert isinstance(hexdigest, _string_type)
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

    def __hash__(self):
        return hash(self.alg) ^ hash(self.hexdigest)

class Function(JsonMixin):
    attrs = [Attribute('name', _string_type)]

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

    def __hash__(self):
        return hash(self.name)

    def accept(self, visitor):
        visitor.visit_function(self)

class Point(JsonMixin):
    attrs = [Attribute('line', int),
             Attribute('column', int)]

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
        return ('Point(line=%r, column=%r)' %
                (self.line, self.column))

    def __hash__(self):
        return hash(self.line) ^ hash(self.column)

    def accept(self, visitor):
        visitor.visit_point(self)

class Range(JsonMixin):
    attrs = [Attribute('start', 'Point'),
             Attribute('end', 'Point')]

    def __init__(self, start, end):
        assert isinstance(start, Point)
        assert isinstance(end, Point)
        self.start = start
        self.end = end

    @classmethod
    def from_xml(cls, node):
        children = list(node)
        start = Point.from_xml(children[0])
        end = Point.from_xml(children[1])
        result = Range(start, end)
        return result

    def to_xml(self):
        node = ET.Element('range')
        node.append(self.start.to_xml())
        node.append(self.end.to_xml())
        return node

    def __repr__(self):
        return ('Range(start=%r, end=%r)' %
                (self.start, self.end))

    def __hash__(self):
        return hash(self.start) ^ hash(self.end)

    def accept(self, visitor):
        visitor.visit_range(self)
        self.start.accept(visitor)
        self.end.accept(visitor)

class CustomFields(OrderedDict):
    @classmethod
    def from_xml(cls, node):
        kvs = []
        for child_node in node:
            if child_node.tag == 'str-field':
                value = child_node.text
                if value is None:
                    value = ''
            elif child_node.tag == 'int-field':
                value = int(child_node.text)
            else:
                raise ValueError('unrecognized element within'
                                 ' <custom-fields>: %s'
                                 % child_node.tag)
            key = child_node.get('name')
            if key is None:
                raise ValueError('missing "name" attribute within'
                                 ' <%s>' % child_node.tag)
            kvs.append( (key, value) )
        result = cls(kvs)
        return result

    def to_xml(self):
        node = ET.Element('custom-fields')
        for key, value in iteritems(self):
            if isinstance(value, _string_type):
                tag = 'str-field'
                text = value
            elif isinstance(value, integer_types):
                tag = 'int-field'
                text = str(value)
            else:
                raise TypeError('unhandled type within CustomFields instance')
            field_node = ET.Element(tag)
            field_node.set('name', key)
            field_node.text = text
            node.append(field_node)
        return node

    @classmethod
    def from_json(cls, jsonobj):
        if jsonobj is None:
            return None
        return cls(jsonobj)

    def to_json(self):
        return OrderedDict(self)

    def __hash__(self):
        # dicts are usually mutable, but it would be useful to hash
        # CustomFields instances (and assume they don't change from under
        # us)
        result = 0
        for key, value in self.iteritems():
            result ^= hash(key) ^ hash(value)
        return result

#
# Traversal of the report structure
#

class Visitor:
    def visit_analysis(self, analysis):
        pass

    def visit_warning(self, warning):
        pass

    def visit_failure(self, failure):
        pass

    def visit_info(self, info):
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

    def visit_range(self, range_):
        pass

def main():
    for filename in sorted(glob.glob('examples/example-*.xml')):
        print('%s as gcc output:' % filename)
        with open(filename) as f:
            r = Analysis.from_xml(f)
            for w in r.results:
                if isinstance(w, Issue):
                    w.write_as_gcc_output(sys.stderr)
            sys.stderr.write(str(r.to_xml()))

if __name__ == '__main__':
    main()
