Change Log
==========
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/) and this project adheres to
[Semantic Versioning](http://semver.org/).

## [Unreleased]
[Unreleased]: https://github.com/LoicGrobol/ginger/compare/v0.4.0...HEAD
### Added
  - `mate` format alias for CoNLL-2009
  - Treebank outputs (see [README](README.md))

### Changed
  - Improve [test.conll](/examples/test.conll) to be an actual treebank instead of a single tree.
### Fixed
  - `libtreebank`
    - Trying to parse CoNLL-X files with more or less than 10 columns now throw a proper `ParsingError`.

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
