r"""A toolkit for [Universal Dependencies](http://universaldependencies.org)."""
import re

import typing as ty
import itertools as it


class ParsingError(Exception):
    pass


class Node:
    '''A node in an UD graph.'''
    def __init__(self,
                 identifier: int,
                 form: str =None,
                 lemma: str =None,
                 upostag: str =None,
                 xpostag: str =None,
                 feats: ty.Dict[str, str] =None,
                 head: 'Node' =None,
                 deprel: str =None,
                 deps: ty.List[ty.Tuple['Node', str]] =None,
                 misc: str =None):
        """See the [CoNLL-U](http://universaldependencies.org/format.html)
           specification for details on the fields.

           ## Deserialisation
             - References in `head` and `deps` are Python references
             - The root's head is `None`
             - `deps` is a Python list
             - `feats` is a Python dict
             - empty fields are either `None` or empty depending on the field type"""
        self.identifier = identifier
        self.form = form
        self.lemma = lemma
        self.upostag = upostag
        self.xpostag = xpostag
        self.feats = feats if feats is not None else dict()
        self.head = head
        self.deprel = deprel
        self.deps = deps if deps is not None else []
        self.misc = misc

    def to_conll(self) -> str:
        '''Return the CoNLL-U representation of the node.'''
        return '{identifier}\t{form}\t{lemma}\t{upostag}\t{xpostag}\t{feats}\t{head}\t{deprel}\t{deps}\t{misc}'.format(
            identifier='_' if self.identifier is None else self.identifier,
            form='_' if self.form is None else self.form,
            lemma='_' if self.lemma is None else self.lemma,
            upostag='_' if self.upostag is None else self.upostag,
            xpostag='_' if self.xpostag is None else self.xpostag,
            feats='|'.join('{feat}={value}'.format(feat=feat, value=value) for feat, value in self.feats.items()),
            head='_' if self.head is None else self.head.identifier,
            deprel='_' if self.deprel is None else self.deprel,
            deps='|'.join('{head}:{dep}'.format(head=head, dep=dep) for head, dep in self.deps),
            misc='_' if self.misc is not None else self.misc
        )

    def __repr__(self):
        return 'Node({identifier}, {form}, {lemma}, {upostag}, {xpostag}, {feats}, {head}, {deprel}, {deps}, {misc})'.format(
            identifier=self.identifier, form=self.form, lemma=self.lemma, upostag=self.upostag, xpostag=self.xpostag,
            feats=self.feats,
            head='None' if self.head is None else self.head.identifier,
            deprel=self.deprel,
            deps=list((h.identifier, r) for h, r in self.deps),
            misc=self.misc
        )


class Tree:
    '''A dependency tree. Conceptually just a list of nodes
       with some constraints:
           1. The nodes are sorted by identifier.
           2. The node identifier are connex integers.
           3. The nodes do not reference nodes that are not in the tree.
           4. The first node (indice 0) is a special root node
             - Its identifier must be 0.
             - Its form should be "ROOT".
             - All of its other attributes should be left empty.'''
    def __init__(self, nodes: ty.Iterable[Node]):
        '''Return a new tree whose nodes are those in `nodes`.

           The nodes should respect the constraints 2, 3 and 4 described in
           the docstring of `Tree`.'''
        self.nodes = sorted(nodes, key=lambda x: x.identifier)
        self.nodes.sort(key=lambda x: x.identifier)
        self.root = self.nodes[0]

    def descendance(self, root: Node, blacklist: ty.Iterable[str] =None) -> ty.List[Node]:
        """Extract the descendance of a node, does not perform any copy or
           reindexing.

           Use `blacklist` to forbid following certain relations."""

        blacklist = set() if blacklist is None else set(blacklist)  # Speed search up

        def aux(node):
            children = [n for n in self.nodes if n.head is node and n.deprel not in blacklist]
            d = it.chain.from_iterable(aux(c) for c in children)
            return it.chain([node], d)

        res = list(aux(root))
        return res

    def to_conll(self) -> str:
        '''Return a CoNLL-U representation of the tree.'''
        return '\n'.join(n.to_conll() for n in self.nodes[1:])

    def __str__(self):
        return '\n'.join(str(n) for n in self.nodes)
