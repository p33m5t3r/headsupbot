import networkx as nx
import numpy as np
from networkx.drawing.nx_agraph import graphviz_layout
from networkx.classes.digraph import DiGraph
from matplotlib import pyplot as plt

# players
PAYOFF, NATURE, P1, P2 = -1, 0, 1, 2

# toggle for better visualization
NO_RAISING = False

class Node:
    def __init__(self, player, action, depth, rc=0, parent=None, children=None):
        self.player = player
        self.action = action
        self.depth = depth
        self.rc = rc        # raise count
        self.parent = parent
        self.children = [] if children is None else children

terminal_counter = 0
# returns [payoff nodes, nature nodes]
def add_fta_tree(G: DiGraph, nature_node: Node, n_rounds):
    fta = P1
    other = P2
    depth = nature_node.depth + 1

    if depth >= n_rounds:
        payoff = Node(PAYOFF, 'p', depth)
        G.add_edge(nature_node, payoff)
        return [], [], 1

    x = Node(fta, 'x', depth)
    xx = Node(other, 'x', depth)
    xb = Node(other, 'b', depth)
    xbf = Node(fta, 'f', depth)
    xbc = Node(fta, 'c', depth)
    b = Node(fta, 'b', depth)
    bf = Node(other, 'f', depth)
    bc = Node(other, 'c', depth)
    ns = [xx, xbc, bc]
    ps = [xbf, bf]

    G.add_edge(nature_node, x)
    G.add_edge(nature_node, b)
    G.add_edge(x, xx)
    G.add_edge(x, xb)
    G.add_edge(xb, xbf)
    G.add_edge(xb, xbc)
    G.add_edge(b, bf)
    G.add_edge(b, bc)

    if NO_RAISING:
        xps, xns = [], []
        bps, bns = [], []
    else:
        br = Node(other, 'r', depth)
        xbr = Node(fta, 'r', depth)
        G.add_edge(xb, xbr)
        G.add_edge(b, br)

        xps, xns = add_raise_tree(G, xbr)
        bps, bns = add_raise_tree(G, br)

    ns = ns + xns + bns
    ps = ps + xps + bps
    return ps, ns, 0

# returns [payoff nodes, nature nodes]
def add_raise_tree(G: DiGraph, raise_node: Node):
    r = raise_node
    rp = raise_node.player
    other = P2 if rp == P1 else P1
    depth = raise_node.depth

    rf = Node(other, 'f', depth)
    rc = Node(other, 'c', depth)
    rr = Node(other, 'r', depth)
    rrf = Node(rp, 'f', depth)
    rrc = Node(rp, 'c', depth)
    rrr = Node(rp, 'r', depth)
    rrrf = Node(other, 'f', depth)
    rrrc = Node(other, 'c', depth)

    ps = [rf, rrf, rrrf]
    ns = [rc, rrc, rrrc]

    G.add_edge(r, rf)
    G.add_edge(r, rc)
    G.add_edge(r, rr)
    G.add_edge(rr, rrf)
    G.add_edge(rr, rrc)
    G.add_edge(rr, rrr)
    G.add_edge(rrr, rrrf)
    G.add_edge(rrr, rrrc)

    return ps, ns

def fta_rec(G: DiGraph, node: Node, n_rounds, nps):
    payoff_count = 0
    ps, ns, t = add_fta_tree(G, node, n_rounds)
    payoff_count += t

    for p in ps:
        payoff = Node(PAYOFF, 'p', p.depth + 1)
        G.add_node(payoff)
        G.add_edge(p, payoff)
        payoff_count += 1

    for n in ns:
        if nps == 1 or n.depth >= n_rounds - 1:
            payoff_count += fta_rec(G, n, n_rounds, nps)
            continue

        n_states = [Node(NATURE, str(i), n.depth + 1) 
            for i in range(nps)]

        for m in n_states:
            G.add_edge(n, m)

        for m in n_states:
            payoff_count += fta_rec(G, m, n_rounds, nps)

    return payoff_count

def formulate_game(G: DiGraph, root, n_rounds, nps=5):
    ns_per_street = nps
    ns = [Node(NATURE, str(i), 0) for i in range(ns_per_street)]
    payoff_count = 0

    for n in ns:
        G.add_edge(root, n)
        payoff_count += fta_rec(G, n, n_rounds, nps)

    print(f"payoff count: {payoff_count}")

def get_node_color_player(node):
    if node.player == NATURE:
        return 'purple'
    if node.player == PAYOFF:
        return 'lightgray'
    if node.player == P1:
        return 'lightgreen'
    if node.player == P2:
        return 'lightcoral'
    else:
        return 'lightyellow'

def get_node_color_depth(node):
    if node.player == NATURE:
        return 'purple'
    if node.player == PAYOFF:
        return 'lightgray'

    colors = [
      'lightgreen', 'lightcoral', 'blue', 'lightyellow',
      'lightpink', 'red', 'pink', 'yellow', 'green', 'orange'
    ]
    
    return colors[node.depth % len(colors)]

def print_g(G: DiGraph, filename=None, color_players=True):
    def node_label(node):
        return f'{node.action}'
   
    def get_node_color(node):
        if color_players:
            return get_node_color_player(node)
        return get_node_color_depth(node)

    pos = graphviz_layout(G, prog='dot')
    labels = {node: node_label(node) for node in G.nodes()}
    node_colors = [get_node_color(node) for node in G.nodes()]
    figsize = (40, 30) if filename else (12, 8)
    # figsize = (16, 14)
    plt.figure(figsize=figsize)  # Adjust the figure size as needed
    nx.draw(
        G, pos, with_labels=True, labels=labels, arrows=True,
        node_color=node_colors, node_size=100, font_size=9
    )

    if filename:
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
    else:
        plt.show()

if __name__ == "__main__":
    NO_RAISING = False
    root = Node(NATURE, 'root', 0)
    G = nx.DiGraph()
    # add_fta_tree(G, root)
    # print_g(G)
    formulate_game(G, root, n_rounds=4, nps=3)
    print_g(G, 'trivial_trees.png', color_players=True)



