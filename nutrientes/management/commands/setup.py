from django.core.management.base import BaseCommand

from nutrientes.preprocessed_data import *

class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Buiding Omegas")
        calc_radio_omega_all()
        print("Calculating AVG")
        calc_avg(force=True)
        print("Generate Matrix")
        matrix_food()
        print("Generate Ranks")
        ranking_global_perfil()
        print("Calculating energy density")
        calc_energy_density()
