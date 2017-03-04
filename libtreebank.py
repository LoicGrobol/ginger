"""Conversion from various treebank formats to CoNLL-U.

A lot of the code comes from Kim Gerdes' [arborator][1], either directly
or through rewriting. Many thanks to him!

[1]: https://github.com/kimgerdes/arborator"""

import re


def conllx(line: str):
    """Conversion from CoNLL-X line to CoNLL-U line.

       Just ignore the PHEAD and PDEP columns."""
    if not line or line.isspace():
        return '\n'
    identifier, form, lemma, upostag, xpostag, feats, head, deprel, phead, pdep = line.split('\t')
    deps, misc = '_'*2
    return '\t'.join((identifier, form, lemma, upostag, xpostag, feats, head, deprel, phead, deps, misc))


def conllu(line: str):
    """Only the identity function."""
    return line


def guess(filecontents: str) -> str:
    """Guess the format of a file. Return the name of the format in a way
       as a key in `formats`."""
    lines = filecontents.split('\n')
    first_line_columns = next(l for l in lines if l).split('\t')

    if len(first_line_columns) == 10:  # 10 columns, assuming CoNLL of some kind
        # CoNLL-X
        if (any(c.isspace() for c in first_line_columns) or
            not re.match(r'_|^([^:|]+:[^:|]\|)+$', first_line_columns[-1]) or
            not re.match(r'_|^([^:|]+:[^:|]\|)+$', first_line_columns[-2])):
            return 'conllx'

    # Default to CoNLL-U
    return "conllu"


formats = {'conllx': conllx,
           'conllu': conllu}
