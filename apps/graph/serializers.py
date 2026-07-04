from rest_framework import serializers
from .models import GraphNode, GraphEdge

class GraphNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = GraphNode
        fields = ['id', 'node_id', 'label', 'node_type', 'description']

class GraphEdgeSerializer(serializers.ModelSerializer):
    source_id = serializers.CharField(source='source.node_id')
    target_id = serializers.CharField(source='target.node_id')

    class Meta:
        model = GraphEdge
        fields = ['id', 'source_id', 'target_id', 'relation_type', 'color', 'is_dashed']