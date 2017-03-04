#! /usr/bin/env python3
r"""ASCII-art representation of Universal Dependency trees

Usage:
  ginger <in-file> [<out-file>]

Arguments:
  <in-file>   input file (in CoNLL-U format), `-` for standard input
  <out-file>  output file, `-` standard input [default: -]

Options:
  -h, --help  Show this screen.

Example:
  `ginger input.conll output.ascii_art`
"""

__version__ = 'ginger 0.0.1'

import sys
import contextlib
from docopt import docopt

try:
    from . import libginger
except SystemError:  # Allow running without installing
    import libginger


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

    conll_trees = conll_str.strip().split('\n\n')

    out_str = '\n\n'.join(libginger.Tree.from_conll(t).ascii_art() for t in conll_trees)

    with smart_open(arguments['<out-file>'], 'w') as out_stream:
        out_stream.write(out_str)


if __name__ == '__main__':
    main_entry_point()
