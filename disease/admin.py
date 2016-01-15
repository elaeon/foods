from django.contrib import admin
from disease.models import MortalityYears, CancerAgent, CancerAgentRelation

class MortalityYearsAdmin(admin.ModelAdmin):
    list_display = ('causa_mortality', 'year', 'amount')

class CancerAgentAdmin(admin.ModelAdmin):
    search_fields = ["name", "name_es"]
    list_display = ('name', 'name_es', 'exposition_in')

admin.site.register(MortalityYears, MortalityYearsAdmin)
admin.site.register(CancerAgent, CancerAgentAdmin)
admin.site.register(CancerAgentRelation)
