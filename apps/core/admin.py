from django.contrib import admin
from .models import ResearchProject

@admin.register(ResearchProject)
class ResearchProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'created_at')