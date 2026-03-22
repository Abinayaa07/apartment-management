# # from django.db import models

# # Create your models here.
# from django.db import models


# class Notice(models.Model):

#     title = models.CharField(max_length=200)
#     message = models.TextField()

#     created_at = models.DateTimeField(auto_now_add=True)

from django.db import models
from django.conf import settings


class Notice(models.Model):
    AUDIENCE_CHOICES = (
        ("all", "All"),
        ("staff", "Staff"),
        ("security", "Security"),
    )

    title = models.CharField(max_length=200)

    message = models.TextField()

    document = models.FileField(
        upload_to="notices/",
        null=True,
        blank=True
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    expiry_date = models.DateField(null=True, blank=True)

    audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES, default="all")

    def __str__(self):
        return self.title
