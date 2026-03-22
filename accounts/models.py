from django.contrib.auth.models import AbstractUser
from django.db import models


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
    


