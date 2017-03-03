Ginger
======

ASCII-art representation of [Universal Dependencies](http://universaldependencies.org) trees.

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

    ginger <in-file> [<out-file>]

### Arguments
  - `<in-file>`   input file (in CoNLL-U format), `-` for standard input
  - `<out-file>`  output file, `-` standard input [default: -]

### Options
  - `-h`, `--help` Get some help

### Examples
  - Print to stdout
    ```
    ginger examples/test.conll
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
This licence (the so-called “MIT License”) is applicable to all the files in this repository.
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
