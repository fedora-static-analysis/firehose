import unittest

import mock

from firehose.parsers import frama_c
from firehose.model import Issue, Location, File, Point, \
    Function, Message, Sut, Result, Analysis

FAKE_SUT = Sut()


class TestParseWarning(unittest.TestCase):

    @staticmethod
    def create_mock_file(lines):
        mock_file = mock.MagicMock()
        mock_file.readlines.return_value = lines
        return mock_file

    def get_file_with_warning(self):
        return self.create_mock_file(["new.c:13:[kernel] warning: Body of function foo falls-through. Adding a return statement"])

    def get_file_without_warning(self):
        return self.create_mock_file(["[kernel] Parsing perft.c (with preprocessing)"])

    def test_parse_warning(self):
        mock_file = self.get_file_with_warning()
        ret = frama_c.parse_file(mock_file)
        self.assertIsInstance(ret, Analysis)
        self.assertIsInstance(ret.results[0], Result)
        self.assertEqual(len(ret.results), 1)

    def test_paths(self):
        mock_file = self.get_file_with_warning()
        analysis = frama_c.parse_file(mock_file)
        self.assertIsInstance(analysis, Analysis)
        self.assertEqual(len(analysis.results), 1)

        results = analysis.results[0]
        self.assertIsInstance(results.location, Location)
        self.assertIsInstance(results.location.file, File)
        self.assertIsInstance(results.location.point, Point)
        self.assertEqual(results.location.function, None)
        self.assertIsInstance(results.message, Message)
        self.assertEqual(results.location.line, 13)

        self.assertEqual(
            results.message.text, "Body of function foo falls-through. Adding a return statement")
        self.assertEqual(results.location.file.givenpath, "new.c")
        self.assertEqual(results.location.file.abspath, None)

    def test_empty(self):
        mock_file = self.create_mock_file([""])
        ret = frama_c.parse_file(mock_file)
        self.assertEqual(len(ret.results), 0)

    def test_new_line(self):
        mock_file = self.create_mock_file(["\n"])
        ret = frama_c.parse_file(mock_file)
        self.assertEqual(len(ret.results), 0)

    def test_no_warning(self):
        mock_file = self.get_file_without_warning()
        ret = frama_c.parse_file(mock_file)
        self.assertEqual(len(ret.results), 0)
