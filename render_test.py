import networkx as nx
import matplotlib.pyplot as plt

def draw_tree():
    G = nx.DiGraph()
    edges = [
        ('Root', 'Left'),
        ('Root', 'Right'),
        ('Left', 'Left.Left'),
        ('Right', 'Right.Right')
    ]
    G.add_edges_from(edges)

    # Вычислим позиции вручную, чтобы получить top-down дерево
    pos = {
        'Root': (0, 3),
        'Left': (-1, 2),
        'Right': (1, 2),
        'Left.Left': (-1.5, 1),
        'Right.Right': (1.5, 1),
    }

    nx.draw(G, pos, with_labels=True, arrows=True, node_size=2000, node_color='lightblue', font_size=10)
    plt.show()

draw_tree()
