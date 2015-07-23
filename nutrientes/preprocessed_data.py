from nutrientes.utils import Food, conection, best_of_general_2
from django.core.exceptions import ImproperlyConfigured

import os
PREPROCESSED_DATA_DIR = os.path.dirname(os.path.dirname(__file__)) + '/preprocessed_data/'


def matrix_food():
    from nutrientes.utils import create_matrix
    matrix = create_matrix(Food.alimentos(limit="limit 9000"))#ALL FOOD
    matrix.save_matrix(PREPROCESSED_DATA_DIR+'matrix.csv')
    return matrix

def order_matrix():
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
    ranking_list = rank.results
    calc_ranking_detail(rank, "global")
    global_ = {ndb_no: i for i, (_, ndb_no, _) in Rank.rank2natural(ranking_list, f_index=lambda x: x[0])}
    return global_


def ranking_category(group):
    from nutrientes.utils import Rank
    rank = best_of_general_2(group)
    ranking_cat_list = rank.results
    calc_ranking_detail(rank, "category")
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
    for ndb_no, position in data.items():
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


def ranking_detail_by_type(ndb_no, data, type_position):
    conn, cursor = conection()
    for nutr_no, position in data.items():
        query = """ SELECT COUNT(*) 
                    FROM ranking_food_detail
                    WHERE ndb_no='{ndb_no}'
                    AND type_position='{type_position}'
                    AND nutr_no='{nutr_no}'""".format(
                ndb_no=ndb_no, 
                type_position=type_position,
                nutr_no=nutr_no)
        cursor.execute(query)
        if cursor.fetchall()[0][0] == 1:
            query = """UPDATE ranking_food_detail 
                        SET position={position}
                        WHERE ndb_no='{ndb_no}'
                        AND type_position='{type_position}'
                        AND nutr_no='{nutr_no}'""".format(
                ndb_no=ndb_no,
                position=position,
                nutr_no=nutr_no,
                type_position=type_position)
        else:
            query = """INSERT INTO ranking_food_detail 
                        VALUES ('{ndb_no}', '{nutr_no}', {position}, '{type_position}')""".format(
            ndb_no=ndb_no, 
            position=position, 
            type_position=type_position,
            nutr_no=nutr_no)
        cursor.execute(query)
        conn.commit()

def calc_ranking_detail(rank, type_category):
    for ndb_no in rank.ranks:
        data = rank.get_values_food(ndb_no)
        ranking_detail_by_type(ndb_no, data, type_category)

def recalc_preprocessed_data():
    print "Generate AVG"
    calc_avg(force=True)
    print "Generate Matrix"
    matrix_food()
    print "Generate Order Matrix"
    order_matrix()
    print "Generate Ranks"
    insert_update_db_ranking()

