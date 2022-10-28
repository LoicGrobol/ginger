import pathlib

import sys

import itertools as it
import typing as ty

import click

from ginger import libtreebank
from ginger import libtreerender
from ginger import __version__


def directory_multi_output(
    path: ty.Union[pathlib.Path, str],
    data: ty.Iterable[ty.Union[str, bytes]],
    name_format: str = "{i}",
):
    """
    Write the elements of `data` to individual files in `path`.

    The file names will be `n=name_format.format(i=<number>)` where `<number>` is the first integer
    such that `n` is not an existing file name in `path`.

      - `path` **must not** be the path to an existing file.
    """
    path = pathlib.Path(path)  # Enforce `path`'s type
    if path.exists() and not path.is_dir():
        raise IOError("{path} is an existing non-directory file.".format(path=path))
    if not path.exists():
        path.mkdir(parents=True)

    # Reuse the same iterator to find available names, to save on calls to `path.iterdir()`
    names = (name_format.format(i=i) for i in it.count())
    for file_content, file_name in zip(
        data, (n for n in names if not (path / n).exists())
    ):
        try:
            (path / file_name).write_bytes(file_content)
        except TypeError:
            (path / file_name).write_text(file_content)


def stream_multi_output(
    stream: ty.BinaryIO,
    data: ty.Iterable[bytes],
    separator: ty.Union[bytes, str] = b"\x00",
):
    """Write the elements of `data` to `stream`, separated by `separator`."""
    separator = bytes(separator)
    data_iter = iter(data)

    # Write the first element without separator before it
    stream.write(next(data_iter))
    for file_content in data_iter:
        stream.write(separator)
        stream.write(file_content)


epilog = """Input formats:

The input must be either the path to an existing file or `-` for standard input. The data that
it contains must be in one of the following formats:

\b
  - `guess`           Try to guess the file format, defaults to CoNLL-U
  - `conllu`          CoNLL-U format
  - `conllx`          CoNLL-X format
  - `conll2009_gold`  CoNLL-2009 format (Gold columns only)
  - `conll2009_sys`   CoNLL-2009 format (Predicted columns only)
  - `talismane`       Outputs of Talismane
  - `mate_gold`       Alias for `conll2009_gold`, used by mate-tools
  - `mate_sys`        Alias for `conll2009_sys`, used by mate-tools

Text formats:

To use these formats, the output destination must be either a file and thus must not be the path to
an existing directory, or `-` for the standard output.

\b
  - `ascii`  ASCII-art (using unicode characters, because, yes, we are subversive)
  - `tikz`   TikZ code. Use the `positioning`, `calc` and `shapes.multipart` tikz libraries
  - `tikz-dependency`   LaTeX code for the `tikz-dependency` package

Image formats:

To use these formats, the output destination must be either a directory and thus must not be the
path of an existing file, or `-` for the standard output, in which case the byte streams
corresponding to different trees will be separated by NULL bytes.

\b
  - `png`
  - `svg`
  - `pdf`

Example:

  `ginger -f conllu input.conll -t tikz output.tex`"""


@click.command(
    help="Format conversion and graphical representations of Universal Dependencies tree.",
    epilog=epilog,
)
@click.argument(
    "origin",
    type=click.File("r"),
)
@click.argument(
    "destination",
    type=click.Path(writable=True, allow_dash=True),
    default="-",
)
@click.option(
    "--from",
    "-f",
    "origin_format",
    default="guess",
    type=click.Choice(
        [
            "guess",
            *sorted([f for f, (i, _) in libtreebank.formats.items() if i is not None]),
        ]
    ),
    help="Input format",
    show_default=True,
)
@click.option(
    "--to",
    "-t",
    "destination_format",
    default="ascii",
    type=click.Choice(
        sorted(
            [
                *("ascii", "tikz", "tikz-dependency"),
                *("png", "svg", "pdf"),
                *(f for f, (_, o) in libtreebank.formats.items() if o is not None),
            ]
        )
    ),
    help="Input format",
    show_default=True,
)
def main_entry_point(
    origin: ty.TextIO,
    destination: str,
    origin_format: str,
    destination_format: str,
):
    in_lst = list(origin.readlines())

    if origin_format == "guess":
        origin_format = libtreebank.guess(in_lst)

    parser, _ = libtreebank.formats.get(origin_format, (None, None))

    if parser is None:
        print(f"{destination_format!r} is not supported as an input format")
        return 1

    treebank = parser(in_lst)

    # Binary outputs
    if destination_format in {"png", "svg", "pdf"}:
        if destination_format == "png":
            out_bytes_lst = [libtreerender.to_png(t) for t in treebank]
        if destination_format == "svg":
            out_bytes_lst = [libtreerender.to_svg(t) for t in treebank]
        if destination_format == "pdf":
            out_bytes_lst = [libtreerender.to_pdf(t) for t in treebank]

        if destination == "-":
            with click.open_file(destination, "wb") as out_stream:
                stream_multi_output(ty.cast(ty.BinaryIO, out_stream), out_bytes_lst)
        else:
            directory_multi_output(
                destination,
                out_bytes_lst,
                name_format=f"{{i}}.{destination_format}",
            )
    # Text outputs
    else:
        # Text-based graphics
        if destination_format == "tikz":
            out_lst = [libtreerender.tikz(t) for t in treebank]
        elif destination_format == "tikz-dependency":
            out_lst = [libtreerender.tikz_dependency(t) for t in treebank]
        elif destination_format == "ascii":
            out_lst = [libtreerender.ascii_art(t) for t in treebank]

        # Treebank
        else:
            _, formatter = libtreebank.formats.get(destination_format, (None, None))

            if formatter is None:
                print(f"{destination_format!r} is not supported as an output format")
                return 1

            out_lst = [formatter(t) for t in treebank]

        with click.open_file(destination, "w", encoding="utf8") as out_stream:
            for t in out_lst[:-1]:
                out_stream.write(t)
                out_stream.write("\n\n")
            out_stream.write(out_lst[-1])
            out_stream.write("\n")


if __name__ == "__main__":
    sys.exit(main_entry_point())
