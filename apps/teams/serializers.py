from .models import *
from rest_framework import serializers
from apps.users.serializers import *
from django.utils import timezone

class TeamSerialiser(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    owner_detail = UserSerializer(source='owner', read_only=True)

    members = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True)
    members_detail = UserSerializer(source='members', many=True, read_only=True)

    class Meta:
        model = Teams
        fields = ['id', 'name', 'owner', 'owner_detail',
                  'members', 'members_detail', 'created_at']
    def validate_members(self, value):
        if len(value) < 1:
            raise serializers.ValidationError("A team must have at least one member.")
        return value
        