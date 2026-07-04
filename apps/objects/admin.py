from django.contrib import admin
from .models import ResearchObject, Metric, Bottleneck, Strength, SliderParameter

class MetricInline(admin.TabularInline):
    model = Metric
    extra = 1

class BottleneckInline(admin.TabularInline):
    model = Bottleneck
    extra = 1

class StrengthInline(admin.TabularInline):
    model = Strength
    extra = 1

class SliderParameterInline(admin.TabularInline):
    model = SliderParameter
    extra = 1

@admin.register(ResearchObject)
class ResearchObjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'status', 'created_at')
    list_filter = ('project', 'status')
    search_fields = ('name', 'description')
    inlines = [MetricInline, BottleneckInline, StrengthInline, SliderParameterInline]