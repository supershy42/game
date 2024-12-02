from rest_framework import serializers
from .models import GameRoom

class GameRoomSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_null=True,
        allow_blank=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = GameRoom
        fields = ['id', 'name', 'password']
        extra_kwargs = {
            'name': {'required': True},
        }
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        room = GameRoom(**validated_data)
        room.set_password(password)
        room.save()
        return room