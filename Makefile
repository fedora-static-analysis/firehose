all: validate dump unittests executables

validate:
	xmllint --relaxng firehose.rng --noout examples/example-*.xml

dump:
	python firehose/report.py

unittests:
	python -m unittest discover -v

executables:
	PYTHONPATH=. \
	  python firehose/parsers/cppcheck.py \
	    tests/parsers/example-output/cppcheck-xml-v2/example-001.xml
	PYTHONPATH=. \
	  python firehose/parsers/clanganalyzer.py \
	    tests/parsers/example-output/clanganalyzer/report-001.plist
