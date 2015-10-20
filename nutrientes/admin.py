from django.contrib import admin

# Register your models here.
from django.contrib import admin
from nutrientes.models import FoodDescImg, NutrDesc
from sorl.thumbnail.admin import AdminImageMixin

class FoodDescImgAdmin(AdminImageMixin, admin.ModelAdmin):
    pass

admin.site.register(FoodDescImg, FoodDescImgAdmin)
admin.site.register(NutrDesc)
