"""Validated graph explorer — owner: Shrestha."""
import streamlit as st
import streamlit.components.v1 as components
from common import load, page_header
from cdlp.learning_path.api import build_graph, graph_summary

page_header('Knowledge Graph', 'Shrestha', 'validated_graph.json')
data = load('validated_graph.json')
include_review = st.checkbox('Include HUMAN_REVIEW edges (experimental)', value=False)
include_soft = st.checkbox('Include soft prerequisites', value=True)
try:
    graph = build_graph(data, include_review=include_review, include_soft=include_soft)
except ValueError as exc:
    st.error(str(exc))
    st.stop()
st.metric('Concepts', graph.number_of_nodes())
st.metric('Accepted dependencies', graph.number_of_edges())
try:
    from pyvis.network import Network
    net = Network(height='530px', width='100%', directed=True, bgcolor='#ffffff', font_color='#1f2937', cdn_resources='in_line')
    for node, attrs in graph.nodes(data=True):
        net.add_node(node, label=attrs.get('name', node), title=f"Concept: {attrs.get('name', node)}")
    for src, dst, attrs in graph.edges(data=True):
        net.add_edge(src, dst, title=f"{attrs.get('strength', 'hard')} prerequisite | confidence {attrs.get('confidence', 0):.2f}", color='#64748b' if attrs.get('strength') == 'soft' else '#2563eb', dashes=attrs.get('strength') == 'soft')
    net.set_options('{"physics":{"stabilization":{"iterations":100}},"interaction":{"hover":true,"navigationButtons":true}}')
    components.html(net.generate_html(), height=550, scrolling=True)
except ImportError:
    st.info('Install pyvis for the interactive network. Showing dependencies below.')
    st.write(list(graph.edges()))
selected = st.selectbox('Inspect a concept', list(graph.nodes), format_func=lambda c: graph.nodes[c].get('name', c))
from networkx import ancestors, descendants
st.write('Prerequisites:', ', '.join(sorted(ancestors(graph, selected))) or 'None')
st.write('Dependents:', ', '.join(sorted(descendants(graph, selected))) or 'None')
for src in graph.predecessors(selected):
    edge = graph.edges[src, selected]
    with st.expander(f"{graph.nodes[src].get('name', src)} → {graph.nodes[selected].get('name', selected)}"):
        st.write(edge.get('reason', 'No reason provided'))
        for ev in edge.get('evidence', []):
            st.caption(f"{ev.get('doc', 'Unknown document')} · page {ev.get('page', '?')}: {ev.get('quote', '')}")
