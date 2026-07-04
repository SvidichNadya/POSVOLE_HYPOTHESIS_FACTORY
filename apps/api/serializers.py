# Общие сериализаторы для API, если потребуется агрегировать данные из разных приложений.
# В текущей реализации мы используем сериализаторы из соответствующих приложений,
# поэтому этот файл можно оставить пустым или с комментарием.
# Однако для будущего расширения можно определить здесь сериализаторы для комплексных ответов.

from rest_framework import serializers

# Пример: сериализатор для сводного дашборда (если будем использовать)
# class DashboardSerializer(serializers.Serializer):
#     top_hypothesis = serializers.DictField()
#     status_counts = serializers.DictField()
#     objects = serializers.ListField()
#     knowledge_stats = serializers.DictField()