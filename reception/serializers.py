from rest_framework import serializers
from .models import Reception

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