Ginger
======

Format conversion and graphical representation of [Universal Dependencies](http://universaldependencies.org) trees.

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
### Installing dependencies
Ginger depends on
  - [Python](https://www.python.org/): ^3.5
  - [docopt](http://docopt.org/): ^0.6

If you are using a sensible OS, Python 3 should already be installed, though it might be stuck at an older version (looking at you, Debian).
If it is the case : it is a shame, pester you sysadmin until they upgrade.

If Python 3 is installed, installing ginger through pip (see below) should take care of the other dependencies.

### Installing ginger
You don't actually need to install anything if you satisfy the dependencies above, running `python3 ginger.py` should just work.

However, if you want to have it installed at global level to get the `ginger` command in your path
  1. Grab the latest release from [Github](https://github.com/LoicGrobol/ginger/releases/latest)
  2. Unpack it and open a terminal inside the resulting folder
  2. Run `pip3 install .`

You can also install it directly from the tip (unstable but usually safe) of the master branch whith
```bash
pip3 install git+https://github.com/LoicGrobol/ginger/
```

Test if everything works by running `ginger examples/test.conll`.
The output should be the same as the ASCII-art tree above.

## Usage
```bash
ginger [--from <format>] <in-file> [--to] [<out-file>]
```

### Arguments
  - `<in-file>`   input file (in CoNLL-U format), `-` for standard input
  - `<out-file>`  output file, `-` for standard input (default: `-`)

### Options
  - `-f`, `--from <format>` input file format, see below (default: `guess`)
  - `-t`, `--to <format>`   output file format, see below (default: `ascii`)
  - `-h`, `--help` Get some help

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

### Input formats
  - `guess` Try to guess the file format, defaults to CoNLL-U

#### CoNLL
  - `conllx` [CoNLL-X format](https://web.archive.org/web/20160814191537/http://ilk.uvt.nl:80/conll/)
  - `conllu` [CoNLL-U format](http://universaldependencies.org/format.html)
  - `conll2009_gold`  [CoNLL-2009 format](http://ufal.mff.cuni.cz/conll2009-st/task-description.html)
    - Takes only the gold columns into account.
    - The P- and -PRED attributes are preserved in the `misc` attribute of the
      intermediate CoNLL-U tree.
  - `conll2009_sys`  [CoNLL-2009 format](http://ufal.mff.cuni.cz/conll2009-st/task-description.html)
    - Takes only the predicted columns into account.
    - The gold columns and the -PRED attributes are preserved in the `misc` attribute of the
      intermediate CoNLL-U tree.

#### Software
Formats used by mainstream NLP tools
  - `talismane`  Outputs of [Talismane](http://redac.univ-tlse2.fr/applications/talismane/talismane_en.html)
  - `mate_gold` Input/Output of [mate-tools](http://www.ims.uni-stuttgart.de/forschung/ressourcen/werkzeuge/matetools.en.html) (actually an alias for `conll2009_gold`)
  - `mate_sys` Input/Output of [mate-tools](http://www.ims.uni-stuttgart.de/forschung/ressourcen/werkzeuge/matetools.en.html) (actually an alias for `conll2009_sys`)

### Output formats
#### Treebanks
  - `conllu` [CoNLL-U format](http://universaldependencies.org/format.html)
  - `conll2009_gold` and `conll2009_sys`  [CoNLL-2009 format](http://ufal.mff.cuni.cz/conll2009-st/task-description.html)
    - `_gold` only fills in the gold columns
    - `_sys` only fills in the predicted columns


Note : no real effort is made to preserve informations that are not relevant to Universal
Dependencies, so this might be information-destructive, e.g. if converting from CoNLL-2009 to
itself, the P- attributes will be dropped.

#### Text-based graphics
These output formats are meant to be used by third-party tools that generate graphic outputs :
  - `ascii` ASCII-art (using Unicode characters, because, yes, we are subversive)
  - `tikz`  TikZ code.
    - Uses the `positioning`, `calc` and `shapes.multipart` libraries. Do not forget to include them in your document.
    - The output is only the `\tikzpicture` part, not a whole compilable document, there is
      [an example](examples/tree.tex) of such a document in `example`.
    - The code is quite verbose since we chose to rely on TikZ' own arithmetic capabilities in order to allow easier edition and reuse of the generated code.

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
