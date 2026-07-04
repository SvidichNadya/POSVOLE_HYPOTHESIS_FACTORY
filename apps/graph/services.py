# apps/graph/services.py
from .models import GraphNode, GraphEdge

def get_graph_data():
    nodes = GraphNode.objects.all()
    edges = GraphEdge.objects.all()

    nodes_data = [{'id': n.node_id, 'label': n.label, 'type': n.node_type, 'desc': n.description} for n in nodes]
    links_data = [{'source': e.source.node_id, 'target': e.target.node_id, 'type': e.relation_type, 'color': e.color, 'dash': e.is_dashed} for e in edges]

    # Слой 3: Link Prediction – выявление скрытых связей (белые пятна)
    existing_pairs = set(f"{e.source_id}_{e.target_id}" for e in edges)
    white_spots_added = 0
    for edge1 in edges:
        if white_spots_added >= 5:
            break
        for edge2 in edges.filter(source=edge1.target):
            if edge1.source != edge2.target:
                pair_key = f"{edge1.source_id}_{edge2.target_id}"
                if pair_key not in existing_pairs:
                    links_data.append({
                        'source': edge1.source.node_id,
                        'target': edge2.target.node_id,
                        'type': 'Скрытая синергия (Предсказание)',
                        'color': '#F59E0B',
                        'dash': True
                    })
                    existing_pairs.add(pair_key)
                    white_spots_added += 1

    return {'nodes': nodes_data, 'links': links_data}