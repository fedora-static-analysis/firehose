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

import unittest
import os

from firehose.parsers import findbugs# import parse_warning, parse_file
from firehose.model import Analysis, Issue, Location, File, Point, \
    Function, Message, Sut, Metadata, Generator

FAKE_SUT = Sut()

'''
Testcases for Parse_line:
H C NP: Null pointer dereference of o in Main.main(String[])  Dereferenced at Main.java:[line 12]
H C NP: Null pointer dereference of l1_l2_so in l1.l2.Main.<static initializer for Main>()  Dereferenced at Main.java:[line 7]
'''
testdata_jformatstring=r'''M B FS: Format string should use %n rather than \n in edu.umd.cs.findbugs.formatStringChecker.FormatterRuntimeTest.testShouldWork()  At FormatterRuntimeTest.java:[line 21]
M B FS: Format string should use %n rather than \n in edu.umd.cs.findbugs.formatStringChecker.FormatterRuntimeTest.testShouldWork()  At FormatterRuntimeTest.java:[line 22]
H C FS: Argument of type String can't be handled by format specifier %d in edu.umd.cs.findbugs.formatStringChecker.FormatterRuntimeTest.testStringWhereIntegerExpected()  At FormatterRuntimeTest.java:[line 28]
H C FS: format string "%s" needs argument 2 but only 1 are provided in edu.umd.cs.findbugs.formatStringChecker.FormatterRuntimeTest.testNotEnoughParameters()  At FormatterRuntimeTest.java:[line 36]
H C USELESS_STRING: Argument of type int[] formatted in useless way in edu.umd.cs.findbugs.formatStringChecker.FormatterRuntimeTest.testPassingAnArray()  At FormatterRuntimeTest.java:[line 43]
H D FS: Non-Boolean argument formatted using %b format specifier in edu.umd.cs.findbugs.formatStringChecker.FormatterRuntimeTest.testPassingAnIntToABoolean()  At FormatterRuntimeTest.java:[line 47]
H C FS: Illegal format string "%Y" in edu.umd.cs.findbugs.formatStringChecker.FormatterRuntimeTest.testFormatDateWithY()  At FormatterRuntimeTest.java:[line 52]
H C FS: No previous argument for format string argument to String.format(String, Object[]) in edu.umd.cs.findbugs.formatStringChecker.FormatterRuntimeTest.testBug1874856TruePositive()  At FormatterRuntimeTest.java:[line 78]
M B FS: Format string should use %n rather than \n in edu.umd.cs.findbugs.formatStringChecker.FormatterRuntimeTest.testDateMismatch()  At FormatterRuntimeTest.java:[line 88]
H C FS: Argument of type String can't be handled by format specifier %tY in edu.umd.cs.findbugs.formatStringChecker.FormatterRuntimeTest.testDateMismatch()  At FormatterRuntimeTest.java:[line 88]
H C RV: return value of String.format(String, Object[]) ignored in edu.umd.cs.findbugs.formatStringChecker.FormatterRuntimeTest.testShouldWork()  At FormatterRuntimeTest.java:[line 19]
M C RV: return value of String.format(String, Object[]) ignored in edu.umd.cs.findbugs.formatStringChecker.FormatterRuntimeTest.testStringWhereIntegerExpected()  At FormatterRuntimeTest.java:[line 28]
M C RV: return value of String.format(String, Object[]) ignored in edu.umd.cs.findbugs.formatStringChecker.FormatterRuntimeTest.testNotEnoughParameters()  At FormatterRuntimeTest.java:[line 36]
M C RV: return value of String.format(String, Object[]) ignored in edu.umd.cs.findbugs.formatStringChecker.FormatterRuntimeTest.testFormatDateWithY()  At FormatterRuntimeTest.java:[line 52]
H D DLS: Dead store to c in edu.umd.cs.findbugs.formatStringChecker.FormatterCompileTimeTest.testBug1874856FalsePositive()  At FormatterCompileTimeTest.java:[line 66]
H D DLS: Dead store to c in edu.umd.cs.findbugs.formatStringChecker.FormatterCompileTimeTest.testBug1874856TruePositive()  At FormatterCompileTimeTest.java:[line 89]'''
testdata_jformatstring_array=testdata_jformatstring.split('\n')
testdata_jformatstring_answer=[
        [21, 'testShouldWork()', 'edu/umd/cs/findbugs/formatStringChecker/FormatterRuntimeTest.java', 'M B FS: Format string should use %n rather than \\n'],
        [22, 'testShouldWork()', 'edu/umd/cs/findbugs/formatStringChecker/FormatterRuntimeTest.java', 'M B FS: Format string should use %n rather than \\n'],
        [28, 'testStringWhereIntegerExpected()', 'edu/umd/cs/findbugs/formatStringChecker/FormatterRuntimeTest.java', 'H C FS: Argument of type String can\'t be handled by format specifier %d'],
        [36, 'testNotEnoughParameters()', 'edu/umd/cs/findbugs/formatStringChecker/FormatterRuntimeTest.java', 'H C FS: format string "%s" needs argument 2 but only 1 are provided'],
        [43, 'testPassingAnArray()', 'edu/umd/cs/findbugs/formatStringChecker/FormatterRuntimeTest.java', 'H C USELESS_STRING: Argument of type int[] formatted in useless way'],
        [47, 'testPassingAnIntToABoolean()', 'edu/umd/cs/findbugs/formatStringChecker/FormatterRuntimeTest.java', 'H D FS: Non-Boolean argument formatted using %b format specifier'],
        [52, 'testFormatDateWithY()', 'edu/umd/cs/findbugs/formatStringChecker/FormatterRuntimeTest.java', 'H C FS: Illegal format string "%Y"'],
        [78, 'testBug1874856TruePositive()', 'edu/umd/cs/findbugs/formatStringChecker/FormatterRuntimeTest.java', 'H C FS: No previous argument for format string argument to String.format(String, Object[])'],
        [88, 'testDateMismatch()', 'edu/umd/cs/findbugs/formatStringChecker/FormatterRuntimeTest.java', 'M B FS: Format string should use %n rather than \\n'],
        [88, 'testDateMismatch()', 'edu/umd/cs/findbugs/formatStringChecker/FormatterRuntimeTest.java', 'H C FS: Argument of type String can\'t be handled by format specifier %tY'],
        [19, 'testShouldWork()', 'edu/umd/cs/findbugs/formatStringChecker/FormatterRuntimeTest.java', 'H C RV: return value of String.format(String, Object[]) ignored'],
        [28, 'testStringWhereIntegerExpected()', 'edu/umd/cs/findbugs/formatStringChecker/FormatterRuntimeTest.java', 'M C RV: return value of String.format(String, Object[]) ignored'],
        [36, 'testNotEnoughParameters()', 'edu/umd/cs/findbugs/formatStringChecker/FormatterRuntimeTest.java', 'M C RV: return value of String.format(String, Object[]) ignored'],
        [52, 'testFormatDateWithY()', 'edu/umd/cs/findbugs/formatStringChecker/FormatterRuntimeTest.java', 'M C RV: return value of String.format(String, Object[]) ignored'],
        [66, 'testBug1874856FalsePositive()', 'edu/umd/cs/findbugs/formatStringChecker/FormatterCompileTimeTest.java', 'H D DLS: Dead store to c'],
        [89, 'testBug1874856TruePositive()', 'edu/umd/cs/findbugs/formatStringChecker/FormatterCompileTimeTest.java', 'H D DLS: Dead store to c'],
        ]
