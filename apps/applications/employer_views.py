import csv
from django.http import HttpResponse
from rest_framework import decorators, viewsets
from drf_spectacular.utils import extend_schema
from apps.common.permissions import IsEmployerUser
from apps.common.responses import APIResponse
from apps.applications.access import employer_applications
from apps.applications.serializers import EmployerApplicationSerializer, StatusTransitionSerializer
from apps.applications.services import ApplicationTransitionService


def csv_cell(value):
    value = str(value)
    return "'" + value if value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")) else value


class EmployerApplicationViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsEmployerUser]
    serializer_class = EmployerApplicationSerializer
    filterset_fields = ["job", "status"]
    search_fields = ["candidate__user__email", "candidate__user__first_name", "candidate__user__last_name"]
    ordering_fields = ["created_at", "status"]

    def get_queryset(self):
        return employer_applications(self.request.user)

    @extend_schema(request=StatusTransitionSerializer, responses=EmployerApplicationSerializer)
    @decorators.action(detail=True, methods=["post"])
    def transition(self, request, pk=None):
        application = self.get_object()
        serializer = StatusTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = ApplicationTransitionService.transition(request.user, application.pk,
            serializer.validated_data["status"], serializer.validated_data.get("note", ""))
        return APIResponse(data=self.get_serializer(result).data)

    @decorators.action(detail=False, methods=["get"])
    def export(self, request):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="applications.csv"'
        response["Cache-Control"] = "no-store"
        writer = csv.writer(response)
        writer.writerow(["Application", "Job", "Candidate", "Email", "Status", "Applied at"])
        for app in self.filter_queryset(self.get_queryset()).iterator(chunk_size=500):
            writer.writerow([csv_cell(v) for v in [app.pk, app.job.title,
                app.candidate.user.get_full_name(), app.candidate.user.email, app.status, app.created_at]])
        return response
