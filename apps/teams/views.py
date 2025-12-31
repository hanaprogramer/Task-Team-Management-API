from django.db.models import Q
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from .models import Teams
from .serializers import TeamSerialiser



class TeamsView(ModelViewSet):
    serializer_class = TeamSerialiser
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Teams.objects.filter(
            Q(owner=user) | Q(members=user)
        ).distinct().select_related('owner').prefetch_related('members')


    def perform_update(self, serializer):
        """
        فقط مالک تیم می‌تواند آن را ویرایش کند
        """
        if serializer.instance.owner != self.request.user:
            raise PermissionDenied("You can only update your own teams")
        serializer.save()

    def perform_destroy(self, instance):
        """
        فقط مالک تیم می‌تواند آن را حذف کند
        """
        if instance.owner != self.request.user:
            raise PermissionDenied("You can only delete your own teams")
        instance.delete()