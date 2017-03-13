#! /usr/bin/env python3
r"""Graphical representation of Universal Dependency trees

Usage:
  ginger [--from <format>] <in-file> [--to <format>] [<out-file>]

Arguments:
  <in-file>   input file `-` for standard input
  <out-file>  output file, `-` for standard input [default: -]

Options:
  -f, --from <format> input file format, see below [default: guess]
  -t, --to <format>   output file foramt, see below [default: ascii]
  -h, --help          Show this screen.

Input formats:
  - `guess` Try to guess the file format, defaults to CoNLL-U
  - `conllx` [CoNLL-X format](https://web.archive.org/web/20160814191537/http://ilk.uvt.nl:80/conll/)
  - `conllu` [CoNLL-U format](http://universaldependencies.org/format.html)

Output formats
  - `ascii` ASCII-art (using unicode character, because, yes, we are subversive)
  - `tikz`  TikZ code. Use the `positioning`, `calc` and `shapes.multipart` libraries

Example:
  `ginger -f conllu input.conll -t tikz output.tex`
"""

__version__ = 'ginger 0.2.1'

import sys
import contextlib
from docopt import docopt

import signal
signal.signal(signal.SIGPIPE, signal.SIG_DFL)

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
        in_str = in_stream.read()

    if arguments['--from'] == 'guess' or arguments['--from'] is None:
        tree_parser = libtreebank.formats[libtreebank.guess(in_str)]

    treebank = [tree_parser(tree) for tree in in_str.split('\n\n') if not tree.isspace()]

    if arguments['--to'] == 'tikz':
        out_str = '\n\n'.join(t.tikz() for t in treebank)
    else:  # elif arguments['--to'] == 'ascii':
        out_str = '\n\n'.join(t.ascii_art() for t in treebank)

    with smart_open(arguments['<out-file>'], 'w') as out_stream:
        out_stream.write(out_str)


if __name__ == '__main__':
    main_entry_point()
