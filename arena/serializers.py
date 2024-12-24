from rest_framework import serializers
from .models import NormalMatch

class BaseMatchSerializer(serializers.ModelSerializer):
    class Meta:
        fields = [
            'left_player',
            'right_player',
            'left_score',
            'right_score',
            'winner',
            'state',
            'created_at',
        ]
        
class NormalMatchSerializer(BaseMatchSerializer):
    class Meta(BaseMatchSerializer.Meta):
        model = NormalMatch
        fields = ['id'] + BaseMatchSerializer.Meta.fields