# -*- coding: utf-8 -*-
from django.shortcuts import render
from disease import models as models_disease

def diabetes(request):
    from collections import OrderedDict
    mortality_years = models_disease.MortalityYears.objects.all().order_by("-year", "-amount")
    mortality_list = OrderedDict()
    years = list(range(2000, 2014))
    years.reverse()
    disease_relate = set([
        u"Enfermedades isquémicas del corazón",
        "Enfermedad cerebrovascular",
        "Enfermedades hipertensivas",
        "Nefritis y nefrosis"])
    for mortality in mortality_years:
        mortality_list.setdefault(mortality.causa_mortality.description, [])
        mortality_list[mortality.causa_mortality.description].append(mortality.amount)
    for k, amount in mortality_list.items():
        growth_rate = round((((amount[0]/float(amount[-1]))**(1/13.)) - 1) * 100, 2)
        mortality_list[k].append(growth_rate)
    return render(request, "diabetes.html", {
        "years": years, 
        "mortality_list": mortality_list,
        "disease_relate": disease_relate})
