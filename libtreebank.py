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


def trees_from_conll(lines_lst: ty.Iterable[str]) -> ty.Iterable[str]:
    '''Extract individual tree strings from the lines of a CoNLL-like file.'''
    current = []  # type: ty.List[str]
    for line in lines_lst:
        # Skip comment lines
        if line.startswith('#'):
            next
        elif line.isspace():
            if current:
                yield current
                current = []
            next
        else:
            current.append(line)
    # Flush the buffer at the end of the file
    if current:
        yield current


# Generic formats
def conllu(treebank_lst: ty.Iterable[str]) -> ty.Iterable[libginger.Tree]:
    '''Parse a CoNLL-U treebank file and return its trees.'''
    trees = trees_from_conll(treebank_lst)
    return (_conllu_tree(t) for t in trees)


def _conllu_tree(tree_str: ty.Iterable[str]) -> libginger.Tree:
    """Return a tree (that is a list of `Nodes`) from its
       [CoNNL-U string representation](http://universaldependencies.org/format.html)."""
    root = libginger.Node(identifier=0, form='ROOT')
    res = [root]
    # First get the self-contained values, deal with references later
    # IMPLEMENTATION: This relies on references being initialisable
    #                 with identifiers
    for i, line in enumerate(l.strip() for l in tree_str):
        # Skip comment lines
        if line.startswith('#'):
            next

        try:
            identifier, form, lemma, upostag, xpostag, feats, head, deprel, deps, misc = line.split('\t')
        except ValueError:
            # TODO: Issue a warning here
            raise libginger.ParsingError('At line {i} : 10 columns expected, got a {n} ({line!r})'.format(i=i, n=len(line.split('\t')), line=line))
        try:
            identifier = int(identifier)
        except ValueError:
            # TODO: Issue a warning here
            if re.match(r'\d+-\d+', identifier):  # Skip multiword tokens
                next
            if re.match(r'\d+.\d+', identifier):  # Skip empty nodes
                next
            raise libginger.ParsingError('At line {i} : the `id` field does not respect CoNLL-U specifications.'.format(i=i))

        try:
            feats = dict() if feats == '_' else dict(e.split('=') for e in feats.split('|'))
        except ValueError:
            # Be nice : if empty, it should be an underscore, but let's be nice with spaces and empty strings, too
            if feats.isspace() or not feats:
                # TODO: Issue a warning here
                feats = dict()
            else:
                raise libginger.ParsingError('At line {i} : the `feats` field does not respect CoNLL-U specifications.'.format(i=i))

        try:
            head = int(head)
        except ValueError:
            raise libginger.ParsingError('At line {i} : the `head` field does not respect CoNLL-U specifications.'.format(i=i))

        try:
            deps = [] if deps == '_' else [e.split(':') for e in deps.split('|')]
        except ValueError as e:
            # Be nice : if empty, it should be an underscore, but let's be nice with spaces and empty strings, too
            if deps.isspace() or not deps:
                # TODO: Add a warning here
                deps = []
            else:
                raise libginger.ParsingError('At line {i} : the `deps` field does not respect CoNLL-U specifications.'.format(i=i))

        new_node = libginger.Node(identifier, form, lemma, upostag, xpostag, feats, head, deprel, deps, misc)
        res.append(new_node)

    # Now deal with references, which is easy, since the index of a node in
    # `res` is exactly its identifier
    for n in res[1:]:
        n.head = res[n.head]
        n.deps = [(res[head], dep) for head, dep in n.deps]

    return libginger.Tree(res)


def conllx(treebank_lst: ty.Iterable[str]) -> ty.Iterable[libginger.Tree]:
    '''Parse a CoNLL-X treebank file and return its trees.'''
    trees = trees_from_conll(treebank_lst)
    return (_conllx_tree(t) for t in trees)


def _conllx_tree(tree_lst: ty.Iterable[str]) -> libginger.Tree:
    """Create an Universal Dependencies tree from a CoNLL-X tree."""
    root = libginger.Node(identifier=0, form='ROOT')
    res = [root]
    conllx_to_conllu_identifers = {0: 0}

    for i, line in enumerate(l.strip() for l in tree_lst):
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


