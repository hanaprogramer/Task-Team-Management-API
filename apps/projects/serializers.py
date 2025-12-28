from django.forms import ValidationError
from .models import *
from rest_framework import serializers
from apps.users.serializers import *
from django.utils import timezone
from apps.teams.serializers import *
from apps.teams.models import *
class ProjectsSerializer(serializers.ModelSerializer):
    team = serializers.PrimaryKeyRelatedField(queryset=Teams.objects.all())
    team_detail=TeamSerialiser(source='team',  read_only=True)

    created_by_detail = UserSerializer(source='created_by', read_only=True)

    class Meta:
        model=Project

        fields=['id', 'name', 'team', 'team_detail', 'created_by_detail']

    def validate_team(self, value):
        user = self.context['request'].user
        if not value:
            raise ValidationError("Defining a project is not possible without selecting a team.")

        team = value
        if user == team.owner or team.members.filter(id=user.id).exists():  # بهینه‌تر
            return value

        raise ValidationError("You do not have permission to create a project in this team.")

    def validate_team(self, value):
        if not value.is_active:
            raise ValidationError("Cannot create a project in an inactive team.")
        return value

    def validate_name(self, value):
        team = self.initial_data.get('team')
        if Project.objects.filter(name=value, team_id=team).exists():
            raise ValidationError("A project with this name already exists in the team.")
        return value
    
    def validate(self, data):
        start = data.get('start_date')
        end = data.get('end_date')
        if start and end and start > end:
            raise ValidationError("End date must be after start date.")
        return data
    
    

