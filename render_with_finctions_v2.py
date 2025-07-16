"""Модуль отрисовки графов."""

import json
import textwrap
from collections import defaultdict

import matplotlib.pyplot as plt
import networkx as nx


COLORS = {
    'prepare': 'green',
    'action': 'purple',
    'metabol': 'yellow',
    'excretion': 'violet',
    'absorbtion': 'black',
    'mechanism': 'blue',
    'group': 'green',
    'noun': 'gray',
    'side_e': 'red'
}


with open('spironolacton_lizinopril.json', 'r', encoding='utf-8') as f:
    data = json.load(f)


graph = nx.DiGraph()

# Добавление узлов
for node in data['nodes']:
    graph.add_node(node['id'],
                   name=node.get('name'),
                   label=node.get('label', ''),
                   weight=node.get('weight', 1),
                   level=node.get('level', 1))

# Добавление связей (рёбер)
for link in data['links']:
    graph.add_edge(link['source'], link['target'])


def collapse_same_label_chains(graph):
    """Свёртка последовательностей вершин с одинаковыми вершинами."""
    visited = set()

    for node in list(graph.nodes):
        if node in visited:
            continue

        label = graph.nodes[node].get('label')
        chain = [node]

        current = node

        while True:
            successors = list(graph.successors(current))
            if len(successors) != 1:
                break

            next_node = successors[0]
            if (graph.nodes[next_node].get('label') == label
                    and graph.in_degree(next_node) == 1
                    and graph.out_degree(current) == 1):

                chain.append(next_node)
                visited.add(next_node)
                current = next_node
            else:
                break

        if len(chain) > 1:
            start, end = chain[0], chain[-1]

            for pred in list(graph.predecessors(start)):
                if pred != end:
                    graph.add_edge(pred, end)

            for n in chain[:-1]:
                graph.remove_node(n)

    return graph


def layered_pos(graph, total_width=10, y_gap=2):
    """Располагает узлы сверху вниз по уровню."""
    level_nodes = defaultdict(list)

    for node, data in graph.nodes(data=True):
        level = data.get('level', 0)
        level_nodes[level].append(node)

    pos = {}
    for level in sorted(level_nodes):
        nodes = level_nodes[level]
        count = len(nodes)
        if count == 1:
            x_positions = [0]
        else:
            step = total_width / (count - 1)
            x_positions = [-total_width / 2 + i * step for i in range(count)]

        y = -level * y_gap
        for node, x in zip(nodes, x_positions):
            pos[node] = (x, y)

    return pos

# def layered_pos(graph, x_gap=2, y_gap=2):

#     """Располагает узлы сверху вниз по уровню."""
#     level_nodes = defaultdict(list)

#     for node, data in graph.nodes(data=True):
#         level = data.get('level', 0)
#         level_nodes[level].append(node)

#     pos = {}
#     for level in sorted(level_nodes):
#         nodes = level_nodes[level]
#         count = len(nodes)
#         width = (count - 1) * x_gap if count > 1 else 0
#         x_start = -width / 2

#         for i, node in enumerate(nodes):
#             x = x_start + i * x_gap
#             y = -level * y_gap
#             pos[node] = (x, y)
    # y_gap = 1.5
    # x_gap = 1.5

    # for level, nodes in level_nodes.items():
    #     for i, node in enumerate(nodes):
    #         x = i * x_gap
    #         y = -level * y_gap
    #         pos[node] = (x, y)

    # return pos


graph = collapse_same_label_chains(graph)

pos = layered_pos(graph)

# Считаем уже занятые позиции
used_x = {p[0] for p in pos.values()}

x_offset = max(used_x, default=1) + 1

for i, node in enumerate(graph.nodes):
    if node not in pos:
        pos[node] = (x_offset, -i)  # вертикально вниз по оси y


def wrap_label(text, width=18):
    return '\n'.join(textwrap.wrap(text or '', width=width))


node_colors = [
    COLORS.get(graph.nodes[n].get('label'), 'white')
    for n in graph.nodes
]

plt.figure(figsize=(14, 10))
nx.draw(graph,
        pos=pos,
        node_color=node_colors,
        with_labels=True,
        labels={n: wrap_label(graph.nodes[n].get("name", n))
                for n in graph.nodes},
        node_size=500,
        font_size=8,
        arrows=True)

headline = f'Граф лекарственного средства {", ".join(data["name"])}'
plt.title(headline)
plt.axis('off')
plt.tight_layout()
plt.show()
plt.savefig(headline)
