# Create your views here.
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from mis.models import Consultations, Users
from mis import serializers, models


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user and request.user.is_authenticated:
            return request.user.role == "admin" or request.user.is_staff
        return False


class PatientsViewSet(viewsets.ModelViewSet):
    queryset = models.Patients.objects.filter(user__role="patient")
    serializer_class = serializers.PatientSerializer
    permission_classes = [permissions.IsAdminUser]


class DoctorsViewSet(viewsets.ModelViewSet):
    queryset = models.Doctors.objects.all()
    serializer_class = serializers.DoctorSerializer
    permission_classes = [permissions.IsAdminUser]


class ClinicsViewSet(viewsets.ModelViewSet):
    queryset = models.Clinics.objects.all()
    serializer_class = serializers.ClinicSerializer
    permission_classes = [IsAdminOrReadOnly]



class ConsultationViewSet(viewsets.ModelViewSet):
    queryset = models.Consultations.objects.all()
    serializer_class = serializers.ConsultationsSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ["status", "doctor__user__last_name", "patient__user__last_name"]
    search_fields = ["doctor__user__last_name", "patient__user__last_name"]

    @action(detail=True, methods=["post"])
    def change_status(self, request, pk=None):
        consultation = self.get_object()
        new_status = request.data.get("status")
        if new_status not in dict(Consultations.STATUS_CHOICES):
            return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)
        consultation.status = new_status
        consultation.save()
        return Response({"status": "Status updated"})
