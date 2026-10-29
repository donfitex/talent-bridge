from rest_framework import permissions, serializers, viewsets
from apps.applications.access import employer_applications
from apps.common.permissions import IsEmployerUser
from apps.interviews.models import Interview
from apps.interviews.services import InterviewService


class InterviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interview
        fields = ["id", "application", "interviewer", "starts_at", "ends_at", "location", "status", "feedback", "created_at"]
        read_only_fields = ["id", "created_at"]


class CandidateInterviewSerializer(InterviewSerializer):
    class Meta(InterviewSerializer.Meta):
        fields = [f for f in InterviewSerializer.Meta.fields if f != "feedback"]
        read_only_fields = fields


class InterviewViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_serializer_class(self):
        return CandidateInterviewSerializer if self.request.user.is_candidate else InterviewSerializer

    def get_permissions(self):
        if self.action in {"create", "partial_update"}:
            return [IsEmployerUser()]
        return super().get_permissions()

    def get_queryset(self):
        qs = Interview.objects.select_related("application__job", "interviewer")
        if self.request.user.is_candidate:
            return qs.filter(application__candidate__user=self.request.user)
        return qs.filter(application__in=employer_applications(self.request.user))

    def perform_create(self, serializer):
        data = dict(serializer.validated_data)
        data.pop("status", None)
        data.pop("feedback", None)
        serializer.instance = InterviewService.schedule(self.request.user, data)

    def perform_update(self, serializer):
        if set(serializer.validated_data) - {"status", "feedback"}:
            raise serializers.ValidationError("Cancel and create a new interview to reschedule.")
        serializer.instance = InterviewService.update(self.request.user, self.get_object(), serializer.validated_data)
