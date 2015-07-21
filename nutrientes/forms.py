# -*- coding: utf-8 -*-
from django import forms

class PerfilIntakeForm(forms.Form):
    edad = forms.IntegerField()
    unidad_edad = forms.ChoiceField( 
        choices=((u"meses", u"meses"), 
                (u"años", u"años")))
    genero = forms.ChoiceField(
        choices=(
            (u"H", u"hombre"),
            (u"M", u"mujer"),
            (u"pregnancy", u"mujer-embarazo"),
            (u"lactation", u"mujer-lactancia")
        ))

class WeightForm(forms.Form):
    ndb_no = forms.CharField(widget=forms.HiddenInput())
    weight = forms.FloatField(widget=forms.NumberInput(attrs={"style": "width:50px;"}))

    def __init__(self, *args, **kwargs):
        super(WeightForm, self).__init__(*args, **kwargs)
        if 'initial' in kwargs:
            self.food = kwargs['initial'].get('food', '')

class MenuRecipeForm(forms.Form):
    recipe = forms.IntegerField(widget=forms.HiddenInput())
    weight = forms.FloatField(widget=forms.NumberInput(attrs={"style": "width:70px;"}))

    def __init__(self, *args, **kwargs):
        super(MenuRecipeForm, self).__init__(*args, **kwargs)
        if 'initial' in kwargs:
            self.name = kwargs['initial'].get('name', '')
