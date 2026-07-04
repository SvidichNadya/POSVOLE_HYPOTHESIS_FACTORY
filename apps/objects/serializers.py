from rest_framework import serializers
from .models import ResearchObject, Metric, Bottleneck, Strength, SliderParameter

class MetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = Metric
        fields = ['id', 'name', 'current_value', 'target_value', 'unit']

class BottleneckSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bottleneck
        fields = ['id', 'description']

class StrengthSerializer(serializers.ModelSerializer):
    class Meta:
        model = Strength
        fields = ['id', 'description']

class SliderParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = SliderParameter
        fields = ['id', 'name', 'key', 'min_value', 'max_value', 'step', 'default_value', 'unit']

class ResearchObjectSerializer(serializers.ModelSerializer):
    metrics = MetricSerializer(many=True, read_only=True)
    bottlenecks = BottleneckSerializer(many=True, read_only=True)
    strengths = StrengthSerializer(many=True, read_only=True)
    sliders = SliderParameterSerializer(many=True, read_only=True)

    class Meta:
        model = ResearchObject
        fields = ['id', 'name', 'description', 'status', 'metrics', 'bottlenecks', 'strengths', 'sliders']