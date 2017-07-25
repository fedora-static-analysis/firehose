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

# Parser for the output of
#   cov-format-errors --json-output-v2=<filename>

import json
from pprint import pprint

from firehose.model import Message, Function, Point, Range, \
    File, Location, Generator, Metadata, Analysis, Issue, Sut, Trace, \
    State, Notes, CustomFields

def parse_json_v2(path):
    """
    Given a JSON file emitted by:
      cov-format-errors --json-output-v2=<filename>
    parse it and return an Analysis instance
    """
    with open(path) as f:
        js = json.load(f)
    if 0:
        pprint(js)

    generator = Generator(name='coverity')
    metadata = Metadata(generator, sut=None, file_=None, stats=None)
    analysis = Analysis(metadata, [])

    for issue in js['issues']:
        if 0:
            pprint(issue)

        cwe = None

        # Use checkerName (e.g. "RESOURCE_LEAK") for
        # the testid:
        testid = issue['checkerName']

        # Use the eventDescription of the final event for the message:
        message = Message(text=issue['events'][-1]['eventDescription'])

        location = Location(file=File(givenpath=issue['mainEventFilePathname'],
                                      abspath=None),

                            function=Function(name=issue['functionDisplayName']),

                            point=Point(int(issue['mainEventLineNumber']),
                                        int(0)))

        notes = None

        trace = make_trace(issue)

        customfields = CustomFields()
        for key in ['mergeKey', 'subcategory', 'domain']:
            if key in issue:
                customfields[key] = issue[key]

        issue = Issue(cwe, testid,
                      location, message, notes, trace,
                      customfields=customfields)

        analysis.results.append(issue)

    return analysis

def make_state(event):
    """
    Construct a State instance from an event within the JSON
    """
    loc = Location(file=File(givenpath=event['filePathname'],
                             abspath=None),
                   function=None,
                   point=Point(int(event['lineNumber']),
                               int(0)))
    notes = Notes(text=event['eventDescription'])
    return State(loc, notes)

def make_trace(issue):
    """
    Construct a Trace instance from an issue within the JSON
    """
    trace = Trace([])
    for event in issue['events']:
        trace.add_state(make_state(event))
    return trace
