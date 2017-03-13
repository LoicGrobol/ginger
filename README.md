Ginger
======

Graphical representation of [Universal Dependencies](http://universaldependencies.org) trees.

![2d graphical representation](doc/tree.png)

```
│
│          ┌─────────────┐
│┌────────┐│             │
││        ││             │┌─────────┐    ┌────┐
││    ┌───│┤         ┌───│┤         │┌──┐│    │
↓│    ↓   ↓│         ↓   ↓│         ↓│  ↓│    ↓
ROOT  Je  reconnais  l'  existence  du  kiwi  .
```

## Installation

No installation needed, just run `ginger.py`.
If you want to have it installed at global level, run `pip3 install .`

Test if everything work by running `ginger examples/test.conll`.
The output should be the same as the tree above.

## Usage
```
ginger [--from <format>] <in-file> [--to] [<out-file>]
```

### Arguments
  - `<in-file>`   input file (in CoNLL-U format), `-` for standard input
  - `<out-file>`  output file, `-` for standard input (default: `-`)

### Options
  - `-f`, `--from <format>` input file format, see below (default: `guess`)
  - `-t`, `--to <format>`   output file foramt, see below (default: `ascii`)
  - `-h`, `--help` Get some help

### Input formats
  - `guess` Try to guess the file format, defaults to CoNLL-U
  - `conllx` [CoNLL-X format](https://web.archive.org/web/20160814191537/http://ilk.uvt.nl:80/conll/)
  - `conllu` [CoNLL-U format](http://universaldependencies.org/format.html)
  - `talismane`  Outputs of [Talismane](http://redac.univ-tlse2.fr/applications/talismane/talismane_en.html)

### Output formats
  - `ascii` ASCII-art (using unicode character, because, yes, we are subversive)
  - `tikz`  TikZ code.
    - Uses the `positioning`, `calc` and `shapes.multipart` libraries. Do not forget to include them in your document.
    - The output is only the `\tikzpicture` part, not a whole compilable document, there is
      [an example](examples/tree.tex) of such a document in `example`.
    - The code is quite verbose since we chose to rely on TikZ' own arithmetic capabilities in order to allow easier edition and reuse of the generated code.

### Examples
  - Print to stdout
    ```
    ginger examples/test.conll
    ```
  - Assume CoNLL-X for input format
    ```
    ginger -f conllx spam.conllx
    ```
  - Output TikZ code
    ```
    ginger examples/test.conll -t tikz
    ```
  - Print to a file
    ```
    ginger examples/test.conll examples/output.asciiart
    ```
  - Pipe in and out
    ```
    cat examples/test.conll | ginger - | less
    ```
  - Get help
    ```
    ginger --help
    ```

## Development
Development and releases on [Github](https://github.com/loic-grobol/ginger).

### Dependencies
  - No dependencies for the main content
  - The unit tests are in `test/` and use [pytest](http://pytest.org). They are a bit of a joke right now, though.

## License
This licence (the so-called “MIT License”) applies to all the files in this repository.
See also [LICENSE.md](LICENSE.md).

```
Copyright 2017 Loïc Grobol <loic.grobol@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
associated documentation files (the "Software"), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify, merge, publish, distribute,
sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT
OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```
