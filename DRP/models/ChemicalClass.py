'''A module containing only the ChemicalClass class'''
from django.db import models
from django.conf import settings

class ChemicalClass(models.Model):

  class Meta:
    app_label='DRP'
    verbose_name_plural='Chemical Classes'

  label=models.CharField(max_length=30, unique=True, error_messages={'unique':'A chemical class with this label already exists'}, choices=settings.CHEMICAL_CLASS_CHOICES)
  description=models.CharField(max_length=20)