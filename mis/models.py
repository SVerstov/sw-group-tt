from datetime import timedelta


from django.db import models
from django.contrib.auth.models import AbstractUser


class Clinics(models.Model):
    name = models.CharField("Название", max_length=100)
    legal_address = models.TextField("юридический адрес")
    actual_address = models.TextField("фактический адрес")

    def __str__(self):
        return self.name


class Users(AbstractUser):
    ROLE_CHOICES = (
        ("admin", "Администратор"),
        ("doctor", "Врач"),
        ("patient", "Пациент"),
    )

    role = models.CharField(choices=ROLE_CHOICES, default="patient")
    middle_name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name} ({self.role})"
        else:
            return f"{self.first_name} {self.last_name} ({self.role})"


class Doctors(models.Model):
    user = models.OneToOneField(
        Users,
        on_delete=models.CASCADE,
        related_name="doctor",
        limit_choices_to={"role": "doctor"},
    )
    clinics = models.ManyToManyField(Clinics, related_name="doctors")
    specialization = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.user} - {self.specialization}"


class Patients(models.Model):
    user = models.OneToOneField(
        Users,
        on_delete=models.CASCADE,
        related_name="patient",
        limit_choices_to={"role": "patient"},
    )
    phone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return str(self.user)


class Consultations(models.Model):
    STATUS_CHOICES = (
        ("waiting", "Ожидает"),
        ("confirmed", "Подтверждена"),
        ("started", "Начата"),
        ("finished", "Завершена"),
        ("paid", "Оплачена"),
    )

    doctor = models.ForeignKey(Doctors, on_delete=models.CASCADE, related_name="consultations")
    patient = models.ForeignKey(Patients, on_delete=models.CASCADE, related_name="consultations")
    clinic = models.ForeignKey(Clinics, on_delete=models.CASCADE, related_name="consultations")

    start_time = models.DateTimeField("Дата и время консультации", blank=False, null=False)
    end_time = models.DateTimeField("Время окончания консультации", blank=True, null=True)
    status = models.CharField(choices=STATUS_CHOICES, default="waiting", max_length=30, verbose_name="Статус")
    updated_at = models.DateTimeField("Последнее редактирование", auto_now=True)
    notes = models.TextField("Заметки", blank=True, null=True)

    class Meta:
        ordering = ["-start_time"]

    def save(self, *args, **kwargs):
        if self.start_time and not self.end_time or self.end_time < self.start_time:
            self.end_time = self.start_time + timedelta(minutes=30)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Консультация {self.start_time.strftime('%Y-%m-%d %H:%M')}.{self.doctor} => {self.patient}"
