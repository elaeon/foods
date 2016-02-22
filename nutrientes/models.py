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
    name = models.CharField(max_length=255, blank=True, null=True)
    img = sorl_ImageField(upload_to="food/")
    ref_img = models.URLField(blank=True, null=True)

    def __unicode__(self):
        return self.ndb_no_t

class EnergyDensity(models.Model):
    ndb_no_t = models.TextField(unique=True)
    energy_density = models.FloatField()

    def __unicode__(self):
        return self.ndb_no_t

class NutrIntake(models.Model):
    nutr_no = models.CharField(max_length=3)
    type = models.TextField()
    genero = models.CharField(max_length=10)
    unidad_edad = models.CharField(max_length=10)
    value = models.FloatField()
    edad_range = models.CharField(max_length=10)
    rnv_type = models.IntegerField(db_index=True)

    def __unique__(self):
        return self.nutr_no

    class Meta:
        unique_together = ('nutr_no', 'type', 'genero', 'unidad_edad', 'edad_range')

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
