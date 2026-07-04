from django.contrib import admin
from .models import GraphNode, GraphEdge

@admin.register(GraphNode)
class GraphNodeAdmin(admin.ModelAdmin):
    list_display = ('node_id', 'label', 'node_type')
    search_fields = ('label', 'description')

@admin.register(GraphEdge)
class GraphEdgeAdmin(admin.ModelAdmin):
    list_display = ('source', 'target', 'relation_type')
    list_filter = ('relation_type',)