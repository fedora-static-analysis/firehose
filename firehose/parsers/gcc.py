#!/usr/bin/env python

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

import re
import sys

from firehose.model import Message, Function, Point, \
    File, Location, Metadata, Generator, Issue, Analysis

# Parser for warnings emitted by GCC
# The code that generates these warnings can be seen within gcc's own
# sources within:
#   gcc/diagnostic.c
#   gcc/langhooks.c: lhd_print_error_function
# (as of gcc-4.7.2)
# See e.g.:
#   http://gcc.gnu.org/viewcvs/trunk/gcc/diagnostic.c?revision=195098&view=markup
#   http://gcc.gnu.org/viewcvs/trunk/gcc/langhooks.c?revision=195098&view=markup
# This parser is only intended to be run with the C locale

# column is optional
# switch is optional
GCC_PATTERN = re.compile("^(?P<path>\S.*?):(?P<line>\d+):(?P<column>\d*):? (?P<type>warning|note): (?P<message>.*?)(?P<switch> \[\-W.+\])?$")

SWITCH_SUB_PATTERN = re.compile("^ \[\-W(?P<name>.*)\]$")

# single quotes may not match locales that are not C
FUNCTION_PATTERN = re.compile(".*: In (?:member )?function '(?P<func>.*)':")

# match when gcc issues a warning for a location it thinks is in global scope
GLOBAL_PATTERN = re.compile(".*: At global scope:$")

# When gcc issues a warning at spot it thinks is in global scope, use this
# as the function name
GLOBAL_FUNC_NAME = '::'


def parse_file(data_file, gccversion=None, sut=None, file_=None, stats=None):
    """
    looks for groups of lines that start with a line identifying a function
    name, followed by one or more lines with a warning or note

    :param data_file:   file object containing build log
    :type  data_file:   file
    :param gccversion:   version of GCC that generated this report
    :type  gccversion:   str

    :return:    Analysis instance
    """
    # has a value only when in a block of lines where the first line identifies
    # a function and is followed by 0 or more warning lines

    generator = Generator(name='gcc',
                          version=gccversion)
    metadata = Metadata(generator, sut, file_, stats)
    analysis = Analysis(metadata, [])

    current_func_name = None
    for line in data_file.readlines():
        match_func = FUNCTION_PATTERN.match(line)
        match_global = GLOBAL_PATTERN.match(line)
        # if we found a line that describes a function name
        if match_func:
            current_func_name = match_func.group('func')
        elif match_global:
            current_func_name = GLOBAL_FUNC_NAME

        # if we think the next line might describe a warning
        elif current_func_name is not None:
            issue = parse_warning(line, current_func_name)
            if issue:
                analysis.results.append(issue)
            else:
                # reset this when we run out of warnings associated with it
                current_func_name = None
    return analysis
                
            
def parse_warning(line, func_name):
    """
    :param line:        current line read from file
    :type  line:        basestring
    :param func_name:   name of the current function
    :type  func_name:   basestring
    :param gccversion:   version of GCC that generated this report
    :type  gccversion:   str
    :param sut:   metadata about the software-under-test
    :type  sut:   Sut

    :return:    Issue if match, else None
    """
    match = GCC_PATTERN.match(line)
    if match:
        message = Message(match.group('message'))
        func = Function(func_name)
        try:
            column = int(match.group('column'))
        except ValueError:
            if match.group('column') == '':
                column = 0
            else:
                raise
        except TypeError:
            column = None
        switch_match = SWITCH_SUB_PATTERN.match(match.group('switch') or '')
        if switch_match:
            switch = switch_match.group('name')
        else:
            switch = None

        point = Point(int(match.group('line')), column)
        path = File(match.group('path'), None)
        location = Location(path, func, point)

        return Issue(None, switch, location, message, None, None)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("provide a build log file path as the only argument")
    else:
        with open(sys.argv[1]) as data_file:
            analysis = parse_file(data_file)
            sys.stdout.write(str(analysis.to_xml()))
            sys.stdout.write('\n')
