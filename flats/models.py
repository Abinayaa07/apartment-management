# from django.db import models

# Create your models here.
from django.db import models


class Flat(models.Model):

    block = models.CharField(max_length=10)
    number = models.CharField(max_length=10)
    floor = models.IntegerField()

    def __str__(self):
        return f"{self.block}-{self.number}"