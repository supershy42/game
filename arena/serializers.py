from rest_framework import serializers

class BaseMatchSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    unique_id = serializers.CharField(max_length=50, allow_null=True)
    left_player = serializers.JSONField(allow_null=True)
    right_player = serializers.JSONField(allow_null=True)
    left_player_score = serializers.IntegerField(default=0)
    right_player_score = serializers.IntegerField(default=0)
    winner = serializers.JSONField(allow_null=True)
    state = serializers.CharField(max_length=20)
    created_at = serializers.DateTimeField()
        
class NormalMatchSerializer(BaseMatchSerializer):
    def to_representation(self, instance):
        return super().to_representation(instance)