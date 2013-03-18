#   Copyright 2013 David Malcolm <dmalcolm@redhat.com>
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

all: validate dump unittests executables

validate:
	xmllint --relaxng firehose.rng --noout examples/example-*.xml

dump:
	python firehose/model.py

unittests:
	python -m unittest discover -v

executables:
	PYTHONPATH=. \
	  python firehose/parsers/cppcheck.py \
	    tests/parsers/example-output/cppcheck-xml-v2/example-001.xml
	PYTHONPATH=. \
	  python firehose/parsers/clanganalyzer.py \
	    tests/parsers/example-output/clanganalyzer/report-001.plist
