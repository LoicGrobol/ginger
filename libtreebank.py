"""Conversion from various treebank formats to CoNLL-U and back again.

A lot of the code comes from Kim Gerdes' [arborator][1], either directly
or through rewriting. Many thanks to him!

[1]: https://github.com/kimgerdes/arborator"""

import typing as ty
import re

try:
    import libginger
except ImportError:
    from ginger import libginger


# Generic formats
def conllx(tree_str: str) -> libginger.Tree:
    """Create an Universal Dependencies tree from a CoNLL-X tree."""
    root = libginger.Node(identifier=0, form='ROOT')
    res = [root]
    conllx_to_conllu_identifers = {0: 0}

    for i, line in enumerate(l.strip() for l in tree_str.splitlines()):
        # Skip comment lines
        if line.startswith('#'):
            next

        try:
            identifier, form, lemma, upostag, xpostag, feats, head, deprel, phead, pdeprel = line.split('\t')
        except ValueError:
            # TODO: Issue a warning here
            raise libginger.ParsingError('At line {i} : 10 columns expected, got a {n} ({line!r})'.format(i=i, n=len(line.split('\t')), line=line))

        try:
            identifier = int(identifier)
        except ValueError:
            # TODO: Issue a warning here
            raise libginger.ParsingError('At line {i} : the `id` field does not respect CoNLL-X specifications ({identifier!r})'.format(i=i, identifier=identifier))

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


def conll2009_gold(tree_str: str) -> libginger.Tree:
    """Create an Universal Dependencies tree from a CoNLL-2009 tree.
       This takes only the gold columns into account

       The P-attributes and 'pred are stored in the `misc` attribute."""
    root = libginger.Node(identifier=0, form='ROOT')
    res = [root]
    conllx_to_conllu_identifers = {0: 0}

    for i, line in enumerate(l.strip() for l in tree_str.splitlines()):
        # Skip comment lines
        if line.startswith('#'):
            next

        try:
            identifier, form, lemma, plemma, pos, ppos, feat, pfeat, head, phead, deprel, pdeprel, fillpred, pred, *apreds = line.split('\t')
        except ValueError:
            # TODO: Issue a warning here
            raise libginger.ParsingError('At line {i} : at least 14 columns expected, got a {n} ({line!r})'.format(i=i, n=len(line.split('\t')), line=line))

        try:
            identifier = int(identifier)
        except ValueError:
            # TODO: Issue a warning here
            raise libginger.ParsingError('At line {i} : the `id` field does not respect CoNLL-2009 specifications.'.format(i=i))

        lemma = re.sub(r'\s', '_', lemma)

        try:
            feat = dict() if feat == '_' else dict(e.split('=') for e in feat.split('|'))
        except ValueError:
            # Be nice : if empty, it should be an underscore, but let's be nice with spaces and empty strings, too
            if feat.isspace() or not feat:
                # TODO: Issue a warning here
                feat = dict()
            else:
                raise libginger.ParsingError('At line {i} : the `feat` field does not respect CoNLL-2009 specifications.'.format(i=i))

        try:
            head = int(head)
        except ValueError:
            raise libginger.ParsingError('At line {i} : the `head` field does not respect CoNLL-2009 specifications.'.format(i=i))
        try:
            phead = int(phead)
        except ValueError:
            if phead == '_' and pdeprel == '_':
                phead, pdeprel = None, None
            else:
                raise libginger.ParsingError('At line {i} : the `phead` field does not respect CoNLL-2009 specifications.'.format(i=i))

        # Deal with multi-token words
        tokens = list(re.findall(r'\w+|\S', form))
        # Deal with the first token
        real_identifier = len(res)
        conllx_to_conllu_identifers[identifier] = real_identifier
        res.append(libginger.Node(identifier=real_identifier, form=tokens[0],
                                  lemma=lemma, upostag=pos, feats=feat,
                                  head=head, deprel=deprel,
                                  deps=[],
                                  misc=dict_to_conll_map(
                                      {k: v for k, v in (('ppos', ppos),
                                                         ('phead', phead),
                                                         ('pdeprel', pdeprel),
                                                         ('fillpred', fillpred),
                                                         ('pred', pred),
                                                         ('apreds', ','.join(apreds)))
                                       if v and v != '_'})))

        # Now deal with the other tokens, their head will simply be the first token,
        # with the relation 'fixed'
        for t in tokens[1:]:
            res.append(libginger.Node(identifier=len(res), form=t, head=identifier, deprel='fixed'))

    # Now that we have a `Node` for every node,& let's do the linking
    for n in res[1:]:
        n.head = res[conllx_to_conllu_identifers[n.head]]
        n.deps = [(res[conllx_to_conllu_identifers[head]], deprel) for head, deprel in n.deps]

    return libginger.Tree(res)


