#!/usr/bin/env python

#   Copyright 2013 ShuxiongYe, yeshuxiong@gmail.com 
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

DEBUG=False

def parse_line(line):
    """
    :param line:        current line read from file
    :type  line:        str 

    :return:    Issue if match, else None
    """
    FINDBUGS_PATTERN=re.compile(r"^(?P<bug_message>[A-Z]* +[A-Z]* +[A-Z]*: *.*) +in +(?P<bug_path_and_function>[^\.\(\)]+(?:\.[^\.\(\)]+)*\([^\)]*\))[^\[]* +(?P<bug_file_name>[^\[ ]+):\[line +(?P<bug_line_number>\d+)\]")
    PATH_AND_FUNCTION_PATTERN=re.compile(r"^(?:(?P<bug_class_path>[^\.]+(?:\.[^\.]+)*)\.){0,1}(?P<bug_class_name>[^\.]+)\.(?P<bug_function_name>[^.]+\([^\.]*\))$")

    match = FINDBUGS_PATTERN.match(line)
    if match:
        if DEBUG:
            print match.groupdict()
            print match.groups()

        match2 = PATH_AND_FUNCTION_PATTERN.match(match.group("bug_path_and_function"))
        if match2:
            if DEBUG:
                print match2.groupdict()
                print match2.groups()

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
    f=open(sys.argv[1],"r")
    for line in f:
        print '------------------------'
        line=line[:-1]
        print line
        print parse_line(line)

    """
    if len(sys.argv) != 2:
        print("provide a build log file path as the only argument")
    else:
        with open(sys.argv[1]) as data_file:
            analysis = parse_file(data_file)
            sys.stdout.write(str(analysis.to_xml()))
            sys.stdout.write('\n')
    """
