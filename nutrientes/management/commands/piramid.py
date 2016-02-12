from django.core.management.base import BaseCommand

from nutrientes.utils import PiramidFood, Food
from nutrientes.weights import WEIGHT_NUTRS as weight_nutrs

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
            help='Select a dataset: all or foodimg')
        parser.add_argument('--number-category',
            default=None,
            help='Select a number food category: 1500, ...')

    def handle(self, *args, **options):
        meat = options.get('meat', "chicken")
        dataset = options.get('dataset', "foodimg")
        categories = options["categories"]
        number_category = options["number_category"]
        if number_category is not None:
            dataset = list(self.datasets(number_category, dataset))
            piramid = PiramidFood(meat=meat, dataset=dataset, categories=categories, weight_nutrs=weight_nutrs)
            total_value = 0
            for category, value in piramid.process():
                print(category, Food(category, avg=False).name, value)
                total_value += value
            print("Total: ", total_value)
        elif dataset == 'test':
            dataset = ["19903", "14545", "09079", "20051", "35193", "25000", "12006"]
            piramid = PiramidFood(meat=meat, dataset=dataset, categories=categories, 
                weight_nutrs={"omega9":3}, radio_omega=False)#{"omega3":3, "omega9": .1, "322": 1, "263": 2, "418": 3})
            total_value = 0
            for category, value in piramid.process():
                print(category, Food(category, avg=False).name, value)
                total_value += value
            print("Total: ", total_value)
        else:
            piramid = PiramidFood(meat=meat, dataset=dataset, categories=categories, 
                weight_nutrs=weight_nutrs)
            total_value = 0
            for category, value in piramid.process():
                print(category, value)
                total_value += value
            print("Total: ", total_value)

    def datasets(self, category, dataset):
        from nutrientes.utils import get_fooddescimg, alimentos_category
        if dataset == "foodimg":
            return (ndb_no[0] for ndb_no in get_fooddescimg(category=category))
        else:
            return (ndb_no for ndb_no, _ in alimentos_category(category, limit='limit 9000'))