class TestParseLine(unittest.TestCase):
    def test_empty(self):
        ret = findbugs.parse_line('')
        self.assertTrue(ret is None)

    def test_new_line(self):
        ret = findbugs.parse_line('\n')
        self.assertTrue(ret is None)

    def test_no_class_path(self):
        ret = findbugs.parse_line('H C NP: Null pointer dereference of o in Main.main(String[])  Dereferenced at Main.java:[line 12]')
        self.assertIsInstance(ret, Issue)

        self.assertIsInstance(ret.location, Location)
        self.assertEqual(ret.location.line, 12)

        self.assertIsInstance(ret.location.function, Function)
        self.assertEqual(ret.location.function.name, "main(String[])")

        self.assertIsInstance(ret.location.file, File)
        self.assertEqual(ret.location.file.givenpath, "Main.java")

        self.assertIsInstance(ret.message, Message)
        self.assertEqual(ret.message.text, "H C NP: Null pointer dereference of o")

    def test_static_initializer_and_multi_level_classpath(self):
        ret = findbugs.parse_line('H C NP: Null pointer dereference of l1_l2_so in l1.l2.Main.<static initializer for Main>()  Dereferenced at Main.java:[line 7]')
        self.assertIsInstance(ret, Issue)

        self.assertIsInstance(ret.location, Location)
        self.assertEqual(ret.location.line, 7)

        self.assertIsInstance(ret.location.function, Function)
        self.assertEqual(ret.location.function.name, "<static initializer for Main>()")

        self.assertIsInstance(ret.location.file, File)
        self.assertEqual(ret.location.file.givenpath, "l1/l2/Main.java")

        self.assertIsInstance(ret.message, Message)
        self.assertEqual(ret.message.text, "H C NP: Null pointer dereference of l1_l2_so")

    def test_testdata_jformatstring(self):
        for i in range(0,len(testdata_jformatstring_answer)):
            ret = findbugs.parse_line(testdata_jformatstring_array[i])
            #print testdata_jformatstring_array[i]
            #print ret
            self.assertIsInstance(ret, Issue)

            self.assertIsInstance(ret.location, Location)
            #print ret.location.line, testdata_jformatstring_answer[i][0]
            self.assertEqual(ret.location.line, testdata_jformatstring_answer[i][0])

            self.assertIsInstance(ret.location.function, Function)
            #print ret.location.function.name, testdata_jformatstring_answer[i][1]
            self.assertEqual(ret.location.function.name, testdata_jformatstring_answer[i][1])

            self.assertIsInstance(ret.location.file, File)
            #print ret.location.file.givenpath, testdata_jformatstring_answer[i][2]
            self.assertEqual(ret.location.file.givenpath, testdata_jformatstring_answer[i][2])

            self.assertIsInstance(ret.message, Message)
            #print ret.message.text, testdata_jformatstring_answer[i][3]
            self.assertEqual(ret.message.text, testdata_jformatstring_answer[i][3])


