from django.contrib import admin
from models import LabGroup, License, Compound, ChemicalClass 
from forms import LabGroupForm, CompoundAdminForm

class LabGroupAdmin(admin.ModelAdmin):
  form = LabGroupForm

def licenseSnippet(license):
  return license.text[:100] + '...'

licenseSnippet.short_description = 'License Snippet'

class LicenseAdmin(admin.ModelAdmin):

  list_display = (licenseSnippet, 'effectiveDate')

class CompoundAdmin(admin.ModelAdmin):
  form = CompoundAdminForm

  list_display = ('abbrev', 'name', 'csid', 'custom', 'labGroup')

class ChemicalClassAdmin(admin.ModelAdmin):
  
  list_display = ('label', 'description')

admin.site.register(LabGroup, LabGroupAdmin)
admin.site.register(License, LicenseAdmin)
admin.site.register(Compound, CompoundAdmin)
admin.site.register(ChemicalClass, ChemicalClassAdmin)
