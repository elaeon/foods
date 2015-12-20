from django.contrib import admin
from disease.models import MortalityYears

class MortalityYearsAdmin(admin.ModelAdmin):
    list_display = ('causa_mortality', 'year', 'amount')

admin.site.register(MortalityYears, MortalityYearsAdmin)
