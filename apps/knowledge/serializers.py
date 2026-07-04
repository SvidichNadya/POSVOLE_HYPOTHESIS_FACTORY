# apps/knowledge/serializers.py
from rest_framework import serializers
from .models import KnowledgeDocument

class KnowledgeDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeDocument
        fields = ['id', 'doc_type', 'title', 'meta', 'abstract', 'tags', 'file', 'status', 'progress', 'created_at']