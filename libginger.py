r"""A toolkit for [Universal Dependencies](http://universaldependencies.org)."""
import re

import typing as ty
import itertools as it


class ParsingError(Exception):
    pass


class Node:
    '''A node in an UD dependency graph.'''
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
             - `feats` is a Python dic
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

    def __repr__(self):
        return 'Node({identifier}, {form}, {lemma}, {upostag}, {xpostag}, {feats}, {head}, {deprel}, {deps}, {misc})'.format(
            identifier=self.identifier, form=self.form, lemma=self.lemma, upostag=self.upostag, xpostag=self.xpostag,
            feats=self.feats,
            head='None' if self.head is None else self.head.identifier,
            deprel=self.deprel,
            deps=self.deps,
            misc=self.misc
        )


class Tree:
    '''A dependency tree. Conceptually just a list of nodes
       with some constraints:
           1. The nodes are sorted by identifier.
           2. The node identifier are connexe integers.
           3. The nodes do not reference nodes that are not in the tree.
           4. The first node (indice 0) is a special root node
             - Its identifier must be 0.
             - Its form should be "ROOT".
             - All other attributes should be left empty.'''
    def __init__(self, nodes: ty.Iterable[Node]):
        '''Return a new tree whose nodes are those in `nodes`.

           Except for sorting, the nodes should respect the constraints 2, 3
           and 4 described in the docstring of `Tree`.'''
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

    def tikz(self) -> str:
        '''Return the TikZ code for a representation of the dependency tree.

           The resulting TikZ code use the `calc`, `positioning` and
           `shapes.multipart` libraries, make sure to include them
           with `\\usetikzlibrary`'''

        # Layout parameters
        token_node_distance = '1em'  # Horizontal distance between the token (word) nodes
        arrow_shift = '.3em'  # Horizontal padding between arrows
        energy = '0.5'  # In short : pointiness of the dependeny arrows. ∈ [0,+∞[

        # Nodes and path templates
        first_token_node_template = r'node[token] (t{index}) {{{form}\nodepart{{two}}{lemma}\nodepart{{three}}{upostag}}}'

        token_node_template = r'node[token, right={token_node_distance} of t{prev}] (t{index}) {{{form}\nodepart{{two}}{lemma}\nodepart{{three}}{upostag}}}'

        dep_template = r'\draw[->] ($(t{head}.north)+({direction}{arrow_shift}, 0)$) .. controls ($(t{head}.north)!{energy}!{direction}90:(t{foot}.north)$) and ($(t{foot}.north)!{energy}!{direction}270:(t{head}.north)$) .. (t{foot}.north) node[dep] {{{deprel}}};'

        root_template = r'\draw[->] ($(arcs.north west)!(t{root_index}.north)!(arcs.north east)$) node[root] {{root}} -- (t{root_index}.north);'

        # First the token nodes
        # We don't draw the root node as a normal node
        draw_nodes = self.nodes[1:]
        # Special case for the first node
        first_token = draw_nodes[0]
        token_nodes_lst = [first_token_node_template.format(index=first_token.identifier,
                                                            form=tex_escape(first_token.form),
                                                            lemma=tex_escape(first_token.lemma),
                                                            upostag=tex_escape(first_token.upostag))]
        # And now the rest
        token_nodes_lst += [token_node_template.format(token_node_distance=token_node_distance,
                                                       prev=p.identifier, index=c.identifier,
                                                       form=tex_escape(c.form),
                                                       lemma=tex_escape(c.lemma),
                                                       upostag=tex_escape(c.upostag))
                            for p, c in zip(draw_nodes, draw_nodes[1:])]
        token_nodes = '\n        '.join(token_nodes_lst)

        # Now the relations
        relations_lst = [dep_template.format(head=n.head.identifier, foot=n.identifier, deprel=tex_escape(n.deprel),
                                             energy=energy, arrow_shift=arrow_shift,
                                             direction='-' if n.head.identifier > n.identifier else '')
                         for n in draw_nodes if n.head.identifier != 0]
        dependencies = '\n        '.join(relations_lst)

        # And finally the roots
        root_lst = [root_template.format(root_index=n.identifier)
                    for n in draw_nodes if n.head.identifier == 0]
        roots = '\n        '.join(root_lst)
        res_template = (r'''
\begin{{tikzpicture}}[>=stealth, token/.style={{text height=1em, rectangle split, rectangle split parts=3}},
                               dep/.style={{font=\small\itshape, midway, above=-.2em}},
                               root/.style={{font=\small\itshape, above}}]
    \path[anchor=base]
        {token_nodes};
    \begin{{scope}}[local bounding box=arcs]
        {dependencies}
    \end{{scope}}

    {roots}
\end{{tikzpicture}}''')[1:]  # Stupid trick for nice display
        return res_template.format(token_nodes=token_nodes,
                                   dependencies=dependencies,
                                   roots=roots)

    # TODO: This (the code) could probably be prettier
    # TODO: For extra display prettiness, a node should be able to have both a forward and a backward outgoing arrow
    #       at the same level. Same for nodes that have an incoming and an outgoig backward (resp. forward) arrow
    #       (Possibly too tricky to code wrt the benefits)
    def ascii_art(self) -> str:
        '''Return an ASCII-art representation of the dependency tree.

           Only the relations, not the relation types (that would make it prohibitively large).

           ## Example
           (only the result)
           ```
                     │
                     │┌─────────────────────────────────────────────────────────────────────────┐
                     │├─────────────────────┐                                                   │
                     ││                     │                  ┌───────────────────┐            │
                     │├─────────┐           │                  │      ┌────────────│┐           │
                     ││         │           │┌────────┐        │      │            ││           │┌───────┐
           ┌─────────│┤   ┌─────│┐      ┌───│┤        │┌──────┐│      │        ┌───│┤     ┌─────│┤       │┌─┐
           ↓         ↓│   ↓     ↓│      ↓   ↓│        ↓│      ↓│      ↓        ↓   ↓│     ↓     ↓│       ↓│ ↓
           première  est  bien  simple  je  voudrais  savoir  depuis  combien  de  temps  vous  habitez  à  Orléans
          ````'''
        res = ['  '.join(t.form for t in self.nodes)]  # Two space to be able to deal with single-letter tokens

        # The first line above the words is easy: only arrow heads (every word) anb butts (for non-leaves)
        # Arrow heads are over the first character (because every token has at least one)
        # Arrow butts (if existent) are over the second, or, inthe case of single-letter tokens, over the first
        # following space.
        # This part could be integrated with the rest of the code (using `relations`) but let's keep it here
        # to keep the rest (c)leaner.
        arrow_ends = []
        for t in self.nodes:
            arrow_ends.append('↓')
            if any(u for u in self.nodes if u.head is t):
                arrow_ends.append('│')
            else:
                arrow_ends.append(' ')
            # Spaces over the rest of the token, plus the double space
            # before the next one. Single space in case of single-letter
            # token. And it works !
            arrow_ends.append(' '*len(t.form))
        res.append(''.join(arrow_ends))

        # And now for the real trouble
        # For future reference : the idea is that we proceed relation by relation, from left to right
        # starting with those with the sortest distance (number of tokens) between the origin and the
        # destination.
        # First get the relations with their real index in this tree instead of the identifier
        # (which might have an arbitrary start, or worse, be non-connex if this was an extracted subtree)
        relations = [(i, self.nodes.index(n.head)) for i, n in enumerate(self.nodes) if n.head in self.nodes]

        relations.sort(key=lambda x: (abs(x[0]-x[1]), min(x)))
        # Then a counter of unfinished incoming arrows. There shouldn't ever be more than one
        # but it doesn't hurt to allow for more (not necessarily supported in the rest of the code)
        # Note that roots will always have an unfinished incoming arrow
        in_open = [1]*len(self.nodes)
        # And a counter of unfinished outgoing arrows
        out_open = [0]*len(self.nodes)
        for _, h in relations:
            out_open[h] += 1

        current_token = 0
        current_line = []

        def fill_until(index, fill_char):
            '''Go from `current_token` to `index`, filling blanks with `fill_char` and
               inserting the appropriate verticals.'''
            for i, t in enumerate(self.nodes[current_token:index], start=current_token):
                current_line.append('│' if in_open[i] else fill_char)
                current_line.append('│' if out_open[i] else fill_char)
                current_line.append(fill_char*len(t.form))

        while relations:
            # Get the next non-crossing relation on this line
            index, current_relation = next(((i, r) for i, r in enumerate(relations) if min(r) >= current_token),
                                           (None, None))
            if index is None:  # None such relation : fill with spaces and go to next line
                fill_until(len(self.nodes), ' ')
                # Flush
                res.append(''.join(current_line))
                current_token = 0
                current_line = []
            else:
                del relations[index]
                first, last = min(current_relation), max(current_relation)
                # Flag to know the direction of the relation
                backward = current_relation[0] < current_relation[1]
                fill_until(first, ' ')  # Get to the first token
                # And handle it
                current_line.append('┌' if backward else '│' if in_open[first] else ' ')
                current_line.append('┌' if not backward and out_open[first] == 1 else
                                    '├' if not backward else
                                    '│' if out_open[first] else '─')
                current_line.append('─'*len(self.nodes[first].form))
                current_token = first + 1

                fill_until(last, '─')  # Go to the last token
                # And handle it
                current_line.append('┐' if not backward else '│' if in_open[last] else '─')
                current_line.append('┐' if backward and out_open[last] == 1 else
                                    '┤' if backward else
                                    '│' if out_open[last] else ' ')
                current_line.append(' '*len(self.nodes[last].form))
                current_token = last + 1

                # Update the open relations registers
                in_open[current_relation[0]] -= 1
                out_open[current_relation[1]] -= 1

        # Flush an eventual last line
        if current_line:
            fill_until(len(self.nodes), ' ')
            res.append(''.join(current_line))
            current_line = []
            current_token = 0
        # And add a last one for eventual root nodes
        if any(in_open):
            fill_until(len(self.nodes), ' ')
            res.append(''.join(current_line))

        return '\n'.join(res[::-1])

    def __str__(self):
        return '\n'.join(str(n) for n in self.nodes)

    # TODO: Add a way to deal with the caveats
    @classmethod
    def from_conll(cls, conll_str: str):
        """Return a tree (that is a list of `Nodes`) from its
           [CoNNL-U string representation](http://universaldependencies.org/format.html).

           ## Caveats
             - Empty nodes are skipped"""
        root = Node(identifier=0, form='ROOT')
        res = [root]
        # First get the self-contained values, deal with references later
        # IMPLEMENTATION: This relies on references being initialisable
        #                 with identifiers
        for i, l in enumerate(l.strip() for l in conll_str.splitlines()):
            # Skip comment lines
            if l.startswith('#'):
                next
            identifier, form, lemma, upostag, xpostag, feats, head, deprel, deps, misc = l.split('\t')
            try:
                identifier = int(identifier)
            except ValueError:
                # TODO: Issue a warning here
                if re.match(r'\d+-\d+', identifier):  # Skip multiword tokens
                    next
                if re.match(r'\d+.\d+', identifier):  # Skip empty nodes
                    next
                raise ParsingError('At line {i} : the `id` field does not respect CoNLL-U specifications.'.format(i=i))

            try:
                feats = dict() if feats == '_' else dict(e.split('=') for e in feats[:-1].split('|'))
            except ValueError:
                # Be nice : if empty, it should be an underscore, but let's be nice with spaces and empty strings, too
                if feats.isspace() or not feats:
                    # TODO: Issue a warning here
                    feats = dict()
                else:
                    raise ParsingError('At line {i} : the `feats` field does not respect CoNLL-U specifications.'.format(i=i))

            try:
                head = int(head)
            except ValueError:
                raise ParsingError('At line {i} : the `head` field does not respect CoNLL-U specifications.'.format(i=i))

            try:
                deps = [] if deps == '_' else [e.split(':') for e in deps.split('|')]
            except ValueError as e:
                # Be nice : if empty, it should be an underscore, but let's be nice with spaces and empty strings, too
                if deps.isspace() or not deps:
                    # TODO: Add a warning here
                    deps = []
                else:
                    raise ParsingError('At line {i} : the `deps` field does not respect CoNLL-U specifications.'.format(i=i))

            new_node = Node(identifier, form, lemma, upostag, xpostag, feats, head, deprel, deps, misc)
            res.append(new_node)

        # Now deal with references, which is easy, since the index of a node in
        # `res` is exactly its identifier
        for n in res[1:]:
            n.head = res[n.head]
            n.deps = [(res[head], dep) for head, dep in n.deps]

        return cls(res)


def tex_escape(text: str) -> str:
    """Thanks [Mark](http://stackoverflow.com/a/25875504/760767)"""
    conv = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\^{}',
        '\\': r'\textbackslash{}',
        '<': r'\textless',
        '>': r'\textgreater',
    }
    regex = re.compile('|'.join(re.escape(key) for key in conv.keys()))
    return regex.sub(lambda match: conv[match.group()], text)
