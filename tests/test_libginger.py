import os
from sys import path
PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path.append(PATH)

import pytest

import libginger

test_conll = """1	la	la	DET	DET	n=s|g=f|	0	_	_	_
2	toute	toute	DET	DET	n=s|g=f|	0	_	_	_
3	première	premier	ADJ	ADJ	n=s|g=f|	4	suj	_	_
4	est	être	V	V	n=s|t=P|p=3|	0	_	_	_
5	bien	bien	ADV	ADV		6	mod	_	_
6	simple	simple	ADJ	ADJ	n=s|	4	ats	_	_
7	je	je	CLS	CLS	n=s|p=1|	8	suj	_	_
8	voudrais	vouloir	V	V	n=s|t=C|p=12|	4	mod	_	_
9	savoir	savoir	VINF	VINF	t=W|	8	obj	_	_
10	depuis	depuis	P	P		9	mod	_	_
11	combien	combien	ADVWH	ADVWH		13	mod	_	_
12	de	de	P	P		13	det	_	_
13	temps	temps	NC	NC	g=m|	10	prep	_	_
14	vous	vous	CLS	CLS	n=p|p=2|	15	suj	_	_
15	habitez	habiter	V	V	n=p|t=P|p=2|	4	mod	_	_
16	à	à	P	P		15	a_obj	_	_
17	Orléans	_	NC	NC	_	16	prep	_	_"""

test_ascii = '│                                                                   │                                          │           \n│                           ┌───────────────────────────────────────│─────────────────────────────────┐        │           \n│                           ├─────────────────────┐                 │                                 │        │           \n│┌─────────────────────────┐│                     │                 │                                 │        │           \n│├────────┐                │├─────────┐           │                 │                    ┌────────────│────────│───┐       \n││        │                ││         │           │┌────────┐       │       ┌────────────│┐           │        │   │       \n│├────┐   │      ┌─────────│┤   ┌─────│┐      ┌───│┤        │       │       │        ┌───│┤     ┌─────│┐       │┌─┐│       \n↓│    ↓   ↓      ↓         ↓│   ↓     ↓│      ↓   ↓│        ↓       ↓       ↓        ↓   ↓│     ↓     ↓│       ↓│ ↓│       \nROOT  la  toute  première  est  bien  simple  je  voudrais  savoir  depuis  combien  de  temps  vous  habitez  à  Orléans'


@pytest.fixture(scope='module')
def test_tree():
    nodes = [libginger.Node(0, 'ROOT')]
    nodes.extend((libginger.Node(1, 'la', 'la', 'DET', 'DET', {'n': 's', 'g': 'f'}, nodes[0], None, [], '_'),
                  libginger.Node(2, 'toute', 'toute', 'DET', 'DET', {'n': 's', 'g': 'f'}, nodes[0], None, [], '_'),
                  libginger.Node(4, 'est', 'être', 'V', 'V', {'n': 's', 't': 'P', 'p': '3'}, nodes[0], None, [], '_')))

    nodes.extend((libginger.Node(3, 'première', 'premier', 'ADJ', 'ADJ', {'n': 's', 'g': 'f'}, nodes[3], 'suj', [], '_'),
                  libginger.Node(6, 'simple', 'simple', 'ADJ', 'ADJ', {'n': 's'}, nodes[3], 'ats', [], '_'),
                  libginger.Node(8, 'voudrais', 'vouloir', 'V', 'V', {'n': 's', 't': 'C', 'p': '12'}, nodes[3], 'mod', [], '_'),
                  libginger.Node(15, 'habitez', 'habiter', 'V', 'V', {'n': 'p', 't': 'P', 'p': '2'}, nodes[3], 'mod',  [], '_')))

    nodes.extend((libginger.Node(5, 'bien', 'bien', 'ADV', 'ADV', {}, nodes[5], 'mod', [], '_'),
                  libginger.Node(7, 'je', 'je', 'CLS', 'CLS', {'n': 's', 'p': '1'}, nodes[6], 'suj', [], '_'),
                  libginger.Node(9, 'savoir', 'savoir', 'VINF', 'VINF', {'t': 'W'}, nodes[6], 'obj', [], '_'),
                  libginger.Node(14, 'vous', 'vous', 'CLS', 'CLS', {'n': 'p', 'p': '2'}, nodes[7], 'suj', [], '_'),
                  libginger.Node(16, 'à', 'à', 'P', 'P', {}, 15, 'a_obj', [], '_')))

    nodes.extend((libginger.Node(10, 'depuis', 'depuis', 'P', 'P', nodes[10], 'mod', [], '_'),
                  libginger.Node(17, 'Orléans', '_', 'NC', 'NC', {}, nodes[12], 'prep', [], '_')))

    nodes.append(libginger.Node(13, 'temps', 'temps', 'NC', 'NC', {'g': 'm'}, nodes[14], 'prep', [], '_'))

    nodes.extend((libginger.Node(11, 'combien', 'combien', 'ADVWH', 'ADVWH', {}, nodes[15], 'mod', [], '_'),
                  libginger.Node(12, 'de', 'de', 'P', 'P', {}, nodes[15], 'det', [], '_')))

    return libginger.Tree(nodes)


def test_ascii_tree_generation():
    t = test_tree()
    assert t.ascii_art() == test_ascii
