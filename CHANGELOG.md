Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/) and this project adheres to
[Semantic Versioning](http://semver.org/).

## [Unreleased]

[Unreleased]: https://github.com/LoicGrobol/ginger/compare/v0.14.1...HEAD

### Added

- Support for the `tikz-dependency` output format

### Changed

- Modernized CI and ops infrastructure
- Modernized packaging

## [0.14.1] - 2020-06-02

[0.14.1]: https://github.com/LoicGrobol/ginger/compare/v0.14.0...v0.14.1

### Fixed

- Installation on Windows without cairo ([#10](https://github.com/LoicGrobol/ginger/issues/10))

## [0.14.0] - 2019-12-27

[0.14.0]: https://github.com/LoicGrobol/ginger/compare/v0.13.0...v0.14.0

### Changed

- Dependency on pycairo is optional again
- Usage without installation is not supported anymore

## [0.13.0] - 2018-04-14

### Added

- Image format outputs !!!!!!!!!!!!

## [0.12.0] - 2018-04-14

### Fixed

- `libginger.Tree.root` is now the actual root of the tree
- `libginger.UDNode.space_after` is now correctly true if `misc` is empty
- `libginger.Tree.descendance` is now sorted

### Changed

- Use the regular setuptools install mechanisms instead of our previous homebrewn solution
- Move dist files to [`ginger/`](/ginger/)

## [0.11.0] - 2017-12-27

### Added

- Support for CoNLL-U `sent_id` and `text` metadata
- UD Nodes (`libginger.UDNodes` and subtypes) have a new `space_after: bool` property corresponding
  to UD 'SpaceAfter'
- A tree with extended dependencies in [`test.conll`](examples/test.conll)

### Changed

- `ginger` returns proper exit codes
- Support for `identifier` and `misc` fields for all UD Nodes, including `libginger.MultiTokenNode`
- Support for arbitrary iterables for `deps` in `libginger.Node` constructor
- `_` columns in CoNLL files are now translated to `None` attributes instead of a litteral `_`

### Fixed

- `libginger.Tree.raw_token_sequence` is now actually UD-compliant

  - It doesn't include words that are part of a multi-word token anymore. E.g. only _vámonos_ and
    not _vamos_ and _nos_.
  - It doesn't return the root node anymore.

- `libginger.Tree.word_sequence` is now actually UD-compliant, as it does not include the root node anymore
- `libtreebank.conll…` direct str parsing should work now
- CoNLL-U metadata are now properly read

## [0.10.3] - 2017-08-22

### Fixed

- Importing in tests now works as it should
- Actually ignore lines that should be ignored in treebanks

### Changed

- Full UD for the first example of [`/examples/test.conll`](/examples/test.conll)
- Format the changelog according to [Keep a Changelog v1.0.0](http://keepachangelog.com/en/1.0.0)

## [0.10.2] - 2017-08-22 [YANKED]

## [0.10.1] - 2017-05-04

### Fixed

- Version number in `ginger.py`

## [0.10.0] - 2017-05-04

### Fixed

- Improved release message

## [0.9.2] - 2017-05-04

### Added

- An [auto-release script](tools/release.py) that works in a fashion similar to [apm](https://github.com/atom/apm).

### Fixed

- Running vendored versions from other folders should work

## [0.9.1] - 2017-04-28

### Fixed

- (libginger) `Tree.raw_token_sequence` should work correctly
- Allow vendoring a version when another version is globally installed

## [0.9.0] - 2017-04-27

### Added

- Now support multi-word tokens for CoNLL-U files

### Fixed

- Correctly catch format errors on CoNLL identifiers

## [0.8.1] - 2017-04-14

### Fixed

- CoNLL-U export now deals correctly with **all** empty fields

## [0.8.0] - 2017-04-14

### Fixed

- Fixed bad formatting on parsing error
- Remove obsolete tests
- Fixed Talismane parsing

### Changed

- Hardened CoNLL parsing strictness
- Moved `ParsingError` from `libginger` to `libtreebank`

### Added

- Added basic test for CoNLL-U parsing

## [0.7.0] - 2017-04-07

### Fixed

- Format guessing now plays nice with CoNLL-2009
- Issue proper errors on wrong number of columns for CoNLL-2009
- More graceful handling of SIGINT
- CoNLL2009-sys now properly exports to CoNLL-2009 sys...
- `guess` now correctly guess CoNLL-2009-sys
- CoNLL2009-sys parsing correctly deals with PDEPREL and PFEAT values

### Changed

- In `libtreebank` : the parsers now deal with whole treebank files (as iterables over lines) instead of on a per-tree basis

## [0.6.0] - 2017-04-03

### Fixed

- Issue loading `package.json` in `setup.py` due to encoding
- Force UTF-8 encoding on I/O

### Changed

- Split the CoNLL-2009/mate format into a Gold and a System version

  - The format previously known as `conll2009` is now `conll2009_gold`
  - We have a new `conll2009_sys` that uses predicted columns instead of gold ones

## [0.5.1] - 2017-04-03

### Fixed

- Add dependency on`docopt`

## [0.5.0] - 2017-03-31

### Added

- `mate` format alias for CoNLL-2009
- Treebank outputs (see [README](README.md))

### Changed

- Improve [test.conll](/examples/test.conll) to be an actual treebank instead of a single tree.

### Fixed

- `libtreebank`

  - Trying to parse CoNLL-[UX] files with more or less than 10 columns now throw a proper `ParsingError`.

## [0.4.1] - 2017-03-29

### Changed

- Try to conform to [Keep a Changelog](http://keepachangelog.com/).

### Bugfix

- Properly add EOL at the end of outputs
- Fixed issues with treebank files starting with a blank line

## [0.4.0] - 2017-03-17

### New features

- Support the [CoNLL-2009 format](http://ufal.mff.cuni.cz/conll2009-st/task-description.html)

### API change

- Minor change in the representation of `Node`s

### Bugfix

- Fix invocation from installed package

## [0.3.0] - 2017-03-13

### New features

- Support [Talismane](http://redac.univ-tlse2.fr/applications/talismane/talismane_en.html) outputs as inputs

### Bugfix

- CoNLL-U parsing now support comment lines, empty nodes and multi-word tokens
- CoNLL-X parsing now support comment lines, empty nodes and multi-token words and takes the projective dependency attributes into account
- Fixed TikZ rendering of token with missing information

### API changes

- libginger

  - CoNLL parsing now raise a specific `ParsingError` exception on parsing errors with a more informative message
  - Renamed `Tree.subtree()` → `Tree.descendance()` in order to allow adding a `Tree.subtree()` function that will really return a `Tree` instead of a list of nodes.
  - Moved tree rendering functions to libtreerender

- libtreebank

  - Almost completely rewritten to parse whole trees instead of translating line-by-line

## [0.2.1] - 2017-03-05

### Improvements

- Nicer generated TikZ code

## [0.2.0] - 2017-03-05

### New features

- Add support for outputting TikZ code

### Breaking

- CLI arguments changed

## [0.1.0] - 2017-03-04

### New features

- Accept CoNLL-X files as input

### Bugfix

- Fix behaviour when used in pipelines (no more `BrokenPipeError`)

## [0.0.1] - 2017-03-04

### Bugfix

- Actually allow running without installation.

## [0.0.0] - 2017-03-03

Initial release

[0.0.0]: https://github.com/LoicGrobol/ginger/tree/v0.0.0
[0.0.1]: https://github.com/LoicGrobol/ginger/compare/v0.0.0...v0.0.1
[0.1.0]: https://github.com/LoicGrobol/ginger/compare/v0.0.0...v0.1.0
[0.10.0]: https://github.com/LoicGrobol/ginger/compare/v0.9.2...0.10.0
[0.10.1]: https://github.com/LoicGrobol/ginger/compare/v0.10.0...0.10.1
[0.10.2]: https://github.com/LoicGrobol/ginger/compare/v0.10.1...0.10.2
[0.10.3]: https://github.com/LoicGrobol/ginger/compare/v0.10.2...0.10.3
[0.11.0]: https://github.com/LoicGrobol/ginger/compare/v0.10.3...0.11.0
[0.12.0]: https://github.com/LoicGrobol/ginger/compare/v0.11.0...0.12.0
[0.13.0]: https://github.com/LoicGrobol/ginger/compare/v0.12.0...0.13.0
[0.2.0]: https://github.com/LoicGrobol/ginger/compare/v0.2.0...v0.1.0
[0.2.1]: https://github.com/LoicGrobol/ginger/compare/v0.2.0...v0.2.1
[0.3.0]: https://github.com/LoicGrobol/ginger/compare/v0.3.0...v0.2.1
[0.4.0]: https://github.com/LoicGrobol/ginger/compare/v0.3.0...v0.4.0
[0.4.1]: https://github.com/LoicGrobol/ginger/compare/v0.4.0...v0.4.1
[0.5.0]: https://github.com/LoicGrobol/ginger/compare/v0.4.1...v0.5.0
[0.5.1]: https://github.com/LoicGrobol/ginger/compare/v0.5.0...v0.5.1
[0.6.0]: https://github.com/LoicGrobol/ginger/compare/v0.5.1...v0.6.0
[0.7.0]: https://github.com/LoicGrobol/ginger/compare/v0.6.0...v0.7.0
[0.8.0]: https://github.com/LoicGrobol/ginger/compare/v0.7.0...v0.8.0
[0.8.1]: https://github.com/LoicGrobol/ginger/compare/v0.8.0...v0.8.1
[0.9.0]: https://github.com/LoicGrobol/ginger/compare/v0.8.1...v0.9.0
[0.9.1]: https://github.com/LoicGrobol/ginger/compare/v0.9.0...v0.9.1
[0.9.2]: https://github.com/LoicGrobol/ginger/compare/v0.9.1...0.9.2
