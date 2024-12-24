from rest_framework import serializers
from .models import NormalMatch

class BaseMatchSerializer(serializers.ModelSerializer):
    class Meta:
        fields = [
            'left_player',
            'right_player',
            'left_player_score',
            'right_player_score',
            'winner',
            'state',
            'created_at',
        ]
        
class NormalMatchSerializer(BaseMatchSerializer):
    class Meta(BaseMatchSerializer.Meta):
        model = NormalMatch
        fields = ['id'] + BaseMatchSerializer.Meta.fields