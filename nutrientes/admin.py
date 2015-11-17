from django.contrib import admin

# Register your models here.
from django.contrib import admin
from nutrientes.models import FoodDescImg, NutrDesc
from sorl.thumbnail.admin import AdminImageMixin

class FoodDescImgAdmin(AdminImageMixin, admin.ModelAdmin):
    list_display = ('ndb_no_t', 'name')


class NutrDescAdmin(admin.ModelAdmin):
    list_display = ('nutr_no_t', 'group', 'essencial')

admin.site.register(FoodDescImg, FoodDescImgAdmin)
admin.site.register(NutrDesc, NutrDescAdmin)
