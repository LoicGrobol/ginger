"""Conversion from various treebank formats to CoNLL-U and back again.

A lot of the code comes from Kim Gerdes' [arborator][1], either directly
or through rewriting. Many thanks to him!

[1]: https://github.com/kimgerdes/arborator"""

import typing as ty
import re

try:
    from . import libginger
except ImportError:
    from ginger import libginger


class ParsingError(Exception):
    pass


class PlaceholderNode(libginger.UDNode):
    '''A Node that serves as a placeholder for a Node that has not been created yet.'''
    def __init__(self, identifier):
        self.identifier = identifier


def trees_from_conll(lines_lst: ty.Iterable[str]) -> ty.Iterable[str]:
    '''Extract individual tree strings from the lines of a CoNLL-like file.'''
    current = []  # type: ty.List[str]
    for line in lines_lst:
        # Skip comment lines
        if line.startswith('#'):
            continue
        elif line.isspace():
            if current:
                yield current
                current = []
            continue
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


def to_conllu(tree: libginger.Tree) -> str:
    """Return `tree` in CoNLL-U format."""
    return tree.to_conll()


def _conllu_tree(tree_lines_lst: ty.Iterable[str]) -> libginger.Tree:
    """Return a tree (that is a list of `Nodes`) from its
       [CoNNL-U string representation](http://universaldependencies.org/format.html)."""
    root = libginger.Node(identifier=0, form='ROOT')
    res = [root]
    full_nodes = [root]  # Efficient storage of referenceable nodes for faster retrival
    # First get the self-contained values, deal with references later
    # IMPLEMENTATION: This relies on references being initialisable with identifiers instead of
    #                 actual references. If we  want to avoid it, we could initialise with `None`
    #                 placeholders, store the identifiers somewhere else, then build the references

    for i, line in enumerate(l.strip() for l in tree_lines_lst):
        # Skip comment lines
        if line.startswith('#'):
            continue

        try:
            (identifier, form, lemma, upostag, xpostag, feats,
             head, deprel, deps, misc) = line.split('\t')
        except ValueError:
            raise ParsingError(
                'At line {i} : 10 columns expected, got {n} ({line!r})'.format(
                    i=i, n=len(line.split('\t')), line=line))

        # Deal with multi-word tokens
        if not identifier.isnumeric() and re.match(r'\d+-\d+', identifier):
            a, b = identifier.split('-')
            new_node = libginger.MultiTokenNode((PlaceholderNode(i)
                                                 for i in range(int(a), int(b)+1)), form)
        else:
            try:
                identifier = _parse_conll_identifier(identifier, i, 'ID', non_zero=True)
            except ValueError:
                # TODO: Issue a warning here
                if re.match(r'\d+.\d+', identifier):  # Skip empty nodes
                    continue
                raise _parse_error_except(i, 'ID', 'CoNLL-U', identifier)

            try:
                feats = conll_map_to_dict(feats)
            except ParsingError:
                raise _parse_error_except(i, 'FEATS', 'CoNLL-U', feats)

            try:
                head = _parse_conll_identifier(head, i, 'HEAD')
            except ValueError:
                raise _parse_error_except(i, 'HEAD', 'CoNLL-U', head)

            try:
                deps = [] if deps == '_' else [e.split(':') for e in deps.split('|')]
            except ValueError as e:
                raise _parse_error_except(i, 'DEPS', 'CoNLL-U', deps)

            new_node = libginger.Node(identifier, form, lemma, upostag, xpostag, feats,
                                      head, deprel, deps, misc)
            full_nodes.append(new_node)
        res.append(new_node)

    # Now deal with references
    for node in res[1:]:
        if isinstance(node, libginger.MultiTokenNode):
            node.span = [full_nodes[placeholder.identifier] for placeholder in node.span]
        else:
            node.head = full_nodes[node.head]
            node.deps = [(next(n for n in res if n.identifier == head), dep)
                         for head, dep in node.deps]

    return libginger.Tree(res)


def conllx(treebank_lst: ty.Iterable[str]) -> ty.Iterable[libginger.Tree]:
    '''Parse a CoNLL-X treebank file and return its trees.'''
    trees = trees_from_conll(treebank_lst)
    return (_conllx_tree(t) for t in trees)


