#!/usr/bin/env python

#   Copyright 2013 Shuxiong Ye <yeshuxiong@gmail.com>
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

import re
import sys

from firehose.model import Message, Function, Point, \
    File, Location, Metadata, Generator, Issue, Analysis

# Parser for result emitted by findbugs
# Example of findbugs' warnings:
# M C RV: return value of String.format(String, Object[]) ignored in edu.umd.cs.findbugs.formatStringChecker.FormatterRuntimeTest.testFormatDateWithY()  At FormatterRuntimeTest.java:[line 52]

# You can find bugs descriptions of findbugs here:
# http://findbugs.sourceforge.net/bugDescriptions.html

DEBUG=False

def parse_file(data_file_name, findbugs_version=None, sut=None, file_=None, stats=None):
    """
    :param data_file:           str object containing findbugs scan result
    :type  data_file:           str
    :param findbugs_version:    version of findbugs
    :type  findbugs_version:    str

    :return:    Analysis instance
    """
    data_file=open(data_file_name)
    generator = Generator(name="findbugs", version=findbugs_version)
    metadata = Metadata(generator, sut, file_, stats)
    analysis = Analysis(metadata, [])
    for line in data_file.readlines():
        issue = parse_line(line)
        if issue:
            analysis.results.append(issue)
        else:
            sys.stderr.write("fail to pass line=[%s]"%line)
    data_file.close()
    return analysis

FINDBUGS_PATTERN=re.compile(r"^(?P<bug_message>[^ ]* +[^ ]* +[^ ]*: *.*) +in +(?P<bug_path_and_function>[^\.\(\)]+(?:\.[^\.\(\)]+)*\([^\)]*\))[^\[]* +(?P<bug_file_name>[^\[ ]+):\[line +(?P<bug_line_number>\d+)\]")
PATH_AND_FUNCTION_PATTERN=re.compile(r"^(?:(?P<bug_class_path>[^\.]+(?:\.[^\.]+)*)\.){0,1}(?P<bug_class_name>[^\.]+)\.(?P<bug_function_name>[^.]+\([^\.]*\))$")

def parse_line(line):
    """
    :param line:        current line read from file
    :type  line:        str 

    :return:    Issue if match, else None
    """
    match = FINDBUGS_PATTERN.match(line)
    if match:
        if DEBUG:
            print(match.groupdict())
            print(match.groups())
        match2 = PATH_AND_FUNCTION_PATTERN.match(match.group("bug_path_and_function"))
        if match2:
            if DEBUG:
                print(match.groupdict())
                print(match.groups())
            message = Message(match.group("bug_message"))
            # findbugs has no column information
            point = Point(int(match.group("bug_line_number")), 0)
            function = Function(match2.group("bug_function_name"))
            path=match.group("bug_file_name")
            if match2.group("bug_class_path"):
                path=match2.group("bug_class_path").replace(".","/")+"/"+path
            path = File(path, None)
            location = Location(path, function, point)

            return Issue(None, None, location, message, None, None)

 
if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.stdout.write("Usage: %s [findbugs result files]\n", sys.argv[0])
    else:
        analysis = parse_file(sys.argv[1])
        sys.stdout.write(str(analysis.to_xml()))
        sys.stdout.write('\n')
