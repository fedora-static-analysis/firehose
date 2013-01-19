all: validate dump

validate:
	xmllint --relaxng firehose.rng --noout examples/example-*.xml

dump:
	python firehose/firehose.py
