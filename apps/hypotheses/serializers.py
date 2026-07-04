from rest_framework import serializers
from .models import Hypothesis, Evidence, RoadmapStep

class EvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evidence
        fields = ['id', 'text', 'source', 'created_at']


class RoadmapStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoadmapStep
        fields = ['id', 'name', 'duration', 'risk_level', 'order']


class HypothesisSerializer(serializers.ModelSerializer):
    evidences = EvidenceSerializer(many=True, read_only=True)
    roadmap_steps = RoadmapStepSerializer(many=True, read_only=True)
    object_name = serializers.SerializerMethodField()

    class Meta:
        model = Hypothesis
        fields = [
            'id', 'object', 'object_name', 'title', 'description', 'status',
            'novelty_score', 'feasibility_score', 'research_cost',
            'economic_benefit', 'payback_months', 'roi', 'complexity_data',
            'evidences', 'roadmap_steps', 'created_at'
        ]

    def get_object_name(self, obj):
        return obj.object.name if obj.object else "Без привязки к объекту"