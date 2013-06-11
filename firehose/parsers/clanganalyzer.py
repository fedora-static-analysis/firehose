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

# Parser for the .plist files emitted by the clang-static-analyzer,
# when "-plist" is passed as an option to "scan-build" or "clang"

# Developed against output from clang-3.0-14.fc17

import glob
import os
import plistlib
from pprint import pprint
import sys

from firehose.model import Message, Function, Point, Range, \
    File, Location, Generator, Metadata, Analysis, Issue, Sut, Trace, \
    State, Notes

def parse_scandir(resultdir, analyzerversion=None, sut=None):
    """
    Given a path to a directory of scan-build output, parse it and
    yield Analysis instances
    """
    for filename in glob.glob(os.path.join(resultdir, 'report-*.plist')):
        yield parse_plist(filename, analyzerversion, sut)

def parse_plist(pathOrFile, analyzerversion=None, sut=None, file_=None, stats=None):
    """
    Given a .plist file emitted by clang-static-analyzer (e.g. via
    scan-build), parse it and return an Analysis instance
    """
    plist = plistlib.readPlist(pathOrFile)
    # We now have the .plist file as a hierarchy of dicts, lists, etc

    # Handy debug dump:
    if 0:
        pprint(plist)

    # A list of filenames, apparently referenced by index within
    # diagnostics:
    files = plist['files']

    generator = Generator(name='clang-analyzer',
                          version=analyzerversion)
    metadata = Metadata(generator, sut, file_, stats)
    analysis = Analysis(metadata, [])

    for diagnostic in plist['diagnostics']:
        if 0:
            pprint(diagnostic)

        cwe = None

        # TODO: we're not yet handling the following:
        #   diagnostic['category']
        #   diagnostic['type']

        message = Message(text=diagnostic['description'])

        loc = diagnostic['location']
        location = Location(file=File(givenpath=files[loc.file],
                                      abspath=None),

                            # FIXME: doesn't tell us function name
                            # TODO: can we patch this upstream?
                            function=None,

                            point=Point(int(loc.line),
                                        int(loc.col)))

        notes = None

        trace = make_trace(files, diagnostic['path'])

        issue = Issue(cwe,
                      None, # FIXME: can we get at the test id?
                      location, message, notes, trace)

        analysis.results.append(issue)

    return analysis

def make_point_from_plist_point(loc):
    # point:
    #   e.g. {'col': 2, 'file': 0, 'line': 130}
    return Point(int(loc.line),
                 int(loc.col))

def make_location_from_point(files, loc):
    # loc:
    #   e.g. {'col': 2, 'file': 0, 'line': 130}
    location = Location(file=File(givenpath=files[loc.file],
                                  abspath=None),

                        # FIXME: doesn't tell us function name
                        # TODO: can we patch this upstream?
                        function=Function(''),

                        point=make_point_from_plist_point(loc))
    return location

def make_location_from_range(files, range_):
    # range_:
    #    e.g.:
    #     [{'col': 18, 'file': 0, 'line': 165},
    #      {'col': 21, 'file': 0, 'line': 165}]
    assert len(range_) == 2
    start = range_[0]
    end = range_[1]
    assert start['file'] == end['file']

    if start == end:
        point = make_point_from_plist_point(start)
        range_ = None
    else:
        point = None
        range_ = Range(start=make_point_from_plist_point(start),
                       end=make_point_from_plist_point(end))

    location = Location(file=File(givenpath=files[start['file']],
                                  abspath=None),

                        # FIXME: doesn't tell us function name
                        # TODO: can we patch this upstream?
                        function=Function(''),

                        point=point,
                        range_=range_)

    return location

def make_trace(files, path):
    """
    Construct a Trace instance from the .plist's 'path' list
    """
    trace = Trace([])
    lastlocation = None
    for node in path:
        if 0:
            pprint(node)

        kind = node['kind']

        if kind == 'event':
            # e.g.:
            #  {'extended_message': "Value stored to 'ret' is never read",
            #   'kind': 'event',
            #   'location': {'col': 2, 'file': 0, 'line': 130},
            #   'message': "Value stored to 'ret' is never read",
            #   'ranges': [[{'col': 8, 'file': 0, 'line': 130},
            #               {'col': 29, 'file': 0, 'line': 130}]]}

            # TODO: we're not yet handling the following:
            #   node['extended_message']
            #   node['ranges']

            loc = node['location']
            location = make_location_from_point(files, loc)

            notes = Notes(node['message'])
            trace.add_state(State(location, notes))

            lastlocation = location

        elif kind == 'control':
            # e.g.:
            #  {'edges': [{'end': [{'col': 9, 'file': 0, 'line': 161},
            #                      {'col': 9, 'file': 0, 'line': 161}],
            #              'start': [{'col': 2, 'file': 0, 'line': 161},
            #                        {'col': 2, 'file': 0, 'line': 161}]}],
            #   'kind': 'control'}
            edges = node['edges']
            for edge in edges:
                edge_start = edge.start
                edge_end = edge.end

                startloc = make_location_from_range(files, edge_start)
                endloc = make_location_from_range(files, edge_end)

                if startloc != lastlocation:
                    trace.add_state(State(startloc, None))
                trace.add_state(State(endloc, None))
                lastlocation = endloc
        else:
            raise ValueError('unknown kind: %r' % kind)
    return trace

analyzerversion = 'clang-3.0-14.fc17.x86_64' # FIXME

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("provide either the path to scan-build results directory, or to that of a .plist file as the only argument")
    else:
        path = sys.argv[1]
        if path.endswith('.plist'):
            analysis = parse_plist(path, analyzerversion)
            sys.stdout.write(str(analysis.to_xml()))
            sys.stdout.write('\n')
        else:
            for analysis in parse_scandir(path, analyzerversion):
                sys.stdout.write(str(analysis.to_xml()))
                sys.stdout.write('\n')
