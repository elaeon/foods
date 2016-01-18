from django.contrib import admin
from disease.models import MortalityYears, CancerAgent, CancerAgentRelation
from disease.models import Cancer5yrSurvivalRate, Cancer

class MortalityYearsAdmin(admin.ModelAdmin):
    list_display = ('causa_mortality', 'year', 'amount')

class CancerAgentAdmin(admin.ModelAdmin):
    search_fields = ["name", "name_es"]
    list_display = ('name', 'name_es', 'exposition_in')

admin.site.register(MortalityYears, MortalityYearsAdmin)
admin.site.register(CancerAgent, CancerAgentAdmin)
admin.site.register(CancerAgentRelation)
admin.site.register(Cancer5yrSurvivalRate)
admin.site.register(Cancer)
