#!/usr/bin/env python
import re
import sys

from firehose.model import Message, Point, \
    File, Location, Metadata, Generator, Issue, Analysis

# Parser for warnings emitted by frama-c
# Frama-c allows for multiple analysis, including the following:
#
# Aorai               verification of behavioral properties (experimental)
#                     (-aorai-h)
# Callgraph           automatically compute the callgraph of the program. Using
#                     Value might improve the precision of this plug-in (-cg-h)
# Dominators          Compute postdominators of statements (-dominators-h)
# From analysis       functional dependencies (-from-h)
# Inout               operational, imperative and all kinds of inputs/outputs
#                     (-inout-h)
# Metrics             syntactic metrics (-metrics-h)
# Obfuscator          objuscator for confidential code (-obfuscator-h)
# Occurrence          automatically computes where variables are used
#                     (-occurrence-h)
# Pdg                 Program Dependence Graph (-pdg-h)
# Postdominators      computing postdominators of statements
#                     (-postdominators-h)
# Report              Properties Status Report (experimental) (-report-h)
# Rtegen              generates annotations for runtime error checking and
#                     preconditions at call sites (-rte-h)
# Scope               data dependencies higher level functions (-scope-h)
# Security-slicing    security slicing (experimental, undocumented)
#                     (-security-slicing-h)
# Semantic constant folding  propagates constants semantically (-scf-h)
# Slicing             code slicer (-slicing-h)
# Sparecode           code cleaner (-sparecode-h)
# Users               function callees (-users-h)
# Value analysis      automatically computes variation domains for the
#                     variables of the program (-value-h)
# WP                  Weakest Precondition Calculus
#                     WP 0.9 for Magnesium-20151002 (-wp-h)
#
# The example log provided in tests/parsers/example-input/sparecode.log is
# from the sparecode analysis run on a trivial C chess engine program

SPARECODE_WARNING = ("^(?P<path>\S.*?):(?P<line>\d+):(?P<module>\S.*?) (?P<type>warning|note): (?P<message>.*?)$")
FRAMA_C_SPARECODE_PATTERN = re.compile(SPARECODE_WARNING)


def parse_file(data_file, sut=None, file_=None, stats=None):
    """
    for each line, the regex for SPARECODE_WARNING is matched

    :param data_file:   file object containing build log
    :type  data_file:   file

    :return:    Analysis instance
    """

    generator = Generator(name='frama-c')
    metadata = Metadata(generator, sut, file_, stats)
    analysis = Analysis(metadata, [])

    for line in data_file.readlines():
        match_warning = FRAMA_C_SPARECODE_PATTERN.match(line)

        if match_warning:
            issue = parse_warning(match_warning)
            analysis.results.append(issue)
    return analysis


def parse_warning(match_warning):
    """
    :param match_warning:  the matched object
    :type  match_warning:  SRE_Match
    :param sut:   metadata about the software-under-test
    :type  sut:   Sut

    :return:    Issue
    """
    message = Message(match_warning.group('message'))
    point = Point(int(match_warning.group('line')), 0)
    path = File(match_warning.group('path'), None)
    location = Location(file=path, function=None, point=point)
    return Issue(
        cwe=None, testid=None, location=location, message=message, notes=None,
        trace=None)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Provide a build log file path as the only argument")
    else:
        with open(sys.argv[1]) as data_file:
            analysis = parse_file(data_file)
            sys.stdout.write(str(analysis.to_xml()))
            sys.stdout.write('\n')
