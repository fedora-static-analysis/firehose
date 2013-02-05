Motivation: http://lists.fedoraproject.org/pipermail/devel/2012-December/175232.html

Mailing list: https://admin.fedoraproject.org/mailman/listinfo/firehose-devel

I want to slurp the results from static code analysis into a database,
which means coercing all of the results into some common interchange format,
codenamed "firehose" (which could also be the name of the database).

The idea is a common XML or JSON format that all tools can emit:
  * describes a warning
  * gives source-code location of the warning: filename, function,
    line number.
  * optionally with a CWE id
  * potentially with other IDs and URLs, e.g. the ID "SIG30-C" with URL
https://www.securecoding.cert.org/confluence/display/seccode/SIG30-C.+Call+only+asynchronous-safe+functions+within+signal+handlers
  * optionally describes code path to get there (potentially
    interprocedural across source files), potentially with "state"
    annotations (e.g. in the case of a reference-counting bug, it's useful
    to be able to annotate the changes to the refcount).

I'm veering towards XML because if multiple tools are going to emit this,
it's good to be able to validate things against a schema (see firehose.rng,
a RELAX-NG schema).

References to source files in the format would include a hash of the source
file itself (e.g. SHA-1) so that you can uniquely identify which source file
you were talking about.

This format would be slurped into the DB for the web UI, and can have other
things done to it without needing a server:
e.g.:
  * convert it to the textual form of a gcc compilation error, so that
    Emacs etc can parse it and take you to the source
  * be turned into a simple HTML report locally on your workstation
  * probably a python module for working with the format directly as
    objects (useful for me).
