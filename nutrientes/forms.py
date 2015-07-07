# -*- coding: utf-8 -*-
from django import forms

class IntakeForm(forms.Form):
    edad = forms.IntegerField()
    unidad_edad = forms.ChoiceField( 
        choices=((u"meses", u"meses"), 
                (u"años", u"años")))
    genero = forms.ChoiceField(
        choices=(
            (u"H", u"hombre"),
            (u"M", u"mujer"),
            (u"pregnancy", u"mujer-embarazo"),
            (u"lactancy", u"mujer-lactancia")
        ))

class WeightForm(forms.Form):
    weight = forms.FloatField()
