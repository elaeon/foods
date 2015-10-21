from django.db import models
from sorl.thumbnail import ImageField as sorl_ImageField

class SatietyIndex(models.Model):
    ndb_no_t = models.TextField(unique=True)
    percent = models.FloatField()
    base = models.BooleanField()

    def __unicode__(self):
        return self.ndb_no_t

class NutrDesc(models.Model):
    nutr_no_t = models.TextField(unique=True)
    desc = models.TextField(blank=True, null=True)
    group = models.TextField()    
    essencial = models.BooleanField(default=False)

    def __unicode__(self):
        return self.nutr_no_t

class FoodDescImg(models.Model):
    ndb_no_t = models.TextField(unique=True)
    img = sorl_ImageField(upload_to="food/")

    def __unicode__(self):
        return self.ndb_no_t

# Create your models here.
#class Recipe(models.Model):
#    name = models.TextField()
#    tiempo_de_preparacion = models.TimeField()
#    tiempo_de_recalendato = models.TimeField()

#class RecipeIngredient(models.Model):
#    recipe = models.ForeignKey(Recipe)
#    ndb_no = models.ForeignKey()
#    weight = models.FloatField()

#class Menu(models.Model):
#    name = models.TextField()
#    recipe = models.ManyToMany(Recipe) 
