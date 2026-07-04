from django.db import models
from django.contrib.auth.models import User

class ResearchProject(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=50, default='planning')
    progress = models.IntegerField(default=0)

    # Привязки
    object = models.ForeignKey('objects.ResearchObject', on_delete=models.SET_NULL, null=True, blank=True)
    hypothesis = models.ForeignKey('hypotheses.Hypothesis', on_delete=models.SET_NULL, null=True, blank=True)

    # Ресурсы и Чек-лист
    available_resources = models.TextField(blank=True)
    checklist = models.JSONField(default=list)   # ИИ-сгенерированный список шагов

    # ИИ-генерируемые показатели
    success_probability = models.FloatField(default=0.5)
    optimal_scenario = models.TextField(blank=True)
    pessimistic_scenario = models.TextField(blank=True)
    optimistic_scenario = models.TextField(blank=True)
    risks = models.TextField(blank=True)
    risk_mitigation = models.TextField(blank=True)
    analogs = models.TextField(blank=True, help_text="Конкретные примеры аналогов с названиями компаний, проектов или DOI")
    resources_needed = models.TextField(blank=True)

    # Бизнес-показатели
    business_roi = models.FloatField(default=0.0)
    business_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    business_payback = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name