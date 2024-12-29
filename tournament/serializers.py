from rest_framework import serializers
from .models import Tournament, TournamentMatch
from arena.serializers import BaseMatchSerializer

class TournamentSerializer(serializers.ModelSerializer):
    current_participants = serializers.ReadOnlyField()
    total_rounds = serializers.ReadOnlyField()
    creator = serializers.CharField(max_length=30, read_only=True)
    
    class Meta:
        model = Tournament
        fields = [
            'id',
            'name',
            'creator',
            'max_participants',
            'winner',
            'created_at',
            'state',
            'current_participants',
            'total_rounds'
        ]
    
    def validate_max_participants(self, value):
        if not Tournament.is_valid_participants(value):
            raise serializers.ValidationError("Invalid max_participants.")
        return value
    
    def create(self, validated_data):
        validated_data['creator'] = self.context['request'].user_id
        return super().create(validated_data)
    

class TournamentMatchSerializer(BaseMatchSerializer):
    round = serializers.IntegerField(read_only=True)
    match_number = serializers.IntegerField()
    state = serializers.CharField(max_length=20)