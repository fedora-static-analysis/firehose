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

import unittest
import os

from firehose.parsers import findbugs# import parse_warning, parse_file
from firehose.model import Analysis, Issue, Location, File, Point, \
    Function, Message, Sut, Metadata, Generator

FAKE_SUT = Sut()

def readRawData(filePath):
    f = open(filePath, "r")
    ret = f.readlines()
    f.close()
    return ret

class TestParseFile(unittest.TestCase):
    def run_testdata(self, xmlFileName, answer, isDebug=False):
        path = os.path.join(os.path.dirname(__file__), "example-output",
                "findbugs", xmlFileName)
        analysis = findbugs.parse_file(path)
        self.assertIsInstance(analysis, Analysis)
        self.assertNotEqual(analysis.results, None)
        if isDebug:
            print(len(analysis.results), len(answer))
        self.assertEqual(len(analysis.results), len(answer))
        for i in range(0, len(analysis.results)):
            ret = analysis.results[i] 
            self.assertIsInstance(ret, Issue)
            self.assertIsInstance(ret.location, Location)
            self.assertEqual(ret.location.line, answer[i][0])
            if answer[i][1]:
                self.assertIsInstance(ret.location.function, Function)
                self.assertEqual(ret.location.function.name, answer[i][1])
            else:
                self.assertEqual(ret.location.function, None)
            self.assertIsInstance(ret.location.file, File)
            self.assertEqual(ret.location.file.givenpath, answer[i][2])

    def test_testdata_jformatstring(self):
        answer = [
                [66, "edu.umd.cs.findbugs.formatStringChecker."+
                "FormatterCompileTimeTest.testBug1874856FalsePositive()",
                "edu/umd/cs/findbugs/formatStringChecker/"+
                "FormatterCompileTimeTest.java"],
                [89, "edu.umd.cs.findbugs.formatStringChecker."+
                "FormatterCompileTimeTest.testBug1874856TruePositive()",
                "edu/umd/cs/findbugs/formatStringChecker/"+
                "FormatterCompileTimeTest.java"],
                [19, "edu.umd.cs.findbugs.formatStringChecker."+
                "FormatterRuntimeTest.testShouldWork()",
                "edu/umd/cs/findbugs/formatStringChecker/"+
                "FormatterRuntimeTest.java"],
                [52, "edu.umd.cs.findbugs.formatStringChecker."+
                "FormatterRuntimeTest.testFormatDateWithY()",
                "edu/umd/cs/findbugs/formatStringChecker/"+
                "FormatterRuntimeTest.java"],
                [36, "edu.umd.cs.findbugs.formatStringChecker."+
                "FormatterRuntimeTest.testNotEnoughParameters()",
                "edu/umd/cs/findbugs/formatStringChecker/"+
                "FormatterRuntimeTest.java"],
                [28, "edu.umd.cs.findbugs.formatStringChecker."+
                "FormatterRuntimeTest.testStringWhereIntegerExpected()",
                "edu/umd/cs/findbugs/formatStringChecker/"+
                "FormatterRuntimeTest.java"],
                [88, "edu.umd.cs.findbugs.formatStringChecker."+
                "FormatterRuntimeTest.testDateMismatch()",
                "edu/umd/cs/findbugs/formatStringChecker/"+
                "FormatterRuntimeTest.java"],
                [28, "edu.umd.cs.findbugs.formatStringChecker."+
                "FormatterRuntimeTest.testStringWhereIntegerExpected()",
                "edu/umd/cs/findbugs/formatStringChecker/"+
                "FormatterRuntimeTest.java"],
                [43, "edu.umd.cs.findbugs.formatStringChecker."+
                "FormatterRuntimeTest.testPassingAnArray()",
                "edu/umd/cs/findbugs/formatStringChecker/"+
                "FormatterRuntimeTest.java"],
                [47, "edu.umd.cs.findbugs.formatStringChecker."+
                "FormatterRuntimeTest.testPassingAnIntToABoolean()",
                "edu/umd/cs/findbugs/formatStringChecker/"+
                "FormatterRuntimeTest.java"],
                [52, "edu.umd.cs.findbugs.formatStringChecker."+
                "FormatterRuntimeTest.testFormatDateWithY()",
                "edu/umd/cs/findbugs/formatStringChecker/"+
                "FormatterRuntimeTest.java"],
                [36, "edu.umd.cs.findbugs.formatStringChecker."+
                "FormatterRuntimeTest.testNotEnoughParameters()",
                "edu/umd/cs/findbugs/formatStringChecker/"+
                "FormatterRuntimeTest.java"],
                [78, "edu.umd.cs.findbugs.formatStringChecker."+
                "FormatterRuntimeTest.testBug1874856TruePositive()",
                "edu/umd/cs/findbugs/formatStringChecker/"+
                "FormatterRuntimeTest.java"],
                [88, "edu.umd.cs.findbugs.formatStringChecker."+
                "FormatterRuntimeTest.testDateMismatch()",
                "edu/umd/cs/findbugs/formatStringChecker/"+
                "FormatterRuntimeTest.java"],
                [21, "edu.umd.cs.findbugs.formatStringChecker"+
                ".FormatterRuntimeTest.testShouldWork()",
                "edu/umd/cs/findbugs/formatStringChecker/"+
                "FormatterRuntimeTest.java"],
                [22, "edu.umd.cs.findbugs.formatStringChecker."+
                "FormatterRuntimeTest.testShouldWork()",
                "edu/umd/cs/findbugs/formatStringChecker/"+
                "FormatterRuntimeTest.java"]
                ]
        self.run_testdata("findbugs_jformatstring.xml", answer)

    def test_testdata_example(self):
        answer = [
                [8, "O0.<static initializer for O0>()", "O0.java"],
                [13, "new O0()", "O0.java"],
                [18, "O0.bugs()", "O0.java"],
                [23, "O0.main(String[])", "O0.java"],
                [9, "l1.O1.<static initializer for O1>()", "l1/O1.java"],
                [14, "new l1.O1()", "l1/O1.java"],
                [19, "l1.O1.bugs()", "l1/O1.java"],
                [24, "l1.O1.main(String[])", "l1/O1.java"],
                [9, "l1.l2.O2.<static initializer for O2>()",
                    "l1/l2/O2.java"],
                [14, "new l1.l2.O2()", "l1/l2/O2.java"],
                [19, "l1.l2.O2.bugs()", "l1/l2/O2.java"],
                [24, "l1.l2.O2.main(String[])", "l1/l2/O2.java"],
                ]
        self.run_testdata("findbugs_Example.xml", answer)

    def test_testdata_no_method(self):
        answer = [
                [77, None, "com/clearspring/ircbot/trac/TracRpc.java"],
                ]
        self.run_testdata("findbugs_no_method.xml", answer)
