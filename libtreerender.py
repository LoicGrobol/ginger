"""Graphical rendering of `libginger` trees."""

import re

try:
    from . import libginger
except ImportError:
    from ginger import libginger


def tikz(tree: libginger.Tree) -> str:
    '''Return the TikZ code for a representation of a dependency tree.

       The resulting TikZ code use the `calc`, `positioning` and
       `shapes.multipart` libraries, make sure to include them
       with `\\usetikzlibrary`'''

    # Layout parameters
    token_node_distance = '1em'  # Horizontal distance between the token (word) nodes
    arrow_shift = '.3em'  # Horizontal padding between arrows
    energy = '0.5'  # In short : pointiness of the dependency arrows. ∈ [0,+∞[

    # Nodes and path templates
    first_token_node_template = r'node[token] (t{index}) {{{form}\nodepart{{two}}{lemma}\nodepart{{three}}{upostag}}}'

    token_node_template = r'node[token, right={token_node_distance} of t{prev}] (t{index}) {{{form}\nodepart{{two}}{lemma}\nodepart{{three}}{upostag}}}'

    dep_template = r'\draw[->] ($(t{head}.north)+({direction}{arrow_shift}, 0)$) .. controls ($(t{head}.north)!{energy}!{direction}90:(t{foot}.north)$) and ($(t{foot}.north)!{energy}!{direction}270:(t{head}.north)$) .. (t{foot}.north) node[dep] {{{deprel}}};'

    root_template = r'\draw[->] ($(arcs.north west)!(t{root_index}.north)!(arcs.north east)$) node[root] {{root}} -- (t{root_index}.north);'

    # First the token nodes
    # We don't draw the root node as a normal node
    draw_nodes = tree.nodes[1:]
    # Special case for the first node
    first_token = draw_nodes[0]
    token_nodes_lst = [first_token_node_template.format(
        index=first_token.identifier,
        form=tex_escape('_' if first_token.form is None else first_token.form),
        lemma=tex_escape('_' if first_token.lemma is None else first_token.lemma),
        upostag=tex_escape('_' if first_token.upostag is None else first_token.upostag))]
    # And now the rest
    token_nodes_lst += [token_node_template.format(
        token_node_distance=token_node_distance,
        prev=p.identifier, index=c.identifier,
        form=tex_escape('_' if c.form is None else c.form),
        lemma=tex_escape('_' if c.lemma is None else c.lemma),
        upostag=tex_escape('_' if c.upostag is None else c.upostag))
                        for p, c in zip(draw_nodes, draw_nodes[1:])]
    token_nodes = '\n        '.join(token_nodes_lst)

    # Now the relations
    relations_lst = [dep_template.format(head=n.head.identifier,
                                         foot=n.identifier,
                                         deprel=tex_escape(n.deprel),
                                         energy=energy,
                                         arrow_shift=arrow_shift,
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
\end{{tikzpicture}}''')[1:]  # Stupid trick for nice(r) display
    return res_template.format(token_nodes=token_nodes,
                               dependencies=dependencies,
                               roots=roots)


# TODO: This (the code) could probably be prettier
# TODO: For extra display prettiness, a node should be able to have both a forward and a backward outgoing arrow
#       at the same level. Same for nodes that have an incoming and an outgoig backward (resp. forward) arrow
#       (Possibly too tricky to code wrt the benefits)
def ascii_art(tree: libginger.Tree) -> str:
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
    res = ['  '.join(t.form for t in tree.nodes)]  # Two space to be able to deal with single-letter tokens

    # The first line above the words is easy: only arrow heads (every word) and butts (for non-leaves)
    # Arrow heads are over the first character (because every token has at least one)
    # Arrow butts (if existent) are over the second, or, inthe case of single-letter tokens, over the first
    # following space.
    # This part could be integrated with the rest of the code (using `relations`) but let's keep it here
    # to keep the rest (c)leaner.
    arrow_ends = []
    for t in tree.nodes:
        arrow_ends.append('↓')
        if any(u for u in tree.nodes if u.head is t):
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
    relations = [(i, tree.nodes.index(n.head)) for i, n in enumerate(tree.nodes)
                 if n.head in tree.nodes]

    relations.sort(key=lambda x: (abs(x[0]-x[1]), min(x)))
    # Then a counter of unfinished incoming arrows. There shouldn't ever be more than one
    # but it doesn't hurt to allow for more (not necessarily supported in the rest of the code)
    # Note that roots will always have an unfinished incoming arrow
    in_open = [1]*len(tree.nodes)
    # And a counter of unfinished outgoing arrows
    out_open = [0]*len(tree.nodes)
    for _, h in relations:
        out_open[h] += 1

    current_token = 0
    current_line = []

    def fill_until(index, fill_char):
        '''Go from `current_token` to `index`, filling blanks with `fill_char` and
           inserting the appropriate verticals.'''
        for i, t in enumerate(tree.nodes[current_token:index], start=current_token):
            current_line.append('│' if in_open[i] else fill_char)
            current_line.append('│' if out_open[i] else fill_char)
            current_line.append(fill_char*len(t.form))

    while relations:
        # Get the next non-crossing relation on this line
        index, current_relation = next(((i, r) for i, r in enumerate(relations)
                                        if min(r) >= current_token),
                                       (None, None))
        if index is None:  # None such relation : fill with spaces and go to next line
            fill_until(len(tree.nodes), ' ')
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
            current_line.append('─'*len(tree.nodes[first].form))
            current_token = first + 1

            fill_until(last, '─')  # Go to the last token
            # And handle it
            current_line.append('┐' if not backward else '│' if in_open[last] else '─')
            current_line.append('┐' if backward and out_open[last] == 1 else
                                '┤' if backward else
                                '│' if out_open[last] else ' ')
            current_line.append(' '*len(tree.nodes[last].form))
            current_token = last + 1

            # Update the open relations registers
            in_open[current_relation[0]] -= 1
            out_open[current_relation[1]] -= 1

    # Flush an eventual last line
    if current_line:
        fill_until(len(tree.nodes), ' ')
        res.append(''.join(current_line))
        current_line = []
        current_token = 0
    # And add a last one for eventual root nodes
    if any(in_open):
        fill_until(len(tree.nodes), ' ')
        res.append(''.join(current_line))

    return '\n'.join(res[::-1])


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
