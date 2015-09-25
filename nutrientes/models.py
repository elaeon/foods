from django.db import models

class SatietyIndex(models.Model):
    ndb_no_t = models.TextField(unique=True)
    percent = models.FloatField()
    base = models.BooleanField()

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
