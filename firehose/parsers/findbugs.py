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
#   Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
#   02110-1301 USA

import re
import sys
import xml.etree.ElementTree as ET

from firehose.model import Message, Function, Point, \
    File, Location, Metadata, Generator, Issue, Analysis

DEBUG=False

# Parser for xml output from findbugs

def parse_file(data_file_obj, findbugs_version=None, sut=None, file_=None,
        stats=None):
    """
    :param data_file_obj:       file object containing findbugs scan result
                                in xml format, it can be generated using 
                                command:
                                fb analyze -xml:withMessages [jar_file]
    :type  data_file_obj:       file object
    :param findbugs_version:    version of findbugs
    :type  findbugs_version:    str

    :return:    Analysis instance
    """
    generator = Generator(name = "findbugs",
            version = findbugs_version)
    metadata = Metadata(generator, sut, file_, stats)
    analysis = Analysis(metadata, [])

    def parse_BugInstance(bugInstance):
        message = Message(bugInstance.find("LongMessage").text)
        # findbugs has no column information
        sourceLine = bugInstance.find("SourceLine")
        point = Point(int(sourceLine.get("start")), 0)
        path = sourceLine.get("sourcepath")
        path = File(path, None)
        method = bugInstance.find("Method")
        if method:
            function = method.find("Message").text
            tmpIndex = function.rfind("In method ") + len("In method ") - 1
            function = Function(function[tmpIndex+1:])
        else:
            function = None
        location = Location(path, function, point)
        if DEBUG:
            print(str(location)+" "+str(message))
        return Issue(None, None, location, message, None, None)

    tree = ET.parse(data_file_obj)
    root = tree.getroot()
    for bugInstance in root.findall("BugInstance"):
        issue=parse_BugInstance(bugInstance)
        if issue:
            analysis.results.append(issue)
        else:
            sys.stderr.write("fail to pass bugInstance=[%s]\n" %
                    str(bugInstance))
    return analysis
 
if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.stdout.write("Usage: %s [findbugs result files]\n" % 
                sys.argv[0])
    else:
        analysis = parse_file(open(sys.argv[1],"r"))
        sys.stdout.write(str(analysis.to_xml()))
        sys.stdout.write('\n')
