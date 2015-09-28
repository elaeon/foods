from django.shortcuts import render
from disease import models as models_disease

def diabetes(request):
    from collections import OrderedDict
    mortality_years = models_disease.MortalityYears.objects.all().order_by("-year", "-amount")
    mortality_list = OrderedDict()
    years = list(range(2000, 2014))
    years.reverse()
    for mortality in mortality_years:
        mortality_list.setdefault(mortality.causa_mortality.description, [])
        mortality_list[mortality.causa_mortality.description].append(mortality.amount)
    return render(request, "diabetes.html", {"years": years, "mortality_list": mortality_list})
