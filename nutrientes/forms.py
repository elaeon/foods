# -*- coding: utf-8 -*-
from django import forms
from nutrientes.utils import RNV_TYPE

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
    rnv_type = forms.ChoiceField(
        choices=(RNV_TYPE.items()))

    def export_perfil(self):
        return {
            "edad": self.cleaned_data["edad"], 
            "unidad_edad": self.cleaned_data["unidad_edad"], 
            "genero": self.cleaned_data["genero"], 
            "rnv_type": self.cleaned_data["rnv_type"]}

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

class CategoryForm(forms.Form):
    key = forms.CharField(widget=forms.HiddenInput())
    check = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super(CategoryForm, self).__init__(*args, **kwargs)
        if 'initial' in kwargs:
            self.key = kwargs['initial'].get('key')
            self.food_type = kwargs['initial'].get('food_type')

class WeightFoodForm(forms.Form):
    key = forms.CharField(widget=forms.HiddenInput())
    check = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super(WeightFoodForm, self).__init__(*args, **kwargs)
        if 'initial' in kwargs:
            self.key = kwargs['initial'].get('key')
            self.name = kwargs['initial'].get('name')

#from django.forms.extras.widgets import SelectWidget
class OmegaRadioForm(forms.Form):
    radio_omega = forms.BooleanField(required=False)
    data_size = forms.ChoiceField(choices=[(i,i) for i in range(10, 60, 10)])
