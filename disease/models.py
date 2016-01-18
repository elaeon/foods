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

class CancerAgent(models.Model):
    name = models.CharField(max_length=100)
    name_es = models.CharField(max_length=100, blank=True, null=True)
    exposition_in = models.CharField(max_length=100, blank=True, null=True)
    nivel = models.CharField(max_length=10)

    def __unicode__(self):
        return self.name

class Cancer(models.Model):
    name = models.CharField(max_length=100, unique=True)
    name_es = models.CharField(max_length=100, blank=True, null=True)
    organ = models.CharField(max_length=100, blank=True, null=True)

    def actual_survival_rate(self):
        try:
            return self.cancer5yrsurvivalrate_set.get(period="2005-2011").percentaje
        except Cancer5yrSurvivalRate.DoesNotExist:
            return None

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('name',)

class CancerAgentRelation(models.Model):
    cancer = models.ForeignKey(Cancer)
    agent = models.ForeignKey(CancerAgent)

class Cancer5yrSurvivalRate(models.Model):
    period = models.CharField(max_length=100)
    cancer = models.ForeignKey(Cancer)
    percentaje = models.FloatField()

    def __unicode__(self):
        return self.period
