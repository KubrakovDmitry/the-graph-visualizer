import base64
import io
import json
import math
from collections import defaultdict

import networkx as nx
import plotly.graph_objects as go
from dash import (Dash, dcc, html, Input, Output, State, ctx,
                  no_update)


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
pos: dict = {}


def empty_figure_with_message(message='Загрузите JSON-файл с графом'):
    return go.Figure(
        layout=go.Layout(
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            annotations=[
                dict(
                    text=message,
                    xref='paper', yref='paper',
                    showarrow=False,
                    font=dict(size=20),
                    x=0.5, y=0.5,
                    align='center'
                )
            ]
        )
    )


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


def find_path_from_roots(target):
    # Ищем любую вершину без входящих рёбер — корень
    roots = [n for n in graph.nodes if graph.in_degree(n) == 0]
    all_paths = []
    for root in roots:
        try:
            paths = nx.shortest_simple_paths(graph, root, target)
            for path in paths:
                all_paths.append(path)
        except nx.NetworkXNoPath:
            continue
    return all_paths
    # roots = [n for n in graph.nodes if graph.in_degree(n) == 0]
    # for root in roots:
    #     try:
    #         return nx.shortest_path(graph, root, target)
    #     except nx.NetworkXNoPath:
    #         continue
    # return []


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


def process_and_draw(data):
    global graph, pos

    graph.clear()
    for node in data['nodes']:
        graph.add_node(node['id'],
                       name=node.get('name'),
                       label=node.get('label', ''),
                       level=node.get('level', 1))
    for link in data['links']:
        if link['source'] in graph.nodes and link['target'] in graph.nodes:
            graph.add_edge(link['source'], link['target'])
        else:
            print(f'Пропущено ребро: {link}')
    pos = layered_pos(graph)
    return build_figure()


# Dash
app = Dash(__name__)

app.layout = html.Div([
    dcc.Input(
        id='search-input',
        type='text',
        placeholder='Введите навазние вершины',
        debounce=True,
        style={'width': '100%', 'padding': '10px', 'fontSize': '16px'}
    ),
    html.Div(id='error-message', style={
        'color': 'red',
        'fontWeight': 'bold',
        'textAlign': 'center',
        'marginBottom': '10px'
    }),
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Перетащите файл сюда или ',
            html.A('выберите')
        ]),
        style={
            'width': '100%', 'height': '60px', 'lineHeight': '60px',
            'borderWidth': '1px', 'borderStyle': 'dashed',
            'borderRadius': '5px', 'textAlign': 'center',
            'margin': '10px'
        },
        multiple=False
    ),
    dcc.Loading(dcc.Graph(id='graph', figure=empty_figure_with_message()),
                type='circle'),
    dcc.Store(id='selected-node'),
    # html.Button(id='reset-btn', style={'display': 'none'}),
    dcc.Store(id='esc-pressed', data=False),
    dcc.Interval(id='interval-esc', interval=500, n_intervals=0),
    # html.Script('''
    #     document.addEventListener('keydown', function(e) {
    #         if (e.key === 'Escape') {
    #             document.getElementById('reset-btn')?.click();
    #         }
    #     });
    # ''')
])

app.clientside_callback(
    """
    function(n_intervals) {
        if (!window.escapeListenerAdded) {
            window.escapeListenerAdded = true;
            window.escPressed = false;
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape') {
                    window.escPressed = true;
                }
            });
        }

        if (window.escPressed) {
            window.escPressed = false;
            return true;
        }

        return window.dash_clientside.no_update;
    }
    """,
    [Output('esc-pressed', 'data')],             # ✅ Только Store!
    [Input('interval-esc', 'n_intervals')]       # Интервал нужен как триггер
)


@app.callback(
    Output('graph', 'figure'),
    Output('selected-node', 'data'),
    Output('error-message', 'children'),
    Input('search-input', 'value'),
    Input('upload-data', 'contents'),
    Input('upload-data', 'filename'),
    Input('graph', 'clickData'),
    # Input('reset-btn', 'n_clicks'),
    Input('esc-pressed', 'data'),
    State('selected-node', 'data'),
    prevent_initial_call=True,
)
def render_graph(search_value, upload_contents, _upload_filename, clickData,
                 esc_pressed,  selected_node):  # _reset_clicks,
    """Функция отрисовки графа."""
    trigger = ctx.triggered_id or 'initial'

    if trigger == 'esc-pressed' and esc_pressed:
        return build_figure(), None, ''
    elif trigger == 'upload-data' and upload_contents:
        print("Загрузка файла")
        try:
            _, content_string = upload_contents.split(',')
            decoded = base64.b64decode(content_string)
            loaded_data = json.load(io.StringIO(decoded.decode('utf-8')))
            return process_and_draw(loaded_data), None, ''
        except Exception as e:
            print('Ошибка при чтении файла:', e)
            return empty_figure_with_message(
                "Ошибка при чтении файла"), None, ''
    elif trigger == 'search-input' and search_value:
        for node, attr in graph.nodes(data=True):
            if attr.get('name', '').lower() == search_value.lower():
                paths = find_path_from_roots(node)
                all_nodes = set()
                for p in paths:
                    all_nodes.update(p)
                return build_figure(list(all_nodes)), node, ''
        return build_figure(), None, (f'Вершина "{search_value}" '
                                      'не найдена в графе.')
    elif trigger == 'graph' and clickData:
        point = clickData['points'][0]
        x = point['x']
        y = point['y']
        for node, (x_node, y_node) in pos.items():
            if math.hypot(x - x_node, y - y_node) < 15:
                if abs(x - x_node) < 10 and abs(y - y_node) < 10:
                    if node == selected_node:
                        return build_figure(), None, ''
                    # path = find_path_from_root(node)
                    # return build_figure(path), node, ''
                    paths = find_path_from_roots(node)
                    all_nodes = set()
                    for path in paths:
                        all_nodes.update(path)
                    return build_figure(list(all_nodes)), node, ''
    return no_update


if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=8050)