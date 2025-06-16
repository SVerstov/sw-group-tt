# Create your views here.
from django_filters.rest_framework.backends import DjangoFilterBackend
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from mis.models import Consultations
from mis import serializers, models


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user and request.user.is_authenticated:
            return request.user.role == "admin" or request.user.is_staff
        return False


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            return request.user.role == "admin" or request.user.is_staff
        return False


class PatientsViewSet(viewsets.ModelViewSet):
    queryset = models.Patients.objects.filter(user__role="patient")
    serializer_class = serializers.PatientSerializer
    permission_classes = [IsAdmin]


class DoctorsViewSet(viewsets.ModelViewSet):
    queryset = models.Doctors.objects.all()
    serializer_class = serializers.DoctorSerializer
    permission_classes = [IsAdmin]


class ClinicsViewSet(viewsets.ModelViewSet):
    queryset = models.Clinics.objects.all()
    serializer_class = serializers.ClinicSerializer
    permission_classes = [IsAdminOrReadOnly]


class ConsultationViewSet(viewsets.ModelViewSet):
    queryset = models.Consultations.objects.all()
    serializer_class = serializers.ConsultationsSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "created_at", "doctor__user__last_name", "patient__user__last_name"]
    search_fields = ["doctor__user__last_name", "patient__user__last_name"]
    ordering_fields = ['created_at', 'start_time']

    @action(detail=True, methods=["post"])
    def change_status(self, request, pk=None):
        consultation = self.get_object()
        new_status = request.data.get("status")
        if new_status not in dict(Consultations.STATUS_CHOICES):
            return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)
        consultation.status = new_status
        consultation.save()
        return Response({"status": "Status updated"})
