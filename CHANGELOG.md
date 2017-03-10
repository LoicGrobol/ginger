Changelog
=========
## 0.3.0 [UNRELEASED]
### Bugfix
  - CoNLL-U parsing now support comment lines, empty nodes and multiword tokens

### API changes
  - libginger
    - CoNLL-U parsing now raise a specific `ParsingError` exception on parsing errors with a more
      informative message
    - Renamed `Tree.subtree()` → `Tree.descendance()` in order to allow adding a `Tree.subtree()`
      function that will really return a `Tree` instead of a list of nodes.

## 0.2.1 [2017-03-05]
### Improvements
  - Nicer generated TikZ code

## 0.2.0 [2017-03-05]
### New features
  - Add support for outputting TikZ code

### Breaking
  - CLI arguments changed

## 0.1.0 [2017-03-04]
### New features
  - Accept CoNLL-X files as input

### Bugfix
  - Fix behaviour when used in pipelines  (no more `BrokenPipeError`)

## 0.0.1 [2017-03-04]
### Bugfix
  - Actually allow running without installation.

## 0.0.0 [2017-03-03]
Initial release
