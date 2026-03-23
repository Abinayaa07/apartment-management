from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):

    ROLE_CHOICES = (
        ('resident', 'Resident'),
        ('security', 'Security'),
        ('staff', 'Staff'),
        ('admin', 'Admin'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=15)
    block_name = models.CharField(max_length=20, blank=True)
    flat_number = models.CharField(max_length=20, blank=True)
    vehicle_number = models.CharField(max_length=20, blank=True)
    id_proof = models.FileField(upload_to="resident_docs/id_proofs/", null=True, blank=True)
    address_proof = models.FileField(upload_to="resident_docs/address_proofs/", null=True, blank=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.username


class FamilyMember(models.Model):
    GENDER_CHOICES = (
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    )

    resident = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="family_members",
        limit_choices_to={"role": "resident"},
    )
    member_name = models.CharField(max_length=120)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    relationship = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    kyc_document = models.FileField(upload_to="resident_docs/family_kyc/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["member_name"]

    def __str__(self):
        return f"{self.member_name} ({self.resident.username})"

    @property
    def age(self):
        today = timezone.localdate()
        years = today.year - self.date_of_birth.year
        if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
            years -= 1
        return years


