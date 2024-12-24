from rest_framework import serializers
from .models import Tournament, TournamentMatch
from arena.serializers import BaseMatchSerializer

class TournamentSerializer(serializers.ModelSerializer):
    current_participants = serializers.ReadOnlyField()
    total_rounds = serializers.ReadOnlyField()
    
    class Meta:
        model = Tournament
        fields = [
            'id',
            'name',
            'max_participants',
            'winner',
            'created_at',
            'state',
            'current_participants',
            'total_rounds'
        ]
        extra_kwargs = {
            'creator': {'read_only': True},
        }
    
    def validate_max_participants(self, value):
        if not Tournament.is_valid_participants(value):
            raise serializers.ValidationError("Invalid max_participants.")
        return value
    
    def create(self, validated_data):
        validated_data['creator'] = self.context['request'].user_id
        return super().create(validated_data)
    

class TournamentMatchSerializer(BaseMatchSerializer):
    class Meta(BaseMatchSerializer.Meta):
        model = TournamentMatch
        fields = BaseMatchSerializer.Meta.fields + [
            'tournament',
            'round',
            'match_number'
        ]