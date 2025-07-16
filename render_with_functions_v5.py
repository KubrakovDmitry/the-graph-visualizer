import json
from collections import defaultdict

import networkx as nx
import plotly.graph_objects as go
from dash import (Dash, dcc, html, Input, Output, State, ctx,
                #   clientside_callback,
                  no_update)


with open("spironolacton_lizinopril.json", encoding="utf-8") as f:
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


def build_figure(highlight_path=None):
    edge_x, edge_y = [], []
    node_x, node_y = [], []
    node_text, node_color, node_opacity = [], [], []

    highlight_nodes = set(highlight_path or [])
    highlight_edges = set()

    # Определим рёбра на пути
    if highlight_path and len(highlight_path) > 1:
        highlight_edges = {(highlight_path[i], highlight_path[i+1])
                           for i in range(len(highlight_path)-1)}

    # Рёбра
    for src, tgt in graph.edges():
        x0, y0 = pos[src]
        x1, y1 = pos[tgt]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color='lightgray'),
        hoverinfo='none',
        mode='lines',
        opacity=0.3 if highlight_path else 1
    )

    if highlight_edges:
        hx, hy = [], []
        for src, tgt in highlight_edges:
            x0, y0 = pos[src]
            x1, y1 = pos[tgt]
            hx += [x0, x1, None]
            hy += [y0, y1, None]

        edge_highlight = go.Scatter(
            x=hx, y=hy,
            line=dict(width=2, color='black'),
            hoverinfo='none',
            mode='lines',
            opacity=1
        )
    else:
        edge_highlight = None

    for node in graph.nodes():
        x, y = pos[node]
        name = graph.nodes[node].get('name', '')
        label = graph.nodes[node].get('label', '')
        color = COLORS.get(label, 'lightgray')

        is_highlighted = not highlight_path or node in highlight_nodes
        opacity = 1.0 if is_highlighted else 0.1

        node_x.append(x)
        node_y.append(y)
        node_color.append(color)
        node_text.append(name)
        node_opacity.append(opacity)

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers',
        hoverinfo='text',
        text=node_text,
        marker=dict(
            color=node_color,
            size=20,
            line_width=2,
            opacity=node_opacity
        )
    )

    data = [edge_trace]
    if edge_highlight:
        data.append(edge_highlight)
    data.append(node_trace)

    fig = go.Figure(
        data=data,
        layout=go.Layout(
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
    )
    return fig


def find_path_from_root(target):
    # Ищем любую вершину без входящих рёбер — корень
    roots = [n for n in graph.nodes if graph.in_degree(n) == 0]
    for root in roots:
        try:
            return nx.shortest_path(graph, root, target)
        except nx.NetworkXNoPath:
            continue
    return []


# Dash
app = Dash(__name__)

app.layout = html.Div([
    dcc.Graph(id='graph', figure=build_figure()),
    dcc.Store(id='selected-node'),
    # dcc.Store(id='reset-request', data=False),
    html.Button(id='reset-btn', style={'display': 'none'}),
    html.Script('''
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                document.getElementById('reset-btn')?.click();
            }
        });
    ''')
])


# clientside_callback(
#     """
#     function(n_clicks) {
#         return true;
#     }
#     """,
#     Output('reset-request', 'data'),
#     Input('graph', 'n_clicks'),
#     prevent_initial_call=True,
# )


@app.callback(
    Output('graph', 'figure'),
    Output('selected-node', 'data'),
    Input('graph', 'clickData'),
    Input('reset-btn', 'n_clicks'),
    State('selected-node', 'data')
)
def update_graph(clickData, reset_clicks, selected_node):
    trigger = ctx.triggered_id

    if trigger == 'reset-btn':
        return build_figure(), None

    if clickData:
        point = clickData['points'][0]
        x = point['x']
        y = point['y']

        for node, (nx, ny) in pos.items():
            if abs(x - nx) < 10 and abs(y - ny) < 10:
                if node == selected_node:
                    return build_figure(), None
                path = find_path_from_root(node)
                return build_figure(path), node
    return no_update


if __name__ == '__main__':
    app.run(debug=False)
