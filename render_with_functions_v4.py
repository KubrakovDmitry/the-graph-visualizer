import json
from collections import defaultdict

import networkx as nx
import plotly.graph_objects as go

with open('spironolacton_lizinopril.json', encoding='utf-8') as f:
    data = json.load(f)

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

graph = nx.DiGraph()
for node in data['nodes']:
    graph.add_node(node['id'],
                   name=node.get('name'),
                   label=node.get('label', ''),
                   level=node.get('level', 1))
for link in data['links']:
    graph.add_edge(link['source'], link['target'])


def layered_pos(graph, y_gap=200, x_gap=100):
    level_nodes = defaultdict(list)
    for node, attr in graph.nodes(data=True):
        level = attr.get('level', 0)
        level_nodes[level].append(node)

    pos = {}
    for level in sorted(level_nodes):
        nodes = level_nodes[level]
        count = len(nodes)
        for i, node in enumerate(nodes):
            x = i * x_gap - (count - 1) * x_gap / 2
            y = -level * y_gap
            pos[node] = (x, y)
    return pos


pos = layered_pos(graph)

edge_trace = go.Scatter(
    x=[],
    y=[],
    line=dict(width=1, color='gray'),
    hoverinfo='none',
    mode='lines'
)

for src, tgt in graph.edges():
    x0, y0 = pos[src]
    x1, y1 = pos[tgt]
    edge_trace['x'] += (x0, x1, None)
    edge_trace['y'] += (y0, y1, None)

x_vals, y_vals, texts, node_colors = [], [], [], []

for node in graph.nodes:
    x, y = pos[node]
    x_vals.append(x)
    y_vals.append(y)

    data = graph.nodes[node]
    label = data.get('label')
    texts.append(data.get('name', 'Без имени'))
    node_colors.append(COLORS.get(label, 'lightgray'))


node_trace = go.Scatter(
    x=x_vals,
    y=y_vals,
    mode='markers',
    textposition='bottom center',
    hoverinfo='text',
    text=texts,
    marker=dict(
        color=node_colors,
        size=20,
        line_width=2)
)

fig = go.Figure(
    data=[edge_trace, node_trace],
    layout=go.Layout(
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
    )
)

fig.show()
