from rest_framework import serializers
from mis.models import Consultations, Doctors, Patients, Clinics, Users


def _ensure_username_or_generate(fields: dict):
    if fields.get("username"):
        return

    base = f"{fields.get("last_name")}_{fields.get("first_name")[0]}{fields.get("middle_name")[0]}"
    username = base
    counter = 1
    while Users.objects.filter(username=username).exists():
        username = f"{base}_{counter}"
        counter += 1
    fields["username"] = username


class ClinicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clinics
        fields = "__all__"


class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ("id", "first_name", "last_name", "middle_name", "email")


class PatientSerializer(serializers.ModelSerializer):
    user = UsersSerializer()

    class Meta:
        model = Patients
        fields = "__all__"

    def create(self, validated_data):
        user_data = validated_data.pop("user")
        _ensure_username_or_generate(user_data)
        user = Users.objects.create_user(**user_data)
        patient = Patients.objects.create(user=user, **validated_data)
        return patient

    def update(self, instance, validated_data):
        super().update(instance.user, validated_data.pop("user"))
        super().update(instance, validated_data)
        return instance


class DoctorSerializer(serializers.ModelSerializer):
    user = UsersSerializer()
    read_only = True

    class Meta:
        model = Doctors
        fields = "__all__"

    def create(self, validated_data):
        user_data = validated_data.pop("user")
        clinics_data = validated_data.pop("clinics", [])
        _ensure_username_or_generate(user_data)
        user = Users.objects.create_user(**user_data)
        doctor = Doctors.objects.create(user=user, **validated_data)
        doctor.clinics.set(clinics_data)
        return doctor

    def update(self, instance, validated_data):
        super().update(instance.user, validated_data.pop("user"))
        super().update(instance, validated_data)
        return instance


class ConsultationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consultations
        fields = ("doctor", "patient", "clinic", "start_time", "end_time", "status", "created_at", "notes")
