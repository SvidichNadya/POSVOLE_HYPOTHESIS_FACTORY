# apps/api/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='api-dashboard'),
    path('dashboard/recommendation/', views.dashboard_recommendation, name='api-dashboard-recommendation'),

    # Projects
    path('projects/', views.projects_list, name='api-projects-list'),
    path('projects/create/', views.create_project, name='api-project-create'),
    path('projects/<int:pk>/', views.project_detail, name='api-project-detail'),
    path('projects/<int:pk>/checklist/', views.update_project_checklist, name='api-project-checklist'),

    # Objects
    path('objects/create/', views.create_object, name='api-object-create'),
    path('objects/', views.objects_list, name='api-objects-list'),
    path('objects/<int:pk>/', views.object_detail, name='api-object-detail'),
    path('objects/metrics/<int:pk>/', views.update_metric, name='api-metric-update'),
    path('objects/<int:pk>/recommendation/', views.object_ai_recommendation, name='api-object-rec'),

    # Hypotheses
    path('hypotheses/', views.hypotheses_list, name='api-hypotheses-list'),
    path('hypotheses/<int:pk>/', views.hypothesis_detail, name='api-hypothesis-detail'),
    path('hypotheses/generate/', views.generate_hypothesis, name='api-hypothesis-generate'),
    path('hypotheses/<int:pk>/status/', views.update_hypothesis_status, name='api-hypothesis-status'),

    # Knowledge
    path('knowledge/', views.knowledge_list, name='api-knowledge-list'),
    path('knowledge/create/', views.create_knowledge, name='api-knowledge-create'),

    # Graph
    path('graph/nodes/', views.graph_nodes, name='api-graph-nodes'),
    path('graph/edges/', views.graph_edges, name='api-graph-edges'),

    # Simulation
    path('simulate/', views.simulate_what_if, name='api-simulate'),

    # Opportunity Map
    path('opportunity-map/', views.opportunity_map, name='api-opportunity-map'),
]