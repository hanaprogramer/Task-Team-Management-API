from django.forms import ValidationError
from .models import *
from rest_framework import serializers
from apps.users.serializers import *
from django.utils import timezone
from apps.teams.serializers import *
from apps.teams.models import *
from apps.projects.models import *
from apps.projects.serializers import *
from datetime import date

class TaskSerializer(serializers.ModelSerializer):
    # ----------------------------
    # WRITE
    # ----------------------------
    project = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(),
        write_only=True
    )

    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )

    # ----------------------------
    # READ
    # ----------------------------
    project_detail = ProjectsSerializer(
        source='project',
        read_only=True
    )

    assigned_to_detail = UserSerializer(
        source='assigned_to',
        read_only=True
    )

    class Meta:
        model = Task
        fields = [
            'title',
            'description',
            'project',
            'project_detail',
            'assigned_to',
            'assigned_to_detail',
            'status',
            'priority',
            'due_date',
            'attachment'
        ]

    def validate(self, data):
        user = self.context['request'].user

        # ==================================================
        # CREATE
        # ==================================================
        if self.instance is None:
            project = data.get('project')
            team = project.team

            # 1. creator must be team owner or member
            if user != team.owner and not team.members.filter(id=user.id).exists():
                raise serializers.ValidationError(
                    "You do not have permission to create a task in this project."
                )

            # 2. assigned_to must be team member
            assigned_to = data.get('assigned_to')
            if assigned_to:    # Because the field was optional
                if assigned_to != team.owner and not team.members.filter(id=assigned_to.id).exists():
                    raise serializers.ValidationError(
                        "Assigned user must be a member of the team."
                    )

            # 3. due_date cannot be in the past
            due_date = data.get('due_date')
            if due_date and due_date < timezone.now().date():
                raise serializers.ValidationError(
                    "Due date cannot be in the past."
                )

            return data

        # ==================================================
        # UPDATE
        # ==================================================
        task = self.instance
        project = task.project
        team = project.team

        STRUCTURAL_FIELDS = ['title', 'description', 'due_date']
        EXECUTION_FIELDS = ['status', 'priority']

        changing_structural = any(field in data for field in STRUCTURAL_FIELDS)
        changing_execution = any(field in data for field in EXECUTION_FIELDS)

        # ---- structural fields ----
        if changing_structural:
            if user != task.created_by and user != team.owner:
                raise serializers.ValidationError(
                    "Only task creator or team owner can modify task details."
                )

        # ---- execution fields ----
        if changing_execution:
            if user != task.assigned_to and user != team.owner:
                raise serializers.ValidationError(
                    "Only assigned user or team owner can update task status or priority."
                )

        # ---- assigned_to change ----
        if 'assigned_to' in data:
            new_assigned = data['assigned_to']

            if user != team.owner:
                raise serializers.ValidationError(
                    "Only team owner can change task assignee."
                )

            if new_assigned:
                if new_assigned != team.owner and not team.members.filter(id=new_assigned.id).exists():
                    raise serializers.ValidationError(
                        "Assigned user must be a member of the team."
                    )

        # ---- due_date validation ----
        if 'due_date' in data:
            if data['due_date'] and data['due_date'] < timezone.now().date():
                raise serializers.ValidationError(
                    "Due date cannot be in the past."
                )

        return data
#-------------------------------comment-------------------------------
class CommentSerializer(serializers.ModelSerializer):
    task = serializers.PrimaryKeyRelatedField(read_only=True)
    task_detail = TaskSerializer(source = 'task', read_only=True)
    author = serializers.PrimaryKeyRelatedField(read_only=True)
    author_detail = UserSerializer(source = 'author', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'task', 'task_detail', 'author', 'author_detail', 'content', 'created_at']
        read_only_fields = ['id', 'task', 'author', 'created_at']
    
        