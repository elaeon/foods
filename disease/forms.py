# -*- coding: utf-8 -*-
from django import forms
from disease import models as models_disease

class RiskFactorForm(forms.Form):
    agent = forms.ModelChoiceField(label="Agente causante",
            queryset=models_disease.CancerAgent.objects.all().order_by("name_es"),
            required=False)
    cancer = forms.ModelChoiceField(label="Tipo de cáncer",
            queryset=models_disease.Cancer.objects.all().order_by("name_es"),
            required=False)
