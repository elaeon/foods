from django.core.management.base import BaseCommand

from nutrientes.utils import PiramidFood

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--meat',
            default=False,
            help='Select a meat in the piramid: beef, pork, luncheon, hunt')
        parser.add_argument('--categories',
            default='all',
            help='Select a category: all, meats, no-meats')
        parser.add_argument('--dataset',
            default=None,
            help='Select a category: all, meats, no-meats')

    def handle(self, *args, **options):
        meat = options.get('meat', "chiken")
        dataset = options.get('dataset', "foodimg")
        categories = options["categories"]
        piramid = PiramidFood(meat=meat, dataset=dataset, categories=categories)
        total_value = 0
        for category, value in piramid.process():
            print(category, value)
            total_value += value
        print("Total: ", total_value)