def _node_to_conll2009_gold(node: libginger.Node):
    '''Return CoNLL-2009 representation of a `Node`.
       This writes the informations in the gold columns only.'''
    return '{identifier}\t{form}\t{lemma}\t_\t{upostag}\t_\t{feats}\t_\t{head}\t_\t{deprel}\t_\t_\t_\t_'.format(
        identifier='_' if node.identifier is None else node.identifier,
        form='_' if node.form is None else node.form,
        lemma='_' if node.lemma is None else node.lemma,
        upostag='_' if node.upostag is None else node.upostag,
        feats='|'.join('{feat}={value}'.format(feat=feat, value=value) for feat, value in node.feats.items()),
        head='_' if node.head is None else node.head.identifier,
        deprel='_' if node.deprel is None else node.deprel,
    )


def to_conll2009_gold(tree: libginger.Tree) -> str:
    '''Return a CoNLL-2009 representation of the tree.'''
    return '\n'.join(_node_to_conll2009_gold(n) for n in tree.nodes[1:])


def conll2009_sys(tree_str: str) -> libginger.Tree:
    """Create an Universal Dependencies tree from a CoNLL-2009 tree.
       This takes only the predicted columns into account

       The gold attributes are stored in the `misc` attribute."""
    root = libginger.Node(identifier=0, form='ROOT')
    res = [root]
    conllx_to_conllu_identifers = {0: 0}

    for i, line in enumerate(l.strip() for l in tree_str.splitlines()):
        # Skip comment lines
        if line.startswith('#'):
            next

        try:
            identifier, form, lemma, plemma, pos, ppos, feat, pfeat, head, phead, deprel, pdeprel, fillpred, pred, *apreds = line.split('\t')
        except ValueError:
            # TODO: Issue a warning here
            raise libginger.ParsingError('At line {i} : at least 14 columns expected, got a {n} ({line!r})'.format(i=i, n=len(line.split('\t')), line=line))
        try:
            identifier = int(identifier)
        except ValueError:
            # TODO: Issue a warning here
            raise libginger.ParsingError('At line {i} : the `id` field does not respect CoNLL-2009 specifications.'.format(i=i))

        lemma = re.sub(r'\s', '_', plemma)

        try:
            feat = dict() if pfeat == '_' else dict(e.split('=') for e in pfeat.split('|'))
        except ValueError:
            # Be nice : if empty, it should be an underscore, but let's be nice with spaces and empty strings, too
            if feat.isspace() or not feat:
                # TODO: Issue a warning here
                feat = dict()
            else:
                raise libginger.ParsingError('At line {i} : the `pfeat` field does not respect CoNLL-2009 specifications.'.format(i=i))

        try:
            phead = int(phead)
        except ValueError:
            raise libginger.ParsingError('At line {i} : the `phead` field does not respect CoNLL-2009 specifications.'.format(i=i))
        try:
            head = int(head)
        except ValueError:
            if head == '_' and pdeprel == '_':
                head, deprel = None, None
            else:
                raise libginger.ParsingError('At line {i} : the `head` field does not respect CoNLL-2009 specifications.'.format(i=i))

        # Deal with multi-token words
        tokens = list(re.findall(r'\w+|\S', form))
        # Deal with the first token
        real_identifier = len(res)
        conllx_to_conllu_identifers[identifier] = real_identifier
        res.append(libginger.Node(identifier=real_identifier, form=tokens[0],
                                  lemma=plemma, upostag=ppos, feats=pfeat,
                                  head=phead, deprel=pdeprel,
                                  deps=[],
                                  misc=dict_to_conll_map(
                                      {k: v for k, v in (('pos', pos),
                                                         ('head', head),
                                                         ('deprel', deprel),
                                                         ('fillpred', fillpred),
                                                         ('pred', pred),
                                                         ('apreds', ','.join(apreds)))
                                       if v and v != '_'})))

        # Now deal with the other tokens, their head will simply be the first token,
        # with the relation 'fixed'
        for t in tokens[1:]:
            res.append(libginger.Node(identifier=len(res), form=t, head=identifier, deprel='fixed'))

    # Now that we have a `Node` for every node,& let's do the linking
    for n in res[1:]:
        n.head = res[conllx_to_conllu_identifers[n.head]]
        n.deps = [(res[conllx_to_conllu_identifers[head]], deprel) for head, deprel in n.deps]

    return libginger.Tree(res)


