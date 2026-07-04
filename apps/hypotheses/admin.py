from django.contrib import admin
from .models import Hypothesis, Evidence, RoadmapStep

class EvidenceInline(admin.TabularInline):
    model = Evidence
    extra = 1

class RoadmapStepInline(admin.TabularInline):
    model = RoadmapStep
    extra = 1
    ordering = ['order']

@admin.register(Hypothesis)
class HypothesisAdmin(admin.ModelAdmin):
    list_display = ('title', 'object', 'status', 'novelty_score', 'roi')
    list_filter = ('status', 'object')
    search_fields = ('title', 'description')
    inlines = [EvidenceInline, RoadmapStepInline]
    readonly_fields = ('created_at',)