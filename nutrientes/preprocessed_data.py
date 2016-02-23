# -*- coding: utf-8 -*-

import sys
import os
PREPROCESSED_DATA_DIR = os.path.dirname(os.path.dirname(__file__)) + '/preprocessed_data/'

import django
sys.path.append(os.path.dirname(os.path.dirname(__file__))) #Set it to the root of your project
os.environ["DJANGO_SETTINGS_MODULE"] = "alimentos.settings"
django.setup()

from nutrientes.utils import Food, conection, best_of_general_2


def matrix_food():
    from nutrientes.utils import create_matrix
    matrix = create_matrix(Food.alimentos(limit="limit 9000"))#ALL FOOD
    matrix.save_matrix(PREPROCESSED_DATA_DIR+'matrix.csv')
    return matrix

def ranking_global_perfil():    
    from nutrientes.utils import Food, Recipe, perfiles, get_range
    import csv

    features = Recipe.create_generic_features()
    rnv_type = 1
    perfiles = perfiles(rnv_type=rnv_type)
    perfiles_dict = {}
    for genero, edad, unidad_edad in perfiles:
        edad_range = edad.split("-")
        if edad_range[1] != '':
            edad = int(edad_range[1])
        else:
            edad = int(edad_range[0])
        unidad_edad = unidad_edad if unidad_edad == "meses" else u"años"
        key = u"{}{}{}".format(edad, genero, unidad_edad)
        if key not in perfiles_dict:
            perfiles_dict[key] = {"edad": edad, "genero": genero, "unidad_edad": unidad_edad, "rnv_type": rnv_type}

    with open(PREPROCESSED_DATA_DIR+'matrix.csv', 'rb') as csvfile:
        rows = list(csv.reader(csvfile, delimiter=',', quotechar='"'))
        for perfil in perfiles_dict.values():
            edad_range = get_range(perfil["edad"], perfil["unidad_edad"])
            print(perfil, edad_range)
            foods = []
            for row in rows[1:]:
                food = Food(row[0])
                score = food.score(perfil, features=features)
                foods.append((
                    food.ndb_no, 
                    score, 
                    edad_range, 
                    perfil["genero"], 
                    perfil["unidad_edad"].encode("utf8", "replace"), 
                    perfil["rnv_type"]))
            ranking_by_perfil(foods)
            #break

def calc_radio_omega_all():
    conn, cursor = conection()
    ndb_nos = Food.alimentos(limit="limit 9000")
    for ndb_no in ndb_nos:
        food = Food(ndb_no, avg=False)
        query = """ SELECT COUNT(*) 
                    FROM omega 
                    WHERE ndb_no='{ndb_no}'""".format(
                ndb_no=ndb_no)
        cursor.execute(query)
        if cursor.fetchall()[0][0] == 1:
             query = """UPDATE omega 
                        SET omega3={omega3}, omega6={omega6}, omega7={omega7}, omega9={omega9}, radio={radio}
                        WHERE ndb_no='{ndb_no}'""".format(
                ndb_no=ndb_no,
                omega3=food.omegas.get("omega 3", [0,0])[1],
                omega6=food.omegas.get("omega 6", [0,0])[1],
                omega7=food.omegas.get("omega 7", [0,0])[1],
                omega9=food.omegas.get("omega 9", [0,0])[1],
                radio=food.radio_omega_raw)
        else:
            query = """INSERT INTO omega VALUES ('{ndb_no}', {omega3}, {omega6}, {omega7}, {omega9}, {radio});""".format(
                ndb_no=ndb_no, 
                omega3=food.omegas.get("omega 3", [0,0])[1],
                omega6=food.omegas.get("omega 6", [0,0])[1],
                omega7=food.omegas.get("omega 7", [0,0])[1],
                omega9=food.omegas.get("omega 9", [0,0])[1],
                radio=food.radio_omega_raw)
        cursor.execute(query)
    conn.commit()


def ranking_by_perfil(data):
    conn, cursor = conection()
    for ndb_no, score, edad_range, genero, unidad_edad, rnv_type in data:
        if len(edad_range) > 1:
            er = edad_range[0]
        else:
            er = edad_range[0]

        query = """SELECT COUNT(*) 
                    FROM ranking_perfil 
                    WHERE ndb_no='{ndb_no}'
                    AND edad_range='{edad_range}'
                    AND genero='{genero}'
                    AND unidad_edad='{unidad_edad}'
                    AND rnv_type={rnv_type}""".format(
                ndb_no=ndb_no, 
                edad_range=er, 
                genero=genero, 
                unidad_edad=unidad_edad, 
                rnv_type=rnv_type)

        cursor.execute(query)
        if cursor.fetchall()[0][0] == 1:
            query = """UPDATE ranking_perfil 
                        SET score={score}
                        WHERE ndb_no='{ndb_no}'
                        AND edad_range='{edad_range}'
                    AND genero='{genero}'
                    AND unidad_edad='{unidad_edad}'
                    AND rnv_type={rnv_type}""".format(
                ndb_no=ndb_no,
                score=score,
                edad_range=er, 
                genero=genero, 
                unidad_edad=unidad_edad, 
                rnv_type=rnv_type)
        else:
            query = """INSERT INTO ranking_perfil (ndb_no, score, edad_range, unidad_edad, genero, rnv_type) VALUES ('{ndb_no}', {score}, '{edad_range}', '{unidad_edad}', '{genero}', '{rnv_type}')""".format(
            ndb_no=ndb_no, 
            score=score,
            edad_range=er, 
            genero=genero, 
            unidad_edad=unidad_edad, 
            rnv_type=rnv_type)
        cursor.execute(query)
        conn.commit()
    conn.close()

def calc_avg(force=False):
    from nutrientes.utils import avg_omega, avg_nutrients, OMEGAS
    nutavg_vector = Food.get_matrix(PREPROCESSED_DATA_DIR + "nutavg.p")
    if len(nutavg_vector) == 0 or force:
        #appended the units with blank ''
        omegas = avg_omega()
        allnutavg_vector = [e[1:] + [""] for e in sorted(avg_nutrients().values())] +\
                        zip(omegas._fields[:-1], sorted(OMEGAS.keys()), omegas[:-1], ['g'] * len(omegas[:-1]))
        nutavg_vector, _ = Food.subs_omegas(allnutavg_vector)
        Food.save_matrix(PREPROCESSED_DATA_DIR + "nutavg.p", nutavg_vector)

def calc_energy_density():
    from nutrientes.models import EnergyDensity
    for ndb_no in Food.alimentos(limit="limit 9000"):
        food = Food(ndb_no=ndb_no)
        food.calc_energy_density()
        energy_density = food.energy_density
        if energy_density is not None:
            EnergyDensity.objects.get_or_create(
                ndb_no_t=ndb_no, 
                defaults={"energy_density": energy_density})

