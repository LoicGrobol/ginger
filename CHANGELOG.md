Changelog
=========
## 0.4.0 [2017-03-17]
### New features
  - Support the [CoNLL-2009 format](http://ufal.mff.cuni.cz/conll2009-st/task-description.html)

### API change
  - Minor change in the representation of `Node`s

### Bugfix
  - Fix invocation from installed package

## 0.3.0 [2017-03-13]
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
