from .models import *
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'role',
            'is_active',
        ]



class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role', 'is_active']
        extra_kwargs = {
            'password': {'write_only': True},
            'role': {'read_only': True, 'default': 'member'},
            'is_active': {'read_only': True},
        }

    def validate_password(self, value):
        validate_password(value)  # اینجا بررسی امنیتی انجام میشه
        return value

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
            role='member',
            is_active=True
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
