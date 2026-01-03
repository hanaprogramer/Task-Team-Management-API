from .models import *
from .serializers import *
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q
from apps.projects.models import *
from apps.teams.models import *
from django.shortcuts import get_object_or_404

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status


class TasksViewSet(ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    from django.db.models import Q

    def get_queryset(self):
        user = self.request.user

    # 1) queryset اصلی: فقط تسک‌هایی که کاربر اجازه دیدن دارد
        qs = Task.objects.filter(
            Q(project__team__owner=user) | Q(project__team__members=user)
        ).distinct()

    # 2) فیلتر status
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)

    # 3) فیلتر assigned_to=me
        assigned_to_param = self.request.query_params.get('assigned_to')
        if assigned_to_param == "me":
            qs = qs.filter(assigned_to=user)

        return qs


    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


    def perform_update(self, serializer):
        user = self.request.user
        task = serializer.instance
        team = task.project.team

        # فقط owner تیم یا اعضای تیم می‌تونن آپدیت کنن
        if user != team.owner and not team.members.filter(id=user.id).exists():
            raise PermissionDenied("You do not have permission to update this task")

        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        team = instance.project.team

        # فقط owner تیم یا اعضای تیم می‌تونن حذف کنن
        if user != team.owner and not team.members.filter(id=user.id).exists():
            raise PermissionDenied("You do not have permission to delete this task")

        instance.delete()
#--------------------------comment------------------------------
class CommentViewSet(ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Comment.objects.filter(Q(author = user)|
                                      Q(task__project__team__owner = user)|
                                      Q(task__project__team__members = user)|
                                      Q(task__assigned_to = user)).select_related('task','author').distinct()
    
    def perform_create(self, serializer):
        task_id = self.kwargs.get("task_id")

    # 1) Task must exist
        task = get_object_or_404(Task, id=task_id)

        user = self.request.user
        team = task.project.team

    # 2) User must have access to this task's team/project
        if user != team.owner and not team.members.filter(id=user.id).exists() and user != task.assigned_to:
            raise PermissionDenied("You do not have permission to comment on this task.")

        serializer.save(author=user, task=task)


    def perform_update(self, serializer):
        if serializer.instance.author != self.request.user:
            raise PermissionDenied("You can only update your own comments")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            raise PermissionDenied("You can only delete your own comments")
        instance.delete()

#------------------------filtering---------------------------------
