from .models import *
from .serializers import *
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied


class ProjectsView(ModelViewSet):
    serializer_class = ProjectsSerializer
    permission_classes = [IsAuthenticated]


    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(
            team__owner=user
        ) | Project.objects.filter(
            team__members=user
        ).distinct()

    def perform_create(self, serializer):
        team = serializer.validated_data['team']
        user = self.request.user

        if user != team.owner and not team.members.filter(id=user.id).exists():
            raise PermissionDenied("Only team owner or team members can create projects")

        serializer.save(created_by=user)


    def perform_update(self, serializer):
        if serializer.instance.team.owner != self.request.user:
            raise PermissionDenied("Only team owner can update project")

        serializer.save()

    def perform_destroy(self, instance):
        if instance.team.owner != self.request.user:
            raise PermissionDenied("Only team owner can delete project")

        instance.delete()
    
