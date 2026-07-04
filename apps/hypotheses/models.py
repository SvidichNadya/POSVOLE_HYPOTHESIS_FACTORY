from django.db import models
from apps.objects.models import ResearchObject

class Hypothesis(models.Model):
    STATUS_CHOICES = [
        ('idea', 'Идея'),
        ('validation', 'Валидация ИИ'),
        ('experiment', 'НИОКР / Эксперимент'),
        ('completed', 'Завершено'),
    ]
    object = models.ForeignKey(
        ResearchObject,
        on_delete=models.CASCADE,
        related_name='hypotheses',
        null=True,
        blank=True
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='idea')
    novelty_score = models.PositiveSmallIntegerField(default=50)
    feasibility_score = models.FloatField(default=0.5)
    research_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    economic_benefit = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    payback_months = models.PositiveSmallIntegerField(null=True, blank=True)
    roi = models.FloatField(null=True, blank=True)
    complexity_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Evidence(models.Model):
    """Цепочка доказательств для гипотезы (XAI)."""
    hypothesis = models.ForeignKey(
        Hypothesis,
        on_delete=models.CASCADE,
        related_name='evidences'
    )
    text = models.TextField(help_text="Текст доказательства или обоснования")
    source = models.CharField(max_length=255, help_text="Источник доказательства (статья, патент, отчёт)")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.source}: {self.text[:50]}..."


class RoadmapStep(models.Model):
    hypothesis = models.ForeignKey(Hypothesis, on_delete=models.CASCADE, related_name='roadmap_steps')
    name = models.CharField(max_length=200)
    duration = models.CharField(max_length=50)
    risk_level = models.CharField(max_length=20)
    order = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return f"{self.name} ({self.duration})"