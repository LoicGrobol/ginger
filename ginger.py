#! /usr/bin/env python3
r"""Format conversion and graphical representation of [Universal Dependencies](http://universaldependencies.org) trees.

Usage:
  ginger [--from <format>] <origin> [--to <format>] [<destination>]

Arguments:
  <origin>       input origin `-` for standard input
  <destination>  output destination, `-` for standard output [default: -]

See below for details on the authorized types of input and output.

Options:
  -f, --from <format>  input format, see below [default: guess]
  -t, --to <format>    output format, see below [default: ascii]
  -h, --help           Show this screen.

Input formats:
The input must be either the path to an existing file or `-` for standard input. The data that
it contains must be in one of the following formats:

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

Output formats:

  - Text formats: to use these formats, the output destination must be either a file and thus must
                  not be the path to an existing directory, or `-` for the standard output.
     - `ascii`  ASCII-art (using unicode characters, because, yes, we are subversive)
     - `tikz`   TikZ code. Use the `positioning`, `calc` and `shapes.multipart` tikz libraries
  - Image formats: these require the installation of the cairo dependencies. Additionally, the
                   output destination must be either a directory and thus must not be the path of
                   an existing file, or `-` for the standard output, in which case the byte streams
                   corresponding to different trees will be separated by NULL bytes.
     - `png`
     - `svg`

Example:
  `ginger -f conllu input.conll -t tikz output.tex`
"""

__version__ = 'ginger 0.11.0'

import sys
import contextlib
import pathlib

import itertools as it
import typing as ty

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
    import ginger  # NOQA
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
        if 'r' in mode:
            stream = sys.stdin
        else:
            stream = sys.stdout
        if 'b' in mode:
            fh = stream.buffer
        else:
            fh = stream
    else:
        fh = open(filename, mode, *args, **kwargs)

    try:
        yield fh
    finally:
        try:
            fh.close()
        except AttributeError:
            pass


def directory_multi_output(path: ty.Union[pathlib.Path, str],
                           data: ty.Iterable[ty.Union[str, bytes]],
                           name_format: str = '{i}'):
    '''Write the elements of `data` to individual files in `path`.
       The file names will be `n=name_format.format(i=<number>)` where
       `<number>` is the first integer such that `n` is not an
       existing file name in `path`.

         - `path` **must not** be the path to an existing non-directory
            file.'''
    path = pathlib.Path(path)  # Enforce `path`'s type
    if path.exists() and not path.is_dir():
        raise IOError('{path} is an existing non-directory file.'.format(path=path))
    if not path.exists():
        path.mkdir(parents=True)

    # Reuse the same iterator to find available names, to save on calls to `path.iterdir()`
    names = (name_format.format(i=i) for i in it.count())
    for file_content in data:
        # In most cases, this should use a single call to `path.iterdir()`, so caching it
        # is probably overkill
        file_name = next(n for n in names if n not in path.iterdir())
        try:
            (path/file_name).write_bytes(file_content)
        except TypeError:
            (path/file_name).write_text(file_content)


def stream_multi_output(stream: ty.BinaryIO,
                        data: ty.Iterable[bytes],
                        separator: ty.Union[bytes, str] = b'\x00'):
    '''Write the elements of `data` to `stream`, separated by `separator`.'''
    separator = bytes(separator)
    data_iter = iter(data)

    # Write the first element without separator before it
    stream.write(next(data_iter))
    for file_content in data_iter:
        stream.write(separator)
        stream.write(file_content)


def main_entry_point(argv=sys.argv[1:]):
    arguments = docopt(__doc__, version=__version__, argv=argv)
    # Since there are no support for default positional arguments in
    # docopt yet. Might be useful for complex default values, too
    if arguments['<destination>'] is None:
        arguments['<destination>'] = '-'

    with smart_open(arguments['<origin>'], encoding='utf8') as in_stream:
        in_lst = list(in_stream.readlines())

    if arguments['--from'] == 'guess' or arguments['--from'] is None:
        arguments['--from'] = libtreebank.guess(in_lst)

    try:
        parser, _ = libtreebank.formats[arguments['--from']]
    except KeyError:
        logging.error('{argsfrom!r} is not a supported format'.format(
            argsfrom=arguments['--from']))
        return 1

    if parser is None:
        logging.error('{argsfrom!r} is not supported as an input format'.format(
            argsfrom=arguments['--from']))
        return 1

    treebank = parser(in_lst)

    # Cairo-based outputs
    if arguments['--to'] in {'png', 'svg', 'pdf'}:
        if arguments['--to'] == 'png':
            out_bytes_lst = [libtreerender.to_png(t) for t in treebank]
        if arguments['--to'] == 'svg':
            out_bytes_lst = [libtreerender.to_svg(t) for t in treebank]
        if arguments['--to'] == 'pdf':
            out_bytes_lst = [libtreerender.to_pdf(t) for t in treebank]
        if arguments['<destination>'] == '-':
            with smart_open(arguments['<destination>'], 'wb') as out_stream:
                stream_multi_output(out_stream, out_bytes_lst)
        else:
            directory_multi_output(arguments['<destination>'], out_bytes_lst,
                                   name_format='{{i}}.{ext}'.format(ext=arguments['--to']))
    # Text outputs
    else:
        # Text-based graphics
        if arguments['--to'] == 'tikz':
            out_lst = [libtreerender.tikz(t) for t in treebank]

        elif arguments['--to'] == 'ascii':
            out_lst = [libtreerender.ascii_art(t) for t in treebank]

        # Treebank
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
            return 1

        if formatter is None:
            logging.error('{argsto!r} is not supported as an output format'.format(
                argsto=arguments['--to']))
            return 1

            out_lst = [formatter(t) for t in treebank]

        with smart_open(arguments['<destination>'], 'w', encoding='utf8') as out_stream:
            for t in out_lst[:-1]:
                out_stream.write(t)
                out_stream.write('\n\n')
            out_stream.write(out_lst[-1])
            out_stream.write('\n')


if __name__ == '__main__':
    sys.exit(main_entry_point())
