from django.contrib import admin
from .models import KnowledgeDocument

@admin.register(KnowledgeDocument)
class KnowledgeDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'doc_type', 'created_at')
    list_filter = ('doc_type',)
    search_fields = ('title', 'abstract', 'meta')