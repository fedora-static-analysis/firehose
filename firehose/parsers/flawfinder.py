#!/usr/bin/env python
#
#   Copyright 2017 David Carlos  <ddavidcarlos1392@gmail.com>
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

import sys
import re
from subprocess import check_output
from firehose.model import Message, Point, \
    File, Location, Generator, Metadata, Analysis, Issue


def main():
    """ Main entry to flawfinder parser """
    try:
        arg_file = sys.argv[1]
        report = open(arg_file, 'r')
    except IOError as e:
        raise e
    except IndexError:
        print("Missing input file")
    analysis = parse_file(report)
    sys.stdout.write(str(analysis.to_xml()))
    sys.stdout.write('\n')


def parse_file(infile):
    """ Parser flawfinder output

    :infile: file-like object
    :returns: Firehose Analysis object, representing the final XML.

    Flawfinder can generate multiple cwes for a single issue.
    Firehose's models does not supports multiple CWEs.
    For now, when  multiple CWEs ocurrs, we get only the first one.

    A issue was created to track this bug:
    https://github.com/fedora-static-analysis/firehose/issues/35
    """

    line = infile.readline()
    generator = Generator(name='flawfinder',
                          version=get_flawfinder_version(line))
    metadata = Metadata(generator, None, None, None)
    analysis = Analysis(metadata, [])
    issue_line_pattern = "(\.?\/?([a-z0-9]+\_?\/?\.?)+)\:([0-9]+)\:"
    issue_severity_pattern = "\[([0-9]+)\]"
    issue_testid_pattern = "\(([a-z]+)\)"
    whitespace = "\s+"

    first_line_pattern = (issue_line_pattern + whitespace +
                     issue_severity_pattern + whitespace +
                     issue_testid_pattern)
    prog = re.compile(first_line_pattern)
    while line:
        if prog.search(line) and line != "\n":
            issue_path = prog.search(line).group(1)
            issue_line = prog.search(line).group(3)
            issue_severity = prog.search(line).group(4)
            testid = prog.search(line).group(5)

            location = Location(file=File(issue_path, None),
                                function=None,
                                point=Point(int(issue_line), 0))

            message_line = infile.readline()
            issue_message = ""
            cwes = []
            while not prog.search(message_line) and message_line != "\n":
                issue_message += " " + message_line
                cwes.extend([int(cwe) for cwe in re.findall("CWE-([0-9]+)", issue_message)])
                message_line = infile.readline()

            line = message_line
            if cwes:
                first_cwe = int(cwes[0])
            else:
                first_cwe = None

            issue = Issue(first_cwe, testid, location,
                          Message(text=issue_message), notes=None,
                          trace=None, severity=issue_severity, customfields=None)

            analysis.results.append(issue)
        else:
            line = infile.readline()

    return analysis


def get_flawfinder_version(first_line):
    """Retrieve flawfinder version from report.
    :first_line: first line of the flawfinder report.
    :returns: flawfinder version.
    """

    pattern = "version\s([0-9]?.[0-9]*)"
    prog = re.compile(pattern)
    try:
        return prog.search(first_line).groups()[0]
    except IndexError:
        return None

if __name__ == '__main__':
    main()
