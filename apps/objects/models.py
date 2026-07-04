from django.db import models
from apps.core.models import ResearchProject

class ResearchObject(models.Model):
    # Изменён related_name с 'objects' на 'research_objects'
    project = models.ForeignKey(ResearchProject, on_delete=models.CASCADE, related_name='research_objects')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=50, default='Новый')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Metric(models.Model):
    object = models.ForeignKey(ResearchObject, on_delete=models.CASCADE, related_name='metrics')
    name = models.CharField(max_length=100)
    current_value = models.CharField(max_length=50)
    target_value = models.CharField(max_length=50)
    unit = models.CharField(max_length=20, blank=True)

class Bottleneck(models.Model):
    object = models.ForeignKey(ResearchObject, on_delete=models.CASCADE, related_name='bottlenecks')
    description = models.TextField()

class Strength(models.Model):
    object = models.ForeignKey(ResearchObject, on_delete=models.CASCADE, related_name='strengths')
    description = models.TextField()

class SliderParameter(models.Model):
    object = models.ForeignKey(ResearchObject, on_delete=models.CASCADE, related_name='sliders')
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=50)
    min_value = models.FloatField()
    max_value = models.FloatField()
    step = models.FloatField(default=1.0)
    default_value = models.FloatField()
    unit = models.CharField(max_length=20, blank=True)