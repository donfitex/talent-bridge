from django.utils import timezone
from rest_framework import decorators, permissions, serializers, viewsets
from apps.common.responses import APIResponse
from apps.notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "subject", "message", "read_at", "created_at"]
        read_only_fields = fields


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @decorators.action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        item = self.get_object()
        if not item.read_at:
            item.read_at = timezone.now()
            item.save(update_fields=["read_at", "updated_at"])
        return APIResponse(data=self.get_serializer(item).data)
