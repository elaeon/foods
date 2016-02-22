from django.core.management.base import BaseCommand

from nutrientes.utils import get_food_all_nutr_intake

class Command(BaseCommand):
    def handle(self, *args, **options):
        for e in get_food_all_nutr_intake():
            print(e)
