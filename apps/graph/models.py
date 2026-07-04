from django.db import models

class GraphNode(models.Model):
    TYPE_CHOICES = [
        ('param', 'Параметр'),
        ('kpi', 'KPI'),
        ('mech', 'Механизм'),
        ('fail', 'Деградация'),
    ]
    node_id = models.CharField(max_length=50, unique=True)
    label = models.CharField(max_length=100)
    node_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    description = models.TextField(blank=True)

class GraphEdge(models.Model):
    source = models.ForeignKey(GraphNode, on_delete=models.CASCADE, related_name='out_edges')
    target = models.ForeignKey(GraphNode, on_delete=models.CASCADE, related_name='in_edges')
    relation_type = models.CharField(max_length=50)
    color = models.CharField(max_length=20, default='#135BEC')
    is_dashed = models.BooleanField(default=False)