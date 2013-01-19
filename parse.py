#!/usr/bin/env python

import re
from cStringIO import StringIO

import firehose


# column is optional
GCC_PATTERN = re.compile("^(?P<path>.+?):(?P<line>\d+):(?P<column>\d*):? (?P<type>warning|note): (?P<message>.*) \[(?P<switch>\-\S+)\]$")

FUNCTION_PATTERN = re.compile(".*: In (?:member )?function '(?P<func>.*)':")


def parse_file(data_file):
    """
    looks for groups of lines that start with a line identifying a function
    name, followed by one or more lines with a warning or note

    :param data_file:   file object containing build log
    :type  data_file:   file
    """
    # has a value only when in a block of lines where the first line identifies
    # a function and is followed by 0 or more warning lines
    current_func_name = None
    for line in data_file.readlines():
        match_func = FUNCTION_PATTERN.match(line)
        if match_func:
            current_func_name = match_func.group('func')
        elif current_func_name is not None:
            report = parse_warning(line, current_func_name)
            if report:
                print_report_xml(report)
            else:
                # reset this when we run out of warnings associated with it
                current_func_name = None
                
            
def parse_warning(line, func_name):
    """
    :param line:        current line read from file
    :type  line:        basestring
    :param func_name:   name of the current function
    :type  func_name:   basestring

    :return:    firehose.Report if match, else None
    """
    match = GCC_PATTERN.match(line)
    if match:
        message = firehose.Message(match.group('message'))
        func = firehose.Function(func_name)
        point = firehose.Point(int(match.group('line')), int(match.group('column')))
        path = firehose.File(match.group('path'))
        location = firehose.Location(path, func, point)

        return firehose.Report(None, location, message, None, None)


################## begin debug crap ##################


def print_report_gcc(report):
    buf= StringIO()
    report.write_as_gcc_output(buf)
    print buf.getvalue()


def print_match(match):
    print '################'
    print match.group('path')
    print match.group('line')
    print match.group('column')
    print match.group('type')
    print match.group('message')


def print_report_xml(report):
    buf= StringIO()
    report.to_xml().write(buf)
    print buf.getvalue()


if __name__ == '__main__':
    with open('build.log') as data_file:
        parse_file(data_file)