class TestParseFile(unittest.TestCase):
    def test_testdata_jformatstring(self):
        path=os.path.join(os.path.dirname(__file__),'example-output','findbugs','findbugs_jformatstring.txt')
        analysis=findbugs.parse_file(path)
        self.assertIsInstance(analysis, Analysis)
        self.assertNotEqual(analysis.results, None)
        self.assertEqual(len(analysis.results), len(testdata_jformatstring_answer))
        for i in range(0,len(analysis.results)):
            ret = analysis.results[i] 
            #print testdata_jformatstring_array[i]
            #print ret
            self.assertIsInstance(ret, Issue)

            self.assertIsInstance(ret.location, Location)
            #print ret.location.line, testdata_jformatstring_answer[i][0]
            self.assertEqual(ret.location.line, testdata_jformatstring_answer[i][0])

            self.assertIsInstance(ret.location.function, Function)
            #print ret.location.function.name, testdata_jformatstring_answer[i][1]
            self.assertEqual(ret.location.function.name, testdata_jformatstring_answer[i][1])

            self.assertIsInstance(ret.location.file, File)
            #print ret.location.file.givenpath, testdata_jformatstring_answer[i][2]
            self.assertEqual(ret.location.file.givenpath, testdata_jformatstring_answer[i][2])

            self.assertIsInstance(ret.message, Message)
            #print ret.message.text, testdata_jformatstring_answer[i][3]
            self.assertEqual(ret.message.text, testdata_jformatstring_answer[i][3])

