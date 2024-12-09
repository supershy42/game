from rest_framework import serializers
from .models import Reception

class ReceptionSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_null=True,
        style={'input_type': 'password'},
        max_length=20,
    )
    
    class Meta:
        model = Reception
        fields = ['id', 'name', 'password']
        extra_kwargs = {
            'name': {'required': True},
        }
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        reception = Reception(**validated_data)
        reception.set_password(password)
        reception.save()
        return reception