def conll2009_gold(treebank_lst: ty.Iterable[str]) -> ty.Iterable[libginger.Tree]:
    '''Parse a CoNLL-2009 gold treebank file and return its trees.'''
    trees = trees_from_conll(treebank_lst)
    return (_conll2009_gold_tree(t) for t in trees)


def _conll2009_gold_tree(tree_lst: ty.Iterable[str]) -> libginger.Tree:
    """Create an Universal Dependencies tree from a CoNLL-2009 tree.
       This takes only the gold columns into account

       The P-attributes and 'pred are stored in the `misc` attribute."""
    root = libginger.Node(identifier=0, form='ROOT')
    res = [root]
    conllx_to_conllu_identifers = {0: 0}

    for i, line in enumerate(l.strip() for l in tree_lst):
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


def conll2009_sys(treebank_lst: ty.Iterable[str]) -> ty.Iterable[libginger.Tree]:
    '''Parse a CoNLL-U treebank file and return its trees.'''
    trees = trees_from_conll(treebank_lst)
    return (_conll2009_sys_tree(t) for t in trees)


def _conll2009_sys_tree(tree_lst: ty.Iterable[str]) -> libginger.Tree:
    """Create an Universal Dependencies tree from a CoNLL-2009 tree.
       This takes only the predicted columns into account

       The gold attributes are stored in the `misc` attribute."""
    root = libginger.Node(identifier=0, form='ROOT')
    res = [root]
    conllx_to_conllu_identifers = {0: 0}

    for i, line in enumerate(l.strip() for l in tree_lst):
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
            if pfeat.isspace() or not pfeat:
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
            if head == '_' and deprel == '_':
                head, deprel = None, None
            else:
                raise libginger.ParsingError('At line {i} : the `head` field does not respect CoNLL-2009 specifications.'.format(i=i))

        # Deal with multi-token words
        tokens = list(re.findall(r'\w+|\S', form))
        # Deal with the first token
        real_identifier = len(res)
        conllx_to_conllu_identifers[identifier] = real_identifier
        res.append(libginger.Node(identifier=real_identifier, form=tokens[0],
                                  lemma=lemma, upostag=ppos, feats=feat,
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
    return '\n'.join(_node_to_conll2009_sys(n) for n in tree.nodes[1:])


def to_conllu(tree: libginger.Tree) -> str:
    """Return `tree` in CoNLL-U format."""
    return tree.to_conll()


# Parser-specific formats
def talismane(treebank_lst: ty.Iterable[str]) -> ty.Iterable[libginger.Tree]:
    '''Parse a CoNLL-U treebank file and return its trees.'''
    trees = trees_from_conll(treebank_lst)
    return (_talismane_tree(t) for t in trees)


def _talismane_tree(tree_str: ty.Iterable[str]) -> libginger.Tree:
    """Create an Universal Dependencies tree from a Talismane tree.

       Talismane outputs are essentially CoNLL-X files, with incompatible
       stylistic idiosyncrasies."""
    conllx_str = (s.replace(r'\|\t', r'\t') for s in tree_str)
    return _conllx_tree(conllx_str)


def dict_to_conll_map(d: ty.Dict) -> str:
    'Return the CoNLL standard description of a dict.'
    return '|'.join('{key}={val}'.format(key=key, val=val) for key, val in d.items())


# Guessing tools
def guess(filelines: ty.Iterable[str]) -> str:
    """Guess the format of a file. Return the name of the format in a way
       as a key in `formats`."""
    lines = iter(filelines)
    first_line_columns = next(l for l in lines if l).split('\t')

    if len(first_line_columns) == 10:  # 10 columns, assuming CoNLL-[XU] of some kind
        # CoNLL-X
        if not re.match(r'_|^([^:|]+:[^:|])(\|[^:|]+:[^:|])*$', first_line_columns[-2]):
            if any(l.split('\t')[5].endswith('|') for l in lines if l and not l.isspace()):
                return 'talismane'
            return 'conllx'
    elif len(first_line_columns) >= 14:  # 14 columns or more assume CoNLL-2009:
        if any(l.split('\t')[3] != '_' for l in lines if l and not l.isspace()):
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
