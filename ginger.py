#! /usr/bin/env python3
r"""ASCII-art representation of Universal Dependency trees

Usage:
  ginger [--format <format>] <in-file> [<out-file>]

Arguments:
  <in-file>   input file `-` for standard input
  <out-file>  output file, `-` for standard input [default: -]

Options:
  -f, --format <format> input file format, see below [default: guess]
  -h, --help  Show this screen.

Formats:
  - `guess` Try to guess the file format, defaults to CoNLL-U
  - `conllx` [CoNLL-X format](https://web.archive.org/web/20160814191537/http://ilk.uvt.nl:80/conll/)
  - `conllu` [CoNLL-U format](http://universaldependencies.org/format.html)

Example:
  `ginger input.conll output.ascii_art`
"""

__version__ = 'ginger 0.0.1'

import sys
import contextlib
from docopt import docopt

try:
    import libginger
    import libtreebank
except ImportError:
    from . import libginger
    from . import libtreebank


# Thanks http://stackoverflow.com/a/17603000/760767
@contextlib.contextmanager
def smart_open(filename: str = None, mode: str = 'r', *args, **kwargs):
    if filename == '-':
        fh = sys.stdin if 'r' in mode else sys.stdout
    else:
        fh = open(filename, mode, *args, **kwargs)

    try:
        yield fh
    finally:
        try:
            fh.close()
        except AttributeError:
            pass


def main_entry_point(argv=sys.argv[1:]):
    arguments = docopt(__doc__, version=__version__, argv=argv)
    # Since there are no support for default positional arguments in
    # docopt yet. Might be useful for complex default values, too
    if arguments['<out-file>'] is None:
        arguments['<out-file>'] = '-'

    with smart_open(arguments['<in-file>']) as in_stream:
        conll_str = in_stream.read()

    if arguments['--format'] == 'guess' or arguments['--format'] is None:
        arguments['--format'] = libtreebank.guess(conll_str)

    # Conversion between formats
    conll_str = '\n'.join(libtreebank.formats[arguments['--format']](l) for l in conll_str.splitlines())
    conll_trees = conll_str.strip().split('\n\n')

    out_str = '\n\n'.join(libginger.Tree.from_conll(t).ascii_art() for t in conll_trees)

    with smart_open(arguments['<out-file>'], 'w') as out_stream:
        out_stream.write(out_str)


if __name__ == '__main__':
    main_entry_point()