def _node_to_conll2009_sys(node: libginger.Node):
    '''Return CoNLL-2009 representation of a `Node`.
       This writes the informations in the pred columns only.'''
    return '{identifier}\t{form}\t_\t{lemma}\t_\t{upostag}\t_\t{feats}\t_\t{head}\t_\t{deprel}\t_\t_\t_'.format(
        identifier='_' if node.identifier is None else node.identifier,
        form='_' if node.form is None else node.form,
        lemma='_' if node.lemma is None else node.lemma,
        upostag='_' if node.upostag is None else node.upostag,
        feats='|'.join('{feat}={value}'.format(feat=feat, value=value) for feat, value in node.feats.items()),
        head='_' if node.head is None else node.head.identifier,
        deprel='_' if node.deprel is None else node.deprel,
    )


def to_conll2009_sys(tree: libginger.Tree) -> str:
    '''Return a CoNLL-2009 representation of the tree.'''
    return '\n'.join(_node_to_conll2009_gold(n) for n in tree.nodes[1:])


def conllu(tree_str: str) -> libginger.Tree:
    """Create an Universal Dependencies tree from a CoNLL-U tree."""
    return libginger.Tree.from_conll(tree_str)


def to_conllu(tree: libginger.Tree) -> str:
    """Return `tree` in CoNLL-U format."""
    return tree.to_conll()


# Parser-specific formats
def talismane(tree_str: str) -> libginger.Tree:
    """Create an Universal Dependencies tree from a Talismane tree.

       Talismane outputs are essentially CoNLL-X files, with incompatible
       stylistic idiosyncrasies."""
    conllx_str = re.sub(r'\|\t', r'\t', tree_str)
    return conllx(conllx_str)


def dict_to_conll_map(d: ty.Dict) -> str:
    'Return the CoNLL standard description of a dict.'
    return '|'.join('{key}={val}'.format(key=key, val=val) for key, val in d.items())


# Guessing tools
def guess(filecontents: str) -> str:
    """Guess the format of a file. Return the name of the format in a way
       as a key in `formats`."""
    lines = filecontents.split('\n')
    first_line_columns = next(l for l in lines if l).split('\t')

    if len(first_line_columns) == 10:  # 10 columns, assuming CoNLL-[XU] of some kind
        # CoNLL-X
        if not re.match(r'_|^([^:|]+:[^:|])(\|[^:|]+:[^:|])*$', first_line_columns[-2]):
            if any(l.split('\t')[5].endswith('|') for l in lines if l and not l.isspace()):
                return 'talismane'
            return 'conllx'
    elif len(first_line_columns) >= 14:  # 14 columns or more assume CoNLL-2009:
        if any(l.split('\t')[2] != '_' for l in lines if l and not l.isspace()):
            return 'conll2009_sys'
        return 'conll2009_gold'

    # Default to CoNLL-U
    return "conllu"


formats = {'conllx': (conllx, None),
           'talismane': (talismane, None),
           'conllu': (conllu, to_conllu),
           'conll2009_gold': (conll2009_gold, to_conll2009_gold),
           'conll2009_sys': (conll2009_sys, to_conll2009_sys),
           'mate_gold': (conll2009_gold, to_conll2009_gold),
           'mate_sys': (conll2009_sys, to_conll2009_sys)}
