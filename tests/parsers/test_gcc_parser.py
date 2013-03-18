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

import unittest

import mock

from firehose.parsers import gcc # import parse_warning, parse_file
from firehose.model import Analysis, Issue, Location, File, Point, \
    Function, Message, Sut, Metadata, Generator

FUNC_NAME = 'I am a func name'

FAKE_SUT = Sut()

class TestParseWarning(unittest.TestCase):
    def test_empty(self):
        ret = gcc.parse_warning('', FUNC_NAME)
        self.assertTrue(ret is None)

    def test_new_line(self):
        ret = gcc.parse_warning('\n', FUNC_NAME)
        self.assertTrue(ret is None)

    def test_parse_c(self):
        line = "unix/arlib.c:299:9: warning: ignoring return value of 'fread', declared with attribute warn_unused_result [-Wunused-result]"
        ret = gcc.parse_warning(line, FUNC_NAME)
        self.assertIsInstance(ret, Issue)

    def test_no_metadata(self):
        line = "unix/arlib.c:299:9: warning: ignoring return value of 'fread', declared with attribute warn_unused_result [-Wunused-result]"
        ret = gcc.parse_warning(line, FUNC_NAME)
        self.assertIsInstance(ret, Issue)

    def test_parse_cpp(self):
        line = "num_get_float.cpp:535:29: warning: dereferencing type-punned pointer will break strict-aliasing rules [-Wstrict-aliasing]"
        ret = gcc.parse_warning(line, FUNC_NAME)
        self.assertIsInstance(ret, Issue)

    def test_empty_col(self):
        line = "webkit/glue/webkitclient_impl.cc:411: warning: 'current_mem_usage' may be used uninitialized in this function"
        ret = gcc.parse_warning(line, FUNC_NAME)
        self.assertIsInstance(ret, Issue)
        self.assertEqual(ret.location.column, 0)
        self.assertEqual(ret.location.line, 411)

    def test_values_c(self):
        line = "unix/arlib.c:299:9: warning: ignoring return value of 'fread', declared with attribute warn_unused_result [-Wunused-result]"
        issue = gcc.parse_warning(line, FUNC_NAME)

        # Verify the metadata:
        self.assertEqual(issue.cwe, None)
        self.assertEqual(issue.testid, 'unused-result')
        self.assertIsInstance(issue.location, Location)
        self.assertIsInstance(issue.location.file, File)
        self.assertIsInstance(issue.location.point, Point)
        self.assertIsInstance(issue.location.function, Function)
        self.assertIsInstance(issue.message, Message)
        self.assertEqual(issue.message.text,
            "ignoring return value of 'fread', declared with attribute warn_unused_result")
        self.assertEqual(issue.location.file.givenpath, "unix/arlib.c")
        self.assertEqual(issue.location.file.abspath, None)
        self.assertEqual(issue.location.point.line, 299)
        self.assertEqual(issue.location.point.column, 9)
        self.assertEqual(issue.location.function.name, FUNC_NAME)

    def test_values_cpp(self):
        line = "num_get_float.cpp:535:29: warning: dereferencing type-punned pointer will break strict-aliasing rules [-Wstrict-aliasing]"
        issue = gcc.parse_warning(line, FUNC_NAME)

        self.assertIsInstance(issue.location, Location)
        self.assertIsInstance(issue.location.file, File)
        self.assertIsInstance(issue.location.point, Point)
        self.assertIsInstance(issue.location.function, Function)
        self.assertIsInstance(issue.message, Message)
        self.assertEqual(issue.message.text,
            "dereferencing type-punned pointer will break strict-aliasing rules")
        self.assertEqual(issue.location.file.givenpath, "num_get_float.cpp")
        self.assertEqual(issue.location.file.abspath, None)
        self.assertEqual(issue.location.point.line, 535)
        self.assertEqual(issue.location.point.column, 29)
        self.assertEqual(issue.location.function.name, FUNC_NAME)

    def test_full_path(self):
        line = "/builddir/build/BUILD/libreoffice-3.5.7.2/icc/unxlngi6.pro/misc/build/SampleICC-1.3.2/IccProfLib/IccMpeACS.cpp:203:40: warning: comparison between signed and unsigned integer expressions [-Wsign-compare]"
        issue = gcc.parse_warning(line, FUNC_NAME)

        self.assertEqual(issue.location.file.givenpath,
            "/builddir/build/BUILD/libreoffice-3.5.7.2/icc/unxlngi6.pro/misc/build/SampleICC-1.3.2/IccProfLib/IccMpeACS.cpp")
        self.assertEqual(issue.location.file.abspath, None)

    def test_ignore_zip_warning(self):
        line = "        zip warning: ../../unxlngi6.pro/bin/autotextuser.zip not found or empty"
        issue = gcc.parse_warning(line, FUNC_NAME)
        self.assertTrue(issue is None)

    def test_ignore_java_warning(self):
        line = "    [javac] /builddir/build/BUILD/libreoffice-3.5.7.2/hsqldb/unxlngi6.pro/misc/build/hsqldb/build/build.xml:139: warning: 'includeantruntime' was not set, defaulting to build.sysclasspath=last; set to false for repeatable builds"
        issue = gcc.parse_warning(line, FUNC_NAME)
        self.assertTrue(issue is None)

    def test_parse_no_switch(self):
        line = "unix/arlib.c:299:9: warning: ignoring return value of 'fread', declared with attribute warn_unused_result"
        issue = gcc.parse_warning(line, FUNC_NAME)
        self.assertIsInstance(issue, Issue)


