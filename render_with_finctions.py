"""Модуль отрисовки графов."""

import json
import textwrap
import random

import matplotlib.pyplot as plt
import networkx as nx


NAME = 'name'

with open('drug_allopurinol.json', 'r', encoding='utf-8') as f:
    data = json.load(f)


graph = nx.DiGraph()

# Добавление узлов
for node in data['nodes']:
    graph.add_node(node['id'],
                   label=node.get('label', ''),
                   weight=node.get('weight', 1))

# Добавление связей (рёбер)
for link in data['links']:
    graph.add_edge(link['source'], link['target'])


graph.remove_nodes_from(list(nx.isolates(graph)))


def hierarchy_pos(graph, root=None, width=1.0, vert_gap=0.5, vert_loc=0):
    """Вычисление позиционирования сверху-вниз (top-down)."""
    def _hierarchy_pos(graph, node, left, right, level, pos):
        """Рекурсивная раскладка для иерархического графа."""
        pos[node] = ((left + right) / 2, -level * vert_gap + vert_loc)
        neighbors = list(graph.successors(node))
        if neighbors:
            width_per_child = (right - left) / len(neighbors)
            for i, child in enumerate(neighbors):
                _hierarchy_pos(graph, child,
                               left + i * width_per_child,
                               left + (i + 1) * width_per_child,
                               level + 1, pos)

    if root is None:
        root = [n for n, d in graph.in_degree() if d == 0][0]

    pos = {}
    _hierarchy_pos(graph, root, 0, width, 0, pos)
    return pos


pos = hierarchy_pos(graph)

# Считаем уже занятые позиции
used_x = {p[0] for p in pos.values()}

x_offset = max(used_x, default=1) + 1

for i, node in enumerate(graph.nodes):
    if node not in pos:
        pos[node] = (x_offset, -i)  # вертикально вниз по оси y


for i, node in enumerate(list(nx.isolates(graph))):
    pos[node] = (i, -len(pos))

node_sizes = [graph.nodes[n].get('weight', 1) * 300 for n in graph.nodes]


def wrap_label(text, width=18):
    return '\n'.join(textwrap.wrap(text, width=width))


labels = {n: wrap_label(n) for n in graph.nodes}

plt.figure(figsize=(14, 10))
nx.draw(graph, pos,
        with_labels=True,
        labels=labels,
        node_size=node_sizes,
        node_color='lightblue',
        font_size=9,
        arrows=True,
        edge_color='gray')

headline = f'Граф лекарственного средства {data[NAME]}'
plt.title(headline)
plt.axis('off')
plt.tight_layout()
plt.savefig(headline)
