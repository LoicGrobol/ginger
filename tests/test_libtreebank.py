import os
from sys import path
PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path.append(PATH)

import textwrap


import pytest

import libtreebank


def test_conllu_parse_basic():
    '''Test parsing a simple CoNLL-U tree.'''
    conllu_basic_tree = [
        "1	Je	je	CLS	CLS	n=s|p=1	2	suj	_	_",
        "2	reconnais	reconnaître	V	V	n=s|t=P|p=12	0	root	_	_",
        "3	l'	l'	DET	DET	n=s	4	det	_	_",
        "4	existence	existence	NC	NC	n=s|g=f	2	obj	_	_",
        "5	du	de	P+D	P+D	n=s|g=m	4	dep	_	_",
        "6	kiwi	kiwi	NC	NC	n=s|g=m	5	prep	_	_",
        "7	.	.	PONCT	PONCT	_	6	ponct	_	_"]
    tree = libtreebank._conllu_tree(conllu_basic_tree)
    # The nodes are in the correct order
    assert [n.form for n in tree.nodes] == ['ROOT', 'Je', 'reconnais', "l'",
                                            'existence', 'du', 'kiwi', '.']
    # The dependency graph is correct
    assert [n.head for n in tree.nodes] == [None, *[tree.nodes[i] for i in (2, 0, 4, 2, 4, 5, 6)]]
