from .models import *
from .serializers import *
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q
class TasksViewSet(ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Task.objects.filter(
            Q(project__team__owner=user) | Q(project__team__members=user)
        ).distinct()


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