def _conllx_tree(tree_lst: ty.Iterable[str]) -> libginger.Tree:
    """Create an Universal Dependencies tree from a CoNLL-X tree."""
    root = libginger.Node(identifier=0, form='ROOT')
    res = [root]
    conllx_to_conllu_identifiers = {0: 0}

    for i, line in enumerate(l.strip() for l in tree_lst):
        # Skip comment lines
        if line.startswith('#'):
            continue

        try:
            (identifier, form, lemma, upostag, xpostag, feats,
             head, deprel, phead, pdeprel) = line.split('\t')
        except ValueError:
            # TODO: Issue a warning here
            raise ParsingError(
                'At line {i} : 10 columns expected, got {n} ({line!r})'.format(
                    i=i, n=len(line.split('\t')), line=line))

        try:
            identifier = _parse_conll_identifier(identifier, i, 'ID', non_zero=True)
        except ValueError:
            raise _parse_error_except(i, 'ID', 'CoNLL-X', identifier)

        lemma = re.sub(r'\s', '_', lemma)

        try:
            feats = conll_map_to_dict(feats)
        except ParsingError:
            # Be nice : if empty, it should be an underscore, but let's be nice with spaces and
            # empty strings, too
            if feats.isspace() or not feats:
                # TODO: Issue a warning here
                feats = dict()
            else:
                raise _parse_error_except(i, 'FEATS', 'CoNLL-X', feats)

        try:
            head = _parse_conll_identifier(head, i, 'HEAD')
        except ValueError:
            raise _parse_error_except(i, 'HEAD', 'CoNLL-X', head)

        try:
            phead = _parse_conll_identifier(phead, i, 'PHEAD')
        except ValueError:
            if phead == '_':
                phead, pdeprel = None, None
            else:
                raise _parse_error_except(i, 'PHEAD', 'CoNLL-X', phead)

        # Deal with multi-token words
        tokens = list(re.findall(r'\w+|\S', form))
        # Deal with the first token
        real_identifier = len(res)
        conllx_to_conllu_identifiers[identifier] = real_identifier
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
        n.head = res[conllx_to_conllu_identifiers[n.head]]
        n.deps = [(res[conllx_to_conllu_identifiers[head]], deprel) for head, deprel in n.deps]

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
    conllx_to_conllu_identifiers = {0: 0}

    for i, line in enumerate(l.strip() for l in tree_lst):
        # Skip comment lines
        if line.startswith('#'):
            continue

        try:
            (identifier, form, lemma, plemma, pos, ppos, feat, pfeat, head, phead, deprel, pdeprel,
             fillpred, pred, *apreds) = line.split('\t')
        except ValueError:
            # TODO: Issue a warning here
            raise ParsingError(
                'At line {i} : at least 14 columns expected, got {n} ({line!r})'.format(
                    i=i, n=len(line.split('\t')), line=line))

        try:
            identifier = _parse_conll_identifier(identifier, i, 'ID', non_zero=True)
        except ValueError:
            raise _parse_error_except(i, 'ID', 'CoNLL-2009', identifier)

        lemma = re.sub(r'\s', '_', lemma)

        try:
            feat = conll_map_to_dict(feat)
        except ValueError:
            # Be nice : if empty, it should be an underscore, but let's be nice with spaces and
            # empty strings, too
            if feat.isspace() or not feat:
                # TODO: Issue a warning here
                feat = dict()
            else:
                raise _parse_error_except(i, 'FEAT', 'CoNLL-2009', feat)

        try:
            head = _parse_conll_identifier(head, i, 'HEAD')
        except ValueError:
            raise _parse_error_except(i, 'HEAD', 'CoNLL-2009', head)

        try:
            phead = _parse_conll_identifier(phead, i, 'PHEAD')
        except ValueError:
            if phead == '_':
                phead, pdeprel = None, None
            else:
                raise _parse_error_except(i, 'PHEAD', 'CoNLL-2009', phead)

        # Deal with multi-token words
        tokens = list(re.findall(r'\w+|\S', form))
        # Deal with the first token
        real_identifier = len(res)
        conllx_to_conllu_identifiers[identifier] = real_identifier
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
            res.append(libginger.Node(identifier=len(res), form=t, head=identifier,
                                      deprel='fixed'))

    # Now that we have a `Node` for every node,& let's do the linking
    for n in res[1:]:
        n.head = res[conllx_to_conllu_identifiers[n.head]]
        n.deps = [(res[conllx_to_conllu_identifiers[head]], deprel) for head, deprel in n.deps]

    return libginger.Tree(res)


