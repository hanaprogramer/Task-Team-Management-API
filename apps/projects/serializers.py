from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Project
from apps.teams.models import Teams
from apps.teams.serializers import TeamSerialiser
from apps.users.serializers import UserSerializer


class ProjectsSerializer(serializers.ModelSerializer):
    # ----------------------------
    # WRITE
    # ----------------------------
    team = serializers.PrimaryKeyRelatedField(queryset=Teams.objects.all())

    # ----------------------------
    # READ
    # ----------------------------
    team_detail = TeamSerialiser(source='team', read_only=True)
    created_by_detail = UserSerializer(source='created_by', read_only=True)

    class Meta:
        model = Project
        fields = [
            'id',
            'name',
            'team',
            'team_detail',
            'created_by_detail',
            'is_active',
            'start_date',
            'end_date',
        ]
        extra_kwargs = {
            'start_date': {'required': False, 'allow_null': True},
            'end_date': {'required': False, 'allow_null': True},
            'is_active': {'required': False},
        }

    # ==================================================
    # TEAM VALIDATION
    # ==================================================
    def validate_team(self, team):
        user = self.context['request'].user


        # CREATE: user must be owner/member
        if self.instance is None:
            if user == team.owner or team.members.filter(id=user.id).exists():
                return team
            raise ValidationError("You do not have permission to create a project in this team.")

        # UPDATE: only if team is being changed
        project = self.instance
        if team != project.team:
            if user != project.team.owner and user != project.created_by:
                raise ValidationError("Only team owner or project creator can change the team.")

        return team

    # ==================================================
    # NAME VALIDATION (unique within a team)
    # ==================================================
    def validate_name(self, value):
        team_id = self.initial_data.get('team')

        # In update, if team wasn't provided, use existing team
        if not team_id and self.instance:
            team_id = self.instance.team_id

        qs = Project.objects.filter(name=value, team_id=team_id)

        # Exclude current project on update
        if self.instance:
            qs = qs.exclude(id=self.instance.id)

        if qs.exists():
            raise ValidationError("A project with this name already exists in the team.")

        return value

    # ==================================================
    # DATE VALIDATION
    # ==================================================
    def validate(self, data):
        start = data.get('start_date')
        end = data.get('end_date')

        if start and end and start > end:
            raise ValidationError("End date must be after start date.")

        return data

    # ==================================================
    # is_active VALIDATION
    # ==================================================
    def validate_is_active(self, value):
        # Only for update
        if self.instance is None:
            return value

        # Only when changing the value
        if value != self.instance.is_active:
            user = self.context['request'].user
            project = self.instance

            if user != project.team.owner and user != project.created_by:
                raise ValidationError(
                    "Only the team owner or the project creator can change is_active."
                )

        return value
