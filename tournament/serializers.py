from rest_framework import serializers
from .models import Tournament

class TournamentSerializer(serializers.ModelSerializer):
    current_participants = serializers.SerializerMethodField()
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
        
    def get_current_participants(self, obj):
        return obj.tournamentparticipant_set.count()
    
    def validate_max_participants(self, value):
        if not Tournament.is_valid_participants(value):
            raise serializers.ValidationError("Invalid max_participants.")
        return value
    
    def create(self, validated_data):
        validated_data['creator'] = self.context['request'].user_id
        return super().create(validated_data)