def _node_to_conll2009_gold(node: libginger.Node):
    '''Return CoNLL-2009 representation of a `Node`.
       This writes the informations in the gold columns only.'''
    return '{identifier}\t{form}\t{lemma}\t_\t{upostag}\t_\t{feats}\t_\t{head}\t_\t{deprel}\t_\t_\t_\t_'.format(
        identifier='_' if node.identifier is None else node.identifier,
        form='_' if node.form is None else node.form,
        lemma='_' if node.lemma is None else node.lemma,
        upostag='_' if node.upostag is None else node.upostag,
        feats=dict_to_conll_map(node.feats),
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
    conllx_to_conllu_identifiers = {0: 0}

    for i, line in enumerate(l.strip() for l in tree_lst):
        # Skip comment lines
        if line.startswith('#'):
            continue

        try:
            (identifier, form, lemma, plemma, pos, ppos, feat, pfeat,
             head, phead, deprel, pdeprel, fillpred, pred, *apreds) = line.split('\t')
        except ValueError:
            raise ParsingError(
                'At line {i} : at least 14 columns expected, got {n} ({line!r})'.format(
                    i=i, n=len(line.split('\t')), line=line))
        try:
            identifier = _parse_conll_identifier(identifier, i, 'ID', non_zero=True)
        except ValueError:
            raise _parse_error_except(i, 'ID', 'CoNLL-2009', identifier)

        plemma = re.sub(r'\s', '_', plemma)

        try:
            pfeat = conll_map_to_dict(pfeat)
        except ValueError:
            # Be nice : if empty, it should be an underscore, but let's be nice with spaces and
            # empty strings, too
            if pfeat.isspace() or not pfeat:
                # TODO: Issue a warning here
                pfeat = dict()
            else:
                raise _parse_error_except(i, 'PFEAT', 'CoNLL-2009', pfeat)

        try:
            phead = _parse_conll_identifier(phead, i, 'PHEAD')
        except ValueError:
            raise _parse_error_except(i, 'PHEAD', 'CoNLL-2009', phead)

        try:
            head = _parse_conll_identifier(head, i, 'HEAD')
        except ValueError:
            if head == '_':
                head, deprel = None, None
            else:
                raise _parse_error_except(i, 'HEAD', 'CoNLL-2009', head)

        # Deal with multi-token words
        tokens = list(re.findall(r'\w+|\S', form))
        # Deal with the first token
        real_identifier = len(res)
        conllx_to_conllu_identifiers[identifier] = real_identifier
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
        n.head = res[conllx_to_conllu_identifiers[n.head]]
        n.deps = [(res[conllx_to_conllu_identifiers[head]], deprel) for head, deprel in n.deps]

    return libginger.Tree(res)


def _node_to_conll2009_sys(node: libginger.Node):
    '''Return CoNLL-2009 representation of a `Node`.
       This writes the informations in the pred columns only.'''
    return '{identifier}\t{form}\t_\t{lemma}\t_\t{upostag}\t_\t{feats}\t_\t{head}\t_\t{deprel}\t_\t_\t_'.format(
        identifier='_' if node.identifier is None else node.identifier,
        form='_' if node.form is None else node.form,
        lemma='_' if node.lemma is None else node.lemma,
        upostag='_' if node.upostag is None else node.upostag,
        feats=dict_to_conll_map(node.feats),
        head='_' if node.head is None else node.head.identifier,
        deprel='_' if node.deprel is None else node.deprel,
    )


def to_conll2009_sys(tree: libginger.Tree) -> str:
    '''Return a CoNLL-2009 representation of the tree.'''
    return '\n'.join(_node_to_conll2009_sys(n) for n in tree.nodes[1:])


# Parser-specific formats
def talismane(treebank_lst: ty.Iterable[str]) -> ty.Iterable[libginger.Tree]:
    '''Parse a CoNLL-U treebank file and return its trees.'''
    trees = trees_from_conll(treebank_lst)
    return (_talismane_tree(t) for t in trees)


def _talismane_tree(tree_str: ty.Iterable[str]) -> libginger.Tree:
    """Create an Universal Dependencies tree from a Talismane tree.

       Talismane outputs are essentially CoNLL-X files, with incompatible
       stylistic idiosyncrasies."""
    conllx_str = [s.replace('|\t', '\t') for s in tree_str]
    return _conllx_tree(conllx_str)


# Utilities
def dict_to_conll_map(d: ty.Dict, *, pair_separator='|', keyval_separator='=') -> str:
    '''Return the CoNLL standard description of a mapping, that is `|`-separated `key=value` pairs.
       Return `"_"` if `d` is empty.

       Custom separators may be specified.'''
    if not d:
        return '_'
    return pair_separator.join('{key}{keyval_separator}{val}'.format(
        key=key, val=val, keyval_separator=keyval_separator)
                               for key, val in d.items())


def conll_map_to_dict(conll_map: str, *, pair_separator='|', keyval_separator='=') -> ty.Dict:
    '''Parse the CoNLL map format of `|`-separated `key=value` pairs.
       Return an empty dict if `conll_map` is `_`, a per the standard.

       Custom separators may be specified.'''
    if conll_map == '_':
        return dict()
    try:
        return dict(e.split(keyval_separator) for e in conll_map.split(pair_separator))
    except ValueError:
        raise ParsingError('Wrong CoNLL map format : {conll_map!r}'.format(
            conll_map=conll_map
        ))


def _parse_error_except(line: int, field: str, form: str, content: str) -> ParsingError:
    '''Return a `Parsing error with the message in the usual format.`'''
    message = ('At line {line},'
               'the `{field}` field does not respect {form} specifications : {content!r}').format(
                   line=line, field=field, form=form, content=content
               )
    return ParsingError(message)


def _parse_conll_identifier(value: str, line: int, field: str, *,
                            non_zero=False) -> int:
    '''Parse a CoNLL token identifier, raise the appropriate exception if it is invalid.
       Just propage the exception if `value` does not parse to an integer.

       If `non_zero` is truthy, raise an exception if `value` is zero.
       `field` and `line` are only used for the error message.'''
    res = int(value)
    if res < 0:
        raise ValueError(
            'At line {line}, the `{field}` field must be a non-negative integer, got {value!r}'.format(
                line=line, field=field, value=value))
    elif non_zero and res == 0:
        raise ValueError(
            'At line {line}, the `{field}` field must be a positive integer, got {value!r}'.format(
                line=line, field=field, value=value))
    return res


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
