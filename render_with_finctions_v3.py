import json
import textwrap
from collections import defaultdict

import networkx as nx
import plotly.graph_objects as go


def wrap_label(text, width=18):
    return '<br>'.join(textwrap.wrap(text or '', width=width))


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

for node in data['nodes']:
    graph.add_node(node['id'],
                   name=node.get('name'),
                   label=node.get('label', ''),
                   weight=node.get('weight', 1),
                   level=node.get('level', 1))

for link in data['links']:
    graph.add_edge(link['source'], link['target'])


def collapse_same_label_chains(graph):
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
            if (graph.nodes[next_node].get('label') == label and
                    graph.in_degree(next_node) == 1 and
                    graph.out_degree(current) == 1):
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


def layered_pos(graph, total_width=10, y_gap=150):
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


graph = collapse_same_label_chains(graph)
pos = layered_pos(graph, total_width=800)

# --- Plotly drawing ---
edge_x = []
edge_y = []

for source, target in graph.edges():
    x0, y0 = pos[source]
    x1, y1 = pos[target]
    edge_x += [x0, x1, None]
    edge_y += [y0, y1, None]

edge_trace = go.Scatter(
    x=edge_x, y=edge_y,
    line=dict(width=1, color='#888'),
    hoverinfo='none',
    mode='lines')

node_x = []
node_y = []
node_text = []
node_color = []

for node in graph.nodes:
    x, y = pos[node]
    node_x.append(x)
    node_y.append(y)
    label = graph.nodes[node].get('label', '')
    color = COLORS.get(label, 'lightgray')
    name = graph.nodes[node].get('name', '')
    node_text.append(wrap_label(name))
    node_color.append(color)

node_trace = go.Scatter(
    x=node_x, y=node_y,
    mode='markers+text',
    text=node_text,
    textposition='middle center',
    hoverinfo='text',
    marker=dict(
        showscale=False,
        color=node_color,
        size=50,
        line=dict(width=2, color='DarkSlateGrey')
    )
)

fig = go.Figure(data=[edge_trace, node_trace],
                layout=go.Layout(
                    title=f"Граф лекарственного средства {', '.join(data['name'])}",
                    title_font_size=16,
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20, l=5, r=5, t=40),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                )

fig.show()
