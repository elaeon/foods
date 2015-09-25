from django.db import models

class CausaMortality(models.Model):
    description = models.CharField(max_length=100)
    cie_10 = models.CharField(max_length=50, unique=True)

    def __unicode__(self):
        return self.description


class MortalityYears(models.Model):
    causa_mortality = models.ForeignKey(CausaMortality)
    year = models.PositiveIntegerField()
    amount = models.PositiveIntegerField()

    def __unicode__(self):
        return self.causa_mortality.__unicode__()

    class Meta:
        unique_together = ("causa_mortality", "year")
