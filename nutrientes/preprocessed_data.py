# -*- coding: utf-8 -*-
from nutrientes.utils import Food, conection, best_of_general_2
from django.core.exceptions import ImproperlyConfigured

import os
PREPROCESSED_DATA_DIR = os.path.dirname(os.path.dirname(__file__)) + '/preprocessed_data/'


def matrix_food():
    from nutrientes.utils import create_matrix
    matrix = create_matrix(Food.alimentos(limit="limit 9000"))#ALL FOOD
    matrix.save_matrix(PREPROCESSED_DATA_DIR+'matrix.csv')
    return matrix

def ordered_matrix():
    from nutrientes.utils import create_order_matrix
    foods = create_order_matrix()
    import csv
    foods_l = [Food(ndb_no, avg=False) for ndb_no in foods]
    with open("order_matrix.csv", 'wb') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=',',
                        quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for food in foods_l:
            csvwriter.writerow([food.ndb_no, food.group["id"]])

def ranking_global():
    from nutrientes.utils import Rank
    rank = best_of_general_2()
    print("Ranking calculated")
    ranking_list = rank.results
    #calc_ranking_detail(rank)
    global_ = {ndb_no: i for i, (_, ndb_no, _) in Rank.rank2natural(ranking_list, f_index=lambda x: x[0])}
    return global_

def ranking_global_perfil():    
    from nutrientes.utils import Food, Recipe, perfiles
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
        
    edad_range_meses = ["0-6", "7-12"]
    edad_range_years = ["1-3", "4-8", "9-13", "14-18", "19-30", "31-50", "51-70", "71-150"]
    def get_range(edad, edad_range_list):
        for edad_range in edad_range_list:
            min_year, max_year = edad_range.split("-")
            min_year = int(min_year)
            if max_year == '':            
                max_year = 200
            else:
                max_year = int(max_year)
            if min_year <= perfil["edad"] <= max_year:
                return edad_range

    with open(PREPROCESSED_DATA_DIR+'order_matrix.csv', 'rb') as csvfile:
        rows = list(csv.reader(csvfile, delimiter=',', quotechar='"'))
        for perfil in perfiles_dict.values():
            print(perfil)
            foods = []
            if perfil["unidad_edad"] == u"meses":
                edad_range = get_range(perfil["edad"], edad_range_meses)
            else:
                edad_range = get_range(perfil["edad"], edad_range_years)
            for row in rows:
                food = Food(row[0])
                score = food.score(perfil, features=features)
                foods.append((food.ndb_no, score, edad_range, perfil["genero"], perfil["unidad_edad"].encode("utf8", "replace"), perfil["rnv_type"]))
            ranking_by_perfil(foods)
            #break

def ranking_category(group):
    from nutrientes.utils import Rank
    rank = best_of_general_2(group)
    ranking_cat_list = rank.results
    category = {ndb_no: i for i, (_, ndb_no, _) in Rank.rank2natural(ranking_cat_list, f_index=lambda x: x[0])}
    return category


def calc_radio_omega_all():
    conn, cursor = conection()
    ndb_nos = Food.alimentos(limit="limit 9000")
    for ndb_no in ndb_nos:
        food = Food(ndb_no, avg=False)
        query = """INSERT INTO omega VALUES ('{ndb_no}', {omega3}, {omega6}, {omega7}, {omega9}, {radio});""".format(
            ndb_no=ndb_no, 
            omega3=food.omegas.get("omega 3", [0,0])[1],
            omega6=food.omegas.get("omega 6", [0,0])[1],
            omega7=food.omegas.get("omega 7", [0,0])[1],
            omega9=food.omegas.get("omega 9", [0,0])[1],
            radio=food.radio_omega_raw)
        cursor.execute(query)
    conn.commit()


def ranking_by_type(data, type_position):
    conn, cursor = conection()
    i = 0
    for ndb_no, position in data.items():
        print(i)
        i += 1
        query = """ SELECT COUNT(*) 
                    FROM ranking 
                    WHERE ndb_no='{ndb_no}'
                    AND type_position='{type_position}'""".format(
                ndb_no=ndb_no, 
                type_position=type_position)
        cursor.execute(query)
        if cursor.fetchall()[0][0] == 1:
            query = """UPDATE ranking 
                        SET position={position}
                        WHERE ndb_no='{ndb_no}'
                        AND type_position='{type_position}'""".format(
                ndb_no=ndb_no,
                position=position,
                type_position=type_position)
        else:
            query = """INSERT INTO ranking VALUES ('{ndb_no}', {position}, '{type_position}')""".format(
            ndb_no=ndb_no, 
            position=position, 
            type_position=type_position)
        cursor.execute(query)
        conn.commit()


def ranking_by_perfil(data):
    conn, cursor = conection()
    for ndb_no, score, edad_range, genero, unidad_edad, rnv_type in data:
        query = """SELECT COUNT(*) 
                    FROM ranking_perfil 
                    WHERE ndb_no='{ndb_no}'
                    AND edad_range='{edad_range}'
                    AND genero='{genero}'
                    AND unidad_edad='{unidad_edad}'
                    AND rnv_type={rnv_type}""".format(
                ndb_no=ndb_no, 
                edad_range=edad_range, 
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
                edad_range=edad_range, 
                genero=genero, 
                unidad_edad=unidad_edad, 
                rnv_type=rnv_type)
        else:
            query = """INSERT INTO ranking_perfil (ndb_no, score, edad_range, unidad_edad, genero, rnv_type) VALUES ('{ndb_no}', {score}, '{edad_range}', '{unidad_edad}', '{genero}', '{rnv_type}')""".format(
            ndb_no=ndb_no, 
            score=score,
            edad_range=edad_range, 
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

def insert_update_db_ranking():
    from nutrientes.utils import categories_foods
    data = ranking_global()
    ranking_by_type(data, "global")

    for group, _ in categories_foods():
        data = ranking_category(group)
        ranking_by_type(data, "category")

    data = ranking_global_perfil()


def recalc_preprocessed_data():
    print "Generate AVG"
    calc_avg(force=True)
    print "Generate Matrix"
    matrix_food()
    print "Generate Ranks"
    insert_update_db_ranking()
    print "Generate Ordered Matrix"
    ordered_matrix()
