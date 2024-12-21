from rest_framework import serializers
from .models import Reception
from config.services import UserService
from asgiref.sync import async_to_sync

class ReceptionSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=False,
        style={'input_type': 'password'},
        max_length=20,
    )
    has_password = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Reception
        fields = ['id', 'name', 'password', 'has_password']
        extra_kwargs = {
            'name': {'required': True},
        }
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        reception = Reception(**validated_data)
        reception.set_password(password)
        reception.save()
        return reception
    
    def get_has_password(self, obj):
        return obj.has_password
    
class ReceptionJoinSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=20, required=False, allow_null=True, allow_blank=False)
    
class ReceptionInvitationSerializer(serializers.Serializer):
    to_user_id = serializers.IntegerField(required=True)
    
    def validate_to_user_id(self, value):
        token = self.context.get('token')
        if not token:
            raise serializers.ValidationError("Token missing.")
        if not async_to_sync(UserService.get_user)(value, token):
            raise serializers.ValidationError("User does not exist.")
        if value == self.context['from_user_id']:
            raise serializers.ValidationError("You cannot invite yourself.")
        return value