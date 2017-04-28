Change Log
==========
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/) and this project adheres to
[Semantic Versioning](http://semver.org/).

## [Unreleased]
[Unreleased]: https://github.com/LoicGrobol/ginger/compare/v0.9.0...HEAD
### Fixed
  - (libginger) `Tree.raw_token_sequence` should work correctly

## [0.9.0] - 2017-04-27
[0.9.0]: https://github.com/LoicGrobol/ginger/compare/v0.8.1...v0.9.0
### Added
  - Now support multi-word tokens for CoNLL-U files

### Fixed
  - Correctly catch format errors on CoNLL identifiers

## [0.8.1] - 2017-04-14
[0.8.1]: https://github.com/LoicGrobol/ginger/compare/v0.8.0...v0.8.1
### Fixed
  - CoNLL-U export now deals correctly with **all** empty fields

## [0.8.0] - 2017-04-14
[0.8.0]: https://github.com/LoicGrobol/ginger/compare/v0.7.0...v0.8.0
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
[0.7.0]: https://github.com/LoicGrobol/ginger/compare/v0.6.0...v0.7.0
### Fixed
  - Format guessing now plays nice with CoNLL-2009
  - Issue proper errors on wrong number of columns for CoNLL-2009
  - More graceful handling of SIGINT
  - CoNLL2009-sys now properly exports to CoNLL-2009 sys…
  - `guess` now correctly guess CoNLL-2009-sys
  - CoNLL2009-sys parsing correctly deals with PDEPREL and PFEAT values

### Changed
  - In `libtreebank` : the parsers now deal with whole treebank files
    (as iterables over lines) instead of on a per-tree basis

## [0.6.0] - 2017-04-03
[0.6.0]: https://github.com/LoicGrobol/ginger/compare/v0.5.1...v0.6.0
### Fixed
  - Issue loading `package.json` in `setup.py` due to encoding
  - Force UTF-8 encoding on I/O

### Changed
  - Split the CoNLL-2009/mate format into a Gold and a System version
    - The format previously known as `conll2009` is now `conll2009_gold`
    - We have a new `conll2009_sys` that uses predicted columns instead of gold ones

## [0.5.1] - 2017-04-03
[0.5.1]: https://github.com/LoicGrobol/ginger/compare/v0.5.0...v0.5.1
### Fixed
  - Add dependency on`docopt`

## [0.5.0] - 2017-03-31
[0.5.0]: https://github.com/LoicGrobol/ginger/compare/v0.4.1...v0.5.0
### Added
  - `mate` format alias for CoNLL-2009
  - Treebank outputs (see [README](README.md))

### Changed
  - Improve [test.conll](/examples/test.conll) to be an actual treebank instead of a single tree.

### Fixed
  - `libtreebank`
    - Trying to parse CoNLL-[UX] files with more or less than 10 columns now throw a proper `ParsingError`.

## [0.4.1] - 2017-03-29
[0.4.1]: https://github.com/LoicGrobol/ginger/compare/v0.4.0...v0.4.1
### Changed
  - Try to conform to [Keep a Changelog](http://keepachangelog.com/).

### Bugfix
  - Properly add EOL at the end of outputs
  - Fixed issues with treebank files starting with a blank line

## [0.4.0] - 2017-03-17
[0.4.0]: https://github.com/LoicGrobol/ginger/compare/v0.3.0...v0.4.0
### New features
  - Support the [CoNLL-2009 format](http://ufal.mff.cuni.cz/conll2009-st/task-description.html)

### API change
  - Minor change in the representation of `Node`s

### Bugfix
  - Fix invocation from installed package

## [0.3.0] - 2017-03-13
[0.3.0]: https://github.com/LoicGrobol/ginger/compare/v0.3.0...v0.2.1
### New features
  - Support [Talismane](http://redac.univ-tlse2.fr/applications/talismane/talismane_en.html) outputs
    as inputs

### Bugfix
  - CoNLL-U parsing now support comment lines, empty nodes and multi-word tokens
  - CoNLL-X parsing now support comment lines, empty nodes and multi-token words and takes
    the projective dependency attributes into account
  - Fixed TikZ rendering of token with missing information

### API changes
  - libginger
    - CoNLL parsing now raise a specific `ParsingError` exception on parsing errors with a more
      informative message
    - Renamed `Tree.subtree()` → `Tree.descendance()` in order to allow adding a `Tree.subtree()`
      function that will really return a `Tree` instead of a list of nodes.
    - Moved tree rendering functions to libtreerender
  - libtreebank
    - Almost completely rewritten to parse whole trees instead of translating line-by-line

## [0.2.1] - 2017-03-05
[0.2.1]: https://github.com/LoicGrobol/ginger/compare/v0.2.0...v0.2.1
### Improvements
  - Nicer generated TikZ code

## [0.2.0] - 2017-03-05
[0.2.0]: https://github.com/LoicGrobol/ginger/compare/v0.2.0...v0.1.0
### New features
  - Add support for outputting TikZ code

### Breaking
  - CLI arguments changed

## [0.1.0] - 2017-03-04
[0.1.0]: https://github.com/LoicGrobol/ginger/compare/v0.0.0...v0.1.0
### New features
  - Accept CoNLL-X files as input

### Bugfix
  - Fix behaviour when used in pipelines  (no more `BrokenPipeError`)

## [0.0.1] - 2017-03-04
[0.0.1]: https://github.com/LoicGrobol/ginger/compare/v0.0.0...v0.0.1
### Bugfix
  - Actually allow running without installation.

## [0.0.0] - 2017-03-03
[0.0.0]: https://github.com/LoicGrobol/ginger/tree/v0.0.0
Initial release
