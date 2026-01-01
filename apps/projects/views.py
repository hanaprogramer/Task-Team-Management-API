from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q

from .models import Project
from .serializers import ProjectsSerializer


class ProjectsView(ModelViewSet):
    serializer_class = ProjectsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(
            Q(team__owner=user) | Q(team__members=user)
        ).distinct()

    def perform_create(self, serializer):
        # تمام چک‌های دسترسی توی serializer انجام شده
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        project = serializer.instance
        user = self.request.user

        if user != project.team.owner and user != project.created_by:
            raise PermissionDenied("Only team owner or project creator can update project")

        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if user != instance.team.owner:
            raise PermissionDenied("Only team owner can delete project")
        instance.delete()
