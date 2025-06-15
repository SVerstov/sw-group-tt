from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView

from mis.views import ConsultationViewSet, PatientsViewSet, ClinicsViewSet, DoctorsViewSet

router = DefaultRouter()
router.register(r"clinics", ClinicsViewSet)
router.register(r"consultations", ConsultationViewSet)
router.register(r"users", PatientsViewSet)
router.register(r"doctors", DoctorsViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair')
]
