#! /usr/bin/env python3
r"""Format conversion and graphical representation of [Universal Dependencies](http://universaldependencies.org) trees.

Usage:
  ginger [--from <format>] <in-file> [--to <format>] [<out-file>]

Arguments:
  <in-file>   input file `-` for standard input
  <out-file>  output file, `-` for standard input [default: -]

Options:
  -f, --from <format> input file format, see below [default: guess]
  -t, --to <format>   output file format, see below [default: ascii]
  -h, --help          Show this screen.

Input formats:
  - `guess`           Try to guess the file format, defaults to CoNLL-U
  - `conllx`          [CoNLL-X format](https://web.archive.org/web/20160814191537/http://ilk.uvt.nl:80/conll/)
  - `conllu`          [CoNLL-U format](http://universaldependencies.org/format.html)
  - `conll2009_gold`  [CoNLL-2009 format](http://ufal.mff.cuni.cz/conll2009-st/task-description.html)
                      (Gold columns only)
  - `conll2009_sys`   [CoNLL-2009 format](http://ufal.mff.cuni.cz/conll2009-st/task-description.html)
                      (Predicted columns only)
  - `talismane`       Outputs of [Talismane](http://redac.univ-tlse2.fr/applications/talismane/talismane_en.html)
  - `mate_gold`       Alias for `conll2009_gold`, used by
                      [mate-tools](http://www.ims.uni-stuttgart.de/forschung/ressourcen/werkzeuge/matetools.en.html)
  - `mate_sys`        Alias for `conll2009_sys`, used by
                      [mate-tools](http://www.ims.uni-stuttgart.de/forschung/ressourcen/werkzeuge/matetools.en.html)


Output formats
  - `ascii`  ASCII-art (using Unicode characters, because, yes, we are subversive)
  - `tikz`   TikZ code. Use the `positioning`, `calc` and `shapes.multipart` libraries

Example:
  `ginger -f conllu input.conll -t tikz output.tex`
"""

__version__ = 'ginger 0.9.0.9.0.10.0'

import sys
import contextlib
import pathlib
from docopt import docopt

import signal
signal.signal(signal.SIGPIPE, signal.SIG_DFL)


import logging
logging.basicConfig(level=logging.INFO)

# Usual frobbing of packages, due to Python's insane importing policy
if __name__ == "__main__" and __package__ is None:
    from sys import path
    ginger_root = pathlib.Path(__file__).resolve().parents[1]
    path.insert(0, str(ginger_root))
    import ginger  # noqa
    __package__ = "ginger"

try:
    from . import libtreebank
    from . import libtreerender
except ImportError:
    from ginger import libtreebank
    from ginger import libtreerender


def sigint_handler(signal, frame):
        logging.error('Process interrupted by SIGINT')
        sys.exit(0)


signal.signal(signal.SIGINT, sigint_handler)


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

    with smart_open(arguments['<in-file>'], encoding='utf8') as in_stream:
        in_lst = list(in_stream.readlines())

    if arguments['--from'] == 'guess' or arguments['--from'] is None:
        arguments['--from'] = libtreebank.guess(in_lst)

    try:
        parser, _ = libtreebank.formats[arguments['--from']]
    except KeyError:
        logging.error('{argsfrom!r} is not a supported format'.format(
            argsfrom=arguments['--from']))
        sys.exit(1)

    if parser is None:
        logging.error('{argsfrom!r} is not supported as an input format'.format(
            argsfrom=arguments['--from']))
        sys.exit(1)

    treebank = parser(in_lst)

    if arguments['--to'] == 'tikz':
        out_lst = [libtreerender.tikz(t) for t in treebank]

    elif arguments['--to'] == 'ascii':
        out_lst = [libtreerender.ascii_art(t) for t in treebank]

    else:
        try:
            _, formatter = libtreebank.formats[arguments['--to']]
        except KeyError:
            logging.error('{argsto!r} is not a supported format'.format(
                argsto=arguments['--to']))
            sys.exit(1)

        if formatter is None:
            logging.error('{argsto!r} is not supported as an output format'.format(
            argsto=arguments['--to']))
            sys.exit(1)

        out_lst = [formatter(t) for t in treebank]

    with smart_open(arguments['<out-file>'], 'w', encoding='utf8') as out_stream:
        for t in out_lst[:-1]:
            out_stream.write(t)
            out_stream.write('\n\n')
        out_stream.write(out_lst[-1])
        out_stream.write('\n')


if __name__ == '__main__':
    main_entry_point()
