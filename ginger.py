#! /usr/bin/env python3
r"""Graphical representation of Universal Dependency trees

Usage:
  ginger [--from <format>] <in-file> [--to <format>] [<out-file>]

Arguments:
  <in-file>   input file `-` for standard input
  <out-file>  output destination, `-` for standard input [default: -]

Options:
  -f, --from <format> input file format, see below [default: guess]
  -t, --to <format>   output file foramt, see below [default: ascii]
  -h, --help          Show this screen.

Input formats:
  - `guess`      Try to guess the file format, defaults to CoNLL-U
  - `conllx`     [CoNLL-X format](https://web.archive.org/web/20160814191537/http://ilk.uvt.nl:80/conll/)
  - `conllu`     [CoNLL-U format](http://universaldependencies.org/format.html)
  - `talismane`  Outputs of [Talismane](http://redac.univ-tlse2.fr/applications/talismane/talismane_en.html)

Output formats
  - Text formats. Those can't be used without any dependency
    - `ascii`  ASCII-art (using unicode character, because, yes, we are subversive)
    - `tikz`   TikZ code. Use the `positioning`, `calc` and `shapes.multipart` libraries
  - Image formats. Uses cairo, requires dependencies and have different convenrions see README.md

Example:
  `ginger -f conllu input.conll -t tikz output.tex`
"""

__version__ = 'ginger 0.3.0'

import sys
import contextlib
from docopt import docopt

import re

import signal
signal.signal(signal.SIGPIPE, signal.SIG_DFL)

try:
    import libginger
    import libtreebank
    import libtreerender
except ImportError:
    from . import libginger
    from . import libtreebank
    from . import libtreerender


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

    treebank = [tree_parser(tree) for tree in re.split('\n\n+', in_str) if tree and not tree.isspace()]

    if arguments['--to'] in ('tikz', 'ascii'):
        if arguments['--to'] == 'tikz':
            out_str = '\n\n'.join(libtreerender.tikz(t) for t in treebank)
        elif arguments['--to'] == 'ascii':
            out_str = '\n\n'.join(libtreerender.ascii_art(t) for t in treebank)
        with smart_open(arguments['<out-file>'], 'w') as out_stream:
            out_stream.write(out_str)
    else:
        if arguments['--to'] == 'png':
            out_bytes = libtreerender.png(treebank[0])

        with smart_open(arguments['<out-file>'], 'wb') as out_stream:
            out_stream.write(out_bytes)


if __name__ == '__main__':
    main_entry_point()
