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
        parser.add_argument('--radio-omega',
            action='store_true',
            help='Weights with radio omega')
        parser.add_argument('--piramid',
            action='store_true',
            help='Build a food piramid')

    def handle(self, *args, **options):
        meat = options.get('meat', "chicken")
        dataset = options.get('dataset', "foodimg")
        categories = options["categories"]
        number_category = options["number_category"]
        radio_omega = options["radio_omega"]
        piramid_print = options["piramid"]
        if number_category is not None:
            dataset = list(self.datasets(number_category, dataset))
            piramid = PiramidFood(meat=meat, dataset=dataset, categories=categories, 
                    weight_nutrs=weight_nutrs, radio_omega=radio_omega)
            total_value = 0
            for category, value, _ in piramid.process(reverse=False):
                print(category, Food(category, avg=False).name, value)
                total_value += value
            print("Total: ", total_value)
        elif dataset == 'test':
            dataset = ["19903", "14545", "09079", "20051", "35193", "25000", "12006", "12220"]
            piramid = PiramidFood(meat=meat, dataset=dataset, categories=categories, 
                weight_nutrs={"omega3":.1, "omega9": .1}, 
                radio_omega=radio_omega)
            #{"omega3":.1, "omega9": .1, "322": 1, "263": 2, "418": 3})
            total_value = 0
            for category, value, _ in piramid.process(reverse=False):
                print(category, Food(category, avg=False).name, value)
                total_value += value
            print("Total: ", total_value)
        else:
            piramid = PiramidFood(meat=meat, dataset=dataset, categories=categories, 
                weight_nutrs=weight_nutrs, radio_omega=radio_omega, energy=True)
            if piramid_print:
                piramid.build_piramid()
            else:
                total_value = 0
                total_energy = 0
                total_weight = 800
                for category, value, energy in piramid.process(reverse=False):
                    weight = total_weight * (value / 100)
                    energy_weight = ((weight * energy) / 100)
                    print(piramid.categories_name.get(category, category), "{}%".format(value), "{}g".format(int(round(weight, 0))), "{}kcal".format(round(energy_weight, 2)))
                    total_value += value
                    total_energy += energy_weight
                print("Total: ", "{}%".format(total_value), "{}kcal".format(int(round(total_energy, 0))))

    def datasets(self, category, dataset):
        from nutrientes.utils import get_fooddescimg, alimentos_category
        if dataset == "foodimg":
            return (ndb_no[0] for ndb_no in get_fooddescimg(category=category))
        else:
            return (ndb_no for ndb_no, _ in alimentos_category(category, limit='limit 9000'))
