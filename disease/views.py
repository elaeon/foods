# -*- coding: utf-8 -*-
from django.shortcuts import render
from disease import models as models_disease


def index(request):
    return render(request, "enfermedades.html", {})

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

def cancer(request):
    from collections import OrderedDict
    mortality_years = models_disease.MortalityYears.objects.all().order_by("-year", "-amount")
    mortality_list = OrderedDict()
    years = list(range(2000, 2014))
    years.reverse()
    for mortality in mortality_years:
        mortality_list.setdefault(mortality.causa_mortality.description, [])
        mortality_list[mortality.causa_mortality.description].append(mortality.amount)
    for k, amount in mortality_list.items():
        growth_rate = round((((amount[0]/float(amount[-1]))**(1/13.)) - 1) * 100, 2)
        mortality_list[k].append(growth_rate)
    return render(request, "cancer.html", {
        "years": years, 
        "mortality_list": mortality_list})

def cancer_risk_factor(request):
    from django.db.models import Count
    from disease.forms import RiskFactorForm
    
    cancer_resumen = models_disease.CancerAgent.objects.all().annotate(
            total=Count('canceragentrelation')).order_by('-total', 'name')

    result = None
    if request.POST:
        rf_form = RiskFactorForm(request.POST)
        if rf_form.is_valid():
            agent = rf_form.cleaned_data["agent"]
            cancer = rf_form.cleaned_data["cancer"]
            if agent is not None:
                result = agent.canceragentrelation_set.all()
                init_result = False
            else:
                result = cancer.canceragentrelation_set.all()
                init_result = False
    else:
        rf_form = RiskFactorForm()
        init_result = True
    
    return render(request, "cancer_risk_factor.html", {
        "rf_form": rf_form,
        "cancer_resumen": cancer_resumen,
        "init_result": init_result,
        "result": result
        })
