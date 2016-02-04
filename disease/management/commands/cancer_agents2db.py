from django.core.management.base import BaseCommand
from optparse import make_option
from django.conf import settings

from disease import models as m_disease
import csv

class Command(BaseCommand):
    def handle(self, *args, **options):
        with open('{}/data/causas_cancer.csv'.format(settings.BASE_DIR), 'rb') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                cancer, _ = m_disease.Cancer.objects.get_or_create(name=row[0])
                agent, _ = m_disease.CancerAgent.objects.get_or_create(name=row[1].strip(), nivel=1)
                m_disease.CancerAgentRelation.objects.get_or_create(cancer=cancer, agent=agent)
                print(row)
