# Create your tests here.
# tests/test_api.py
from datetime import datetime, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from rest_framework.test import APIClient

from mis.models import Doctors, Patients, Clinics, Users, Consultations

import random


@pytest.fixture
def create_user():
    def _create_user(role="patient", password=None) -> Users:
        first_names = ["Alex", "Sam", "Chris", "Jordan", "Taylor"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones"]
        middle_names = ["Lee", "Pat", "Ray", "Drew", "Sky"]

        username = get_random_string(10)
        password = password or get_random_string(10)
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        middle_name = random.choice(middle_names)
        email = f"{get_random_string(10)}@example.com"

        return get_user_model().objects.create_user(
            username=username,
            password=password,
            role=role,
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
            email=email,
        )

    return _create_user


@pytest.mark.django_db
def test_jwt_login(create_user):
    client = APIClient()
    user = create_user(role="admin", password="testpass123")
    response = client.post("/api/token/", {"username": user.username, "password": "testpass123"})
    assert response.status_code == 200
    assert "access" in response.data


@pytest.mark.django_db
def test_jwt_login_wrong_pass(create_user):
    client = APIClient()
    user = create_user(role="admin", password="testpass123")
    response = client.post("/api/token/", {"username": user.username, "password": "WRONG"})
    assert response.status_code == 401


@pytest.fixture
def api_client_with_token(create_user):
    def _create_api_client(role="patient"):
        client = APIClient()
        password = get_random_string(10)
        user = create_user(role, password=password)
        response = client.post("/api/token/", {"username": user.username, "password": password})
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        return client, user

    return _create_api_client


@pytest.mark.django_db
def test_role_access(api_client_with_token):
    client_patient, _ = api_client_with_token("patient")
    response = client_patient.get("/api/consultations/")
    assert response.status_code == 403
    response = client_patient.get("/api/users/")
    assert response.status_code == 403

    client_admin, admin = api_client_with_token("admin")
    response = client_admin.get("/api/consultations/")
    assert response.status_code == 200
    response = client_admin.get("/api/users/")
    assert response.status_code == 200


@pytest.fixture
def doctor(create_user):
    user = create_user(role="doctor")
    return Doctors.objects.create(user=user, specialization="Терапевт")


@pytest.fixture
def create_doctor(create_user):
    def _create_doctor(specialization="Терапевт") -> Doctors:
        user = create_user(role="doctor")
        return Doctors.objects.create(user=user, specialization=specialization)

    return _create_doctor


@pytest.fixture
def patient(create_user):
    user = create_user(role="patient")
    return Patients.objects.create(user=user, phone=f"+7{random.randint(1000000000, 9999999999)}")


@pytest.fixture
def create_patient(create_user):
    def _create_patient(phone=None) -> Patients:
        user = create_user(role="patient")
        phone = phone or f"+7{random.randint(1000000000, 9999999999)}"
        return Patients.objects.create(user=user, phone=phone)

    return _create_patient


@pytest.fixture
def clinic():
    return Clinics.objects.create(name="Клиника 1", legal_address="Юр. адрес", actual_address="Физ. адрес")


@pytest.fixture
def create_clinic():
    def _create_clinic() -> Clinics:
        name = f"Клиника {get_random_string(5)}"
        legal_address = f"Юр адрес {get_random_string(10)}"
        actual_address = f"Физический адрес {get_random_string(10)}"
        return Clinics.objects.create(name=name, legal_address=legal_address, actual_address=actual_address)

    return _create_clinic


@pytest.fixture
def create_consultation():
    def _create_consultation(
        start_time: datetime | str,
        doctor: Doctors,
        patient: Patients,
        clinic: Clinics,
        status="waiting",
    ) -> Consultations:
        return Consultations.objects.create(
            doctor=doctor, patient=patient, clinic=clinic, start_time=start_time, status=status
        )

    return _create_consultation


@pytest.mark.django_db
def test_create_consultation(api_client_with_token, doctor, patient, clinic):
    client, user = api_client_with_token(role="admin")
    data = {
        "doctor": doctor.id,
        "patient": patient.id,
        "clinic": clinic.id,
        "start_time": "2025-06-20T10:00:00Z",
        "status": "waiting",
    }
    response = client.post("/api/consultations/", data)
    assert response.status_code == 201
    assert response.data["status"] == "waiting"


@pytest.mark.django_db
def test_deny_create_consultation(api_client_with_token, doctor, patient, clinic):
    client, user = api_client_with_token(role="patient")
    data = {
        "doctor": doctor.id,
        "patient": patient.id,
        "clinic": clinic.id,
        "start_time": "2025-06-20T10:00:00Z",
        "status": "waiting",
    }
    response = client.post("/api/consultations/", data)
    assert response.status_code == 403


@pytest.mark.django_db
def test_update_consultation_data(api_client_with_token, create_doctor, create_consultation, patient, clinic):
    doctor1 = create_doctor(specialization="Терапевт")
    doctor2 = create_doctor(specialization="Хирург")

    consultation = create_consultation(
        start_time=datetime.now() + timedelta(days=1), doctor=doctor1, patient=patient, clinic=clinic, status="waiting"
    )

    client, user = api_client_with_token(role="admin")

    new_data = {
        "doctor": doctor2.id,
        "patient": patient.id,
        "clinic": clinic.id,
        "start_time": "2026-06-20T10:00:00Z",
        "status": "confirmed",
    }
    response = client.put(f"/api/consultations/{consultation.id}/", new_data)

    assert response.status_code == 200

    consultation.refresh_from_db()
    assert consultation.status == new_data["status"]
    assert consultation.doctor.id == new_data["doctor"]


@pytest.fixture
@pytest.mark.django_db
def create_bunch_consultation(create_consultation, create_doctor, patient, clinic):
    doc1 = create_doctor()
    doc1.user.last_name = "Иванов"
    doc1.user.save()
    doc2 = create_doctor()
    doc2.user.last_name = "Петров"
    doc2.user.save()
    for i, status in enumerate(["waiting", "confirmed", "started", "finished", "paid"]):
        create_consultation(
            start_time=datetime.now() + timedelta(days=i),
            doctor=doc1 if i % 2 == 0 else doc2,
            patient=patient,
            clinic=clinic,
            status=status,
        )


@pytest.mark.django_db
def test_filter_consultations_by_status(api_client_with_token, create_bunch_consultation):
    client, user = api_client_with_token(role="admin")
    response = client.get("/api/consultations/?status=waiting")
    assert response.status_code == 200
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["status"] == "waiting"


@pytest.mark.django_db
def test_search_consultations_by_doctor_lastname(api_client_with_token, create_bunch_consultation):
    client, user = api_client_with_token(role="admin")
    response = client.get("/api/consultations/?search=Иванов&search_type=doctor")
    assert response.status_code == 200
    assert len(response.data["results"]) == 3
    response = client.get("/api/consultations/?search=Петров&search_type=doctor")
    assert response.status_code == 200
    assert len(response.data["results"]) == 2


@pytest.mark.django_db
def test_order_consultations_by_start_time(api_client_with_token, create_bunch_consultation):
    client, user = api_client_with_token(role="admin")
    # ASC order
    response = client.get("/api/consultations/?ordering=start_time")
    result = response.data["results"]
    assert datetime.fromisoformat(result[0]["start_time"]) < datetime.fromisoformat(result[1]["start_time"])

    # DESC order
    response = client.get("/api/consultations/?ordering=-start_time")
    result = response.data["results"]
    assert datetime.fromisoformat(result[0]["start_time"]) > datetime.fromisoformat(result[1]["start_time"])