class TestParseFile(unittest.TestCase):
    @staticmethod
    def create_mock_file(lines):
        mock_file = mock.MagicMock()
        mock_file.readlines.return_value = lines
        return mock_file

    @mock.patch.object(gcc, 'parse_warning')
    def test_identify_c(self, mock_parse_warning):
        lines = self.create_mock_file(["unix/arlib.c: In function 'ar_scan':", "ignored by mock"])
        analysis = gcc.parse_file(lines, '4.7.2')
        self.assertEqual(len(analysis.results), 1)
        self.assertEqual(analysis.results[0],
                         mock_parse_warning.return_value)
        self.assertEqual(mock_parse_warning.call_args[0][1], "ar_scan")

    @mock.patch.object(gcc, 'parse_warning')
    def test_identify_cpp(self, mock_parse_warning):
        lines = self.create_mock_file(
            ["/builddir/build/BUILD/libreoffice-3.5.7.2/icc/unxlngi6.pro/misc/build/SampleICC-1.3.2/IccProfLib/IccMpeACS.cpp: In member function 'virtual bool CIccMpeAcs::Read(icUInt32Number, CIccIO*)':",
            "ignored by mock"])
        analysis = gcc.parse_file(lines, '4.7.2')
        self.assertEqual(len(analysis.results), 1)
        self.assertEqual(analysis.results[0],
                         mock_parse_warning.return_value)
        self.assertEqual(mock_parse_warning.call_args[0][1], "virtual bool CIccMpeAcs::Read(icUInt32Number, CIccIO*)")

    @mock.patch.object(gcc, 'parse_warning')
    def test_identify_global(self, mock_parse_warning):
        lines = self.create_mock_file(
            ["/builddir/build/BUILD/libreoffice-3.5.7.2/icc/unxlngi6.pro/misc/build/SampleICC-1.3.2/IccProfLib/IccMpeACS.cpp: At global scope:",
            "ignored by mock"])
        analysis = gcc.parse_file(lines, '4.7.2')
        self.assertEqual(len(analysis.results), 1)
        self.assertEqual(analysis.results[0],
                         mock_parse_warning.return_value)
        self.assertEqual(mock_parse_warning.call_args[0][1], gcc.GLOBAL_FUNC_NAME)

    @mock.patch.object(gcc, 'parse_warning')
    def test_multiple_warnings_per_func(self, mock_parse_warning):
        # we expect that upon reaching "None", it will stop looking for
        # warnings, and thus the last MagicMock won't be counted
        mock_parse_warning.side_effect = [mock.MagicMock(), mock.MagicMock(), None, mock.MagicMock()]
        lines = self.create_mock_file(["unix/arlib.c: In function 'ar_scan':", "", "", "", ""])
        analysis = gcc.parse_file(lines, '4.7.2')
        self.assertEqual(len(analysis.results), 2)
    

# This represents a variety of cases that we should handle.
#
# For the first warning (on line 3), there was no function name given, so do
# we make the function name optional?
"""
In file included from /builddir/build/BUILD/libreoffice-3.5.7.2/icc/unxlngi6.pro/misc/build/SampleICC-1.3.2/IccProfLib/IccMpeACS.h:83:0,
                 from /builddir/build/BUILD/libreoffice-3.5.7.2/icc/unxlngi6.pro/misc/build/SampleICC-1.3.2/IccProfLib/IccMpeACS.cpp:86:
/builddir/build/BUILD/libreoffice-3.5.7.2/icc/unxlngi6.pro/misc/build/SampleICC-1.3.2/IccProfLib/IccTagMPE.h:212:16: warning: unused parameter 'nIterp' [-Wunused-parameter]
/builddir/build/BUILD/libreoffice-3.5.7.2/icc/unxlngi6.pro/misc/build/SampleICC-1.3.2/IccProfLib/IccTagMPE.h:212:16: warning: unused parameter 'pMPE' [-Wunused-parameter]
/builddir/build/BUILD/libreoffice-3.5.7.2/icc/unxlngi6.pro/misc/build/SampleICC-1.3.2/IccProfLib/IccTagMPE.h:213:16: warning: unused parameter 'pDestPixel' [-Wunused-parameter]
/builddir/build/BUILD/libreoffice-3.5.7.2/icc/unxlngi6.pro/misc/build/SampleICC-1.3.2/IccProfLib/IccTagMPE.h:213:16: warning: unused parameter 'pSrcPixel' [-Wunused-parameter]
/builddir/build/BUILD/libreoffice-3.5.7.2/icc/unxlngi6.pro/misc/build/SampleICC-1.3.2/IccProfLib/IccMpeACS.cpp: In member function 'virtual bool CIccMpeAcs::Read(icUInt32Number, CIccIO*)':
/builddir/build/BUILD/libreoffice-3.5.7.2/icc/unxlngi6.pro/misc/build/SampleICC-1.3.2/IccProfLib/IccMpeACS.cpp:203:40: warning: comparison between signed and unsigned integer expressions [-Wsign-compare]
/builddir/build/BUILD/libreoffice-3.5.7.2/icc/unxlngi6.pro/misc/build/SampleICC-1.3.2/IccProfLib/IccMpeACS.cpp: At global scope:
/builddir/build/BUILD/libreoffice-3.5.7.2/icc/unxlngi6.pro/misc/build/SampleICC-1.3.2/IccProfLib/IccMpeACS.cpp:260:6: warning: unused parameter 'nInterp' [-Wunused-parameter]
/builddir/build/BUILD/libreoffice-3.5.7.2/icc/unxlngi6.pro/misc/build/SampleICC-1.3.2/IccProfLib/IccMpeACS.cpp:260:6: warning: unused parameter 'pMPE' [-Wunused-parameter]
"""

