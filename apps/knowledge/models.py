from django.db import models

class KnowledgeDocument(models.Model):
    TYPE_CHOICES = [
        ('paper', 'Научная статья'),
        ('patent', 'Патент'),
        ('report', 'Внутренний отчет'),
        ('dataset', 'Датасет'),
    ]
    STATUS_CHOICES = [
        ('pending', 'В очереди'),
        ('processing', 'Обработка'),
        ('completed', 'Завершено'),
        ('failed', 'Ошибка'),
    ]

    doc_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    meta = models.CharField(max_length=255, blank=True)
    abstract = models.TextField()
    tags = models.JSONField(default=list)
    file = models.FileField(upload_to='knowledge/', blank=True, null=True)

    # Поля для отслеживания статуса обработки
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress = models.PositiveSmallIntegerField(default=0, help_text="Прогресс обработки 0-100%")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title