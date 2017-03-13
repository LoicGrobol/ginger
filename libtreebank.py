"""Conversion from various treebank formats to CoNLL-U.

A lot of the code comes from Kim Gerdes' [arborator][1], either directly
or through rewriting. Many thanks to him!

[1]: https://github.com/kimgerdes/arborator"""

import re

import libginger


def conllx(tree_str: str) -> libginger.Tree:
    """Create an Universal Dependencies tree from a CoNLL-X tree."""
    root = libginger.Node(identifier=0, form='ROOT')
    res = [root]
    conllx_to_conllu_identifers = {0: 0}

    for i, l in enumerate(l.strip() for l in tree_str.splitlines()):
        # Skip comment lines
        if l.startswith('#'):
            next
        identifier, form, lemma, upostag, xpostag, feats, head, deprel, phead, pdeprel = l.split('\t')

        try:
            identifier = int(identifier)
        except ValueError:
            # TODO: Issue a warning here
            raise libginger.ParsingError('At line {i} : the `id` field does not respect CoNLL-U specifications.'.format(i=i))

        lemma = re.sub(r'\s', '_', lemma)

        try:
            feats = dict() if feats == '_' else dict(e.split('=') for e in feats.split('|'))
        except ValueError:
            # Be nice : if empty, it should be an underscore, but let's be nice with spaces and empty strings, too
            if feats.isspace() or not feats:
                # TODO: Issue a warning here
                feats = dict()
            else:
                raise libginger.ParsingError('At line {i} : the `feats` field does not respect CoNLL-X specifications.'.format(i=i))

        try:
            head = int(head)
        except ValueError:
            raise libginger.ParsingError('At line {i} : the `head` field does not respect CoNLL-X specifications.'.format(i=i))
        try:
            phead = int(phead)
        except ValueError:
            if phead == '_' and pdeprel == '_':
                phead, pdeprel = None, None
            else:
                raise libginger.ParsingError('At line {i} : the `phead` field does not respect CoNLL-X specifications.'.format(i=i))

        # Deal with multi-token words
        tokens = list(re.findall(r'\w+|\S', form))
        # Deal with the first token
        real_identifier = len(res)
        conllx_to_conllu_identifers[identifier] = real_identifier
        res.append(libginger.Node(identifier=real_identifier, form=tokens[0],
                                  lemma=lemma, upostag=upostag, xpostag=xpostag, feats=feats,
                                  head=head, deprel=deprel,
                                  deps=[] if phead is None else [(phead, pdeprel)]))

        # Now deal with the other tokens, their head will simply be the first token,
        # with the relation 'fixed'
        for t in tokens[1:]:
            res.append(libginger.Node(identifier=len(res), form=t, head=identifier, deprel='fixed'))

    # Now that we have a `Node` for every node, let's do the linking
    for n in res[1:]:
        n.head = res[conllx_to_conllu_identifers[n.head]]
        n.deps = [(res[conllx_to_conllu_identifers[head]], deprel) for head, deprel in n.deps]

    return libginger.Tree(res)


def conllu(tree_str: str) -> libginger.Tree:
    """Create an Universal Dependencies tree from a CoNLL-U tree."""
    return libginger.Tree.from_conll(tree_str)


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
