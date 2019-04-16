r"""A toolkit for [Universal Dependencies](http://universaldependencies.org)."""
# TODO: refactor the data model
import typing as ty
import itertools as it


class UDNode:
    """A generic for UD nodes (full, multi-token and empty)."""

    def __init__(self, identifier, misc: str = None):
        self.identifier = identifier
        self.misc = misc

    @property
    def space_after(self) -> bool:
        return not (self.misc and "SpaceAfter=No" in self.misc)


class Node(UDNode):
    """A full node in an UD graph."""

    def __init__(
        self,
        identifier: int,
        form: ty.Optional[str] = None,
        lemma: ty.Optional[str] = None,
        upostag: ty.Optional[str] = None,
        xpostag: ty.Optional[str] = None,
        feats: ty.Dict[str, str] = None,
        head: ty.Optional["Node"] = None,
        deprel: ty.Optional[str] = None,
        deps: ty.Iterable[ty.Tuple["Node", ty.Optional[str]]] = None,
        misc: ty.Optional[str] = None,
    ):
        """See the [CoNLL-U](http://universaldependencies.org/format.html)
           specification for details on the fields.

           ## Deserialisation
             - References in `head` and `deps` are Python references
             - The root's head is `None`
             - `deps` is a Python list
             - `feats` is a Python dict
             - empty fields are either `None` or empty depending on the field type"""
        super().__init__(identifier, misc)
        self.form = form
        self.lemma = lemma
        self.upostag = upostag
        self.xpostag = xpostag
        self.feats = feats if feats is not None else dict()
        self.head = head
        self.deprel = deprel
        self.deps = list(deps) if deps is not None else []

    def to_conll(self) -> str:
        """Return the CoNLL-U representation of the node."""
        return (
            "{identifier}\t{form}\t{lemma}\t{upostag}\t{xpostag}\t{feats}"
            "\t{head}\t{deprel}\t{deps}\t{misc}"
        ).format(
            identifier=self.identifier,
            form="_" if self.form is None else self.form,
            lemma="_" if self.lemma is None else self.lemma,
            upostag="_" if self.upostag is None else self.upostag,
            xpostag="_" if self.xpostag is None else self.xpostag,
            feats="_"
            if not self.feats
            else "|".join(
                "{feat}={value}".format(feat=feat, value=value)
                for feat, value in self.feats.items()
            ),
            head="_" if self.head is None else self.head.identifier,
            deprel="_" if self.deprel is None else self.deprel,
            deps="_"
            if not self.deps
            else "|".join(
                "{head}:{dep}".format(head=head, dep=dep) for head, dep in self.deps
            ),
            misc="_" if self.misc is None else self.misc,
        )

    def __repr__(self):
        return (
            "Node({identifier}, {form}, {lemma}, {upostag}, {xpostag},"
            "{feats}, {head}, {deprel}, {deps}, {misc})"
        ).format(
            identifier=self.identifier,
            form=self.form,
            lemma=self.lemma,
            upostag=self.upostag,
            xpostag=self.xpostag,
            feats=self.feats,
            head="None" if self.head is None else self.head.identifier,
            deprel=self.deprel,
            deps=list((h.identifier, r) for h, r in self.deps),
            misc=self.misc,
        )


class MultiTokenNode(UDNode):
    """A node in a UD that represent a compound othographic form that
       spans several words.

         - `span` **must** be an iterable over **connex** `Node`s."""

    def __init__(self, span: ty.Iterable[UDNode], form: str = None, misc: str = None):
        self.span = list(span)
        self.form = form
        self.start = self.span[0].identifier
        self.end = self.span[-1].identifier
        identifier = "{start}-{end}".format(start=self.start, end=self.end)
        super().__init__(identifier, misc)

    def to_conll(self) -> str:
        """Return the CoNLL-U representation of the node"""
        return "{identifier}\t{form}\t_\t_\t_\t_\t_\t_\t_\t{misc}".format(
            identifier=self.identifier,
            form="_" if self.form is None else self.form,
            misc="_" if self.misc is None else self.misc,
        )

    def __repr__(self):
        return "MultiTokenNode({span}, {form})".format(
            span=[n.identifier for n in self.span],
            form="_" if self.form is None else self.form,
        )


class Tree:
    """A dependency tree. Conceptually just a list of nodes
       with some constraints:
           1. The nodes are sorted as in
              [the CoNLL-U specification](http://universaldependencies.org/format.html)
           2. The nodes do not reference nodes that are not in the tree.
           3. The first node (indice 0) is a special root node
             - Its identifier must be 0.
             - Its form should be "ROOT".
             - All of its other attributes should be left empty."""

    def __init__(
        self, nodes: ty.Iterable[UDNode], sent_id: str = None, text: str = None
    ):
        """Return a new tree whose nodes are those in `nodes`.

           The nodes should respect the constraints 1 through 3 described in
           the docstring of `Tree`."""
        self.all_nodes = list(nodes)
        self.word_sequence: ty.List[Node] = [
            n for n in self.all_nodes[1:] if isinstance(n, Node)
        ]
        self.nodes = self.word_sequence
        self.root = self.all_nodes[0]
        self.sent_id = sent_id
        self.text = text

    @property
    def raw_token_sequence(self) -> ty.Iterable[UDNode]:
        """Return the orthographic token sequence as described in
           [the CoNLL-U specification][1].

           [1]: http://universaldependencies.org/format.html#words-tokens-and-empty-nodes
           """
        current_span = []
        for node in self.all_nodes[1:]:
            if node in current_span:
                continue
            elif isinstance(node, MultiTokenNode):
                current_span = node.span
            yield node

    def descendance(
        self, root: Node, blacklist: ty.Iterable[str] = None
    ) -> ty.List[Node]:
        """Extract the descendance of a node, does not perform any copy or
           reindexing.

           Use `blacklist` to forbid following certain relations."""

        blacklist = set() if blacklist is None else set(blacklist)  # Speed search up

        def aux(node):
            children = [
                n for n in self.nodes if n.head is node and n.deprel not in blacklist
            ]
            d = it.chain.from_iterable(aux(c) for c in children)
            return it.chain([node], d)

        res = sorted(aux(root), key=lambda x: x.identifier)
        return res

    def to_conll(self) -> str:
        """Return a CoNLL-U representation of the tree."""
        return "\n".join(n.to_conll() for n in self.all_nodes[1:])

    def __str__(self):
        return "\n".join(str(n) for n in self.all_nodes)
