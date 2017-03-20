"""Graphical rendering of `libginger` trees."""

import re
import math

try:
    import cairocffi as cairo
except ImportError:  # don't break if cairo is not available
    # TODO: Issue a warning here
    cairo = None

try:
    import libginger
except ImportError:
    from ginger import libginger


def text(tree: libginger.Tree) -> str:
    '''Return the text content of the tree, without any dependency link.'''
    return ' '.join(n.form for n in tree.nodes)

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
    relations = [(i, tree.nodes.index(n.head)) for i, n in enumerate(tree.nodes) if n.head in tree.nodes]

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
        index, current_relation = next(((i, r) for i, r in enumerate(relations) if min(r) >= current_token),
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


def cairo_surf(tree: libginger.Tree,
               font_size: int = 20,
               token_node_distance: int = 20,
               node_part_margin: int = None) -> cairo.Surface:
    '''Render a tree in a cairo surface.

       ## Parameters
         - `font_size`  the font size used
         - `token_node_distance`  the horizontal soacing between two nodes
         - `node_part_margin`  the vertical spacing between node attributes
                               (default: $⌈`token_node_distance`/3⌉$)'''
    if cairo is None:
        raise NotImplementedError

    node_part_margin = node_part_margin if node_part_margin is not None else math.ceil(token_node_distance/3)

    # First, determine the size of the result
    # A surface that will serve to compute the actual size of the final survace
    dummy = cairo.ImageSurface(cairo.FORMAT_ARGB32, 0, 0)
    dummy_context = cairo.Context(dummy)
    dummy_context.set_font_size(font_size)
    # For every token, we need to take account the width of the largest of the stacked
    # attributes : `form`, `lemma`, `upostag`
    # The height will simply be three times the maximum height
    res_width = max_height = 0
    for n in tree.nodes[1:]:
        parts_extents = [dummy_context.text_extents(s) for s in (n.form, n.lemma, n.upostag) if s is not None]
        res_width += max(e[2] for e in parts_extents)
        part_height = max(max_height, max(e[3] for e in parts_extents))
    # Add the spaces
    res_width += token_node_distance*(len(tree.nodes)-1)
    res_height = 3*part_height + 2*node_part_margin
    # Normalise to integer pixel sizes
    res_width, res_height = math.ceil(res_width), math.ceil(res_height)

    # Now draw for real
    res = cairo.ImageSurface(cairo.FORMAT_ARGB32, res_width, res_height)
    context = cairo.Context(res)
    context.set_font_size(font_size)

    with context:
        context.set_source_rgb(1, 1, 1)  # White
        context.paint()

    context.set_source_rgba(0, 0, 0)

    # First draw the nodes
    context.move_to(0, 0)
    for n in tree.nodes[1:]:
        parts = (s if s is not None else '_' for s in (n.form, n.lemma, n.upostag))
        parts_extents = [dummy_context.text_extents(s) for s in parts]
        token_width = max(e[2] for e in parts_extents)

        for p, e in zip(parts, parts_extents):
            margin = (token_width - e[2]) // 2
            context.rel_move_to(margin, part_height)
            context.show_text(p)
            context.rel_move_to(-(margin + e[4]), node_part_margin)
        context.rel_move_to(token_width + token_node_distance, -(res_height + node_part_margin))

    context.stroke()

    # Now draw the arcs
    return res


def png(tree: libginger.Tree) -> bytes:
    return cairo_surf(tree).write_to_png()
