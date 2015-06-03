from nutrientes.utils import Food, conection, best_of_general_2
from django.core.exceptions import ImproperlyConfigured

try:
    from django.conf import settings
    PREPROCESSED_DATA_DIR = settings.PREPROCESSED_DATA_DIR
except ImproperlyConfigured:
    import os
    PREPROCESSED_DATA_DIR = os.path.dirname(os.path.dirname(__file__)) + '/preprocessed_data/'

def matrix_food(force=False):
    matrix = Food.get_matrix(PREPROCESSED_DATA_DIR+'matrix.p')
    if len(matrix) == 0 or force:
        fields = Food.create_vector_fields_nutr()
        ndb_nos = Food.alimentos(limit="limit 9000")#ALL FOOD
        for ndb_no in ndb_nos:
            records = Food.get_raw_nutrients(ndb_no)
            vector = Food.vector_features(fields, records)
            matrix.append((ndb_no, vector.values()))
        Food.save_matrix(PREPROCESSED_DATA_DIR+'matrix.p', matrix)
    return matrix


def ranking_global(force=False):
    global_ = Food.get_matrix(PREPROCESSED_DATA_DIR+"ranking.p")
    if len(global_) == 0 or force:
        ranking_list = best_of_general_2()
        global_ = {ndb_no: (i, g, b) for i, (_, ndb_no, _, g, b) in enumerate(ranking_list, 1)}
        Food.save_matrix(PREPROCESSED_DATA_DIR+"ranking.p", global_)
    return global_


def ranking_category(group, force=False):
    from nutrientes.utils import Rank
    category = Food.get_matrix("%s%s.p" % (PREPROCESSED_DATA_DIR, group,))
    if len(category) == 0 or force:
        ranking_cat_list = best_of_general_2(group)
        category = {ndb_no: i for i, (_, ndb_no, _) in Rank.rank2natural(ranking_cat_list, f_index=lambda x: x[0])}
        Food.save_matrix("%s%s.p" % (PREPROCESSED_DATA_DIR, group), category)
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
        print type_position, position
        #for type_position, position in zip(types, values):
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

def insert_update_db_ranking():
    from nutrientes.utils import categories_foods
    data = ranking_global(force=True)
    ranking_by_type(data, "global")

    #for group, _ in categories_foods():
    #    data = ranking_category(group, force=True)
    #    ranking_by_type(data, "category")


def recalc_preprocessed_data():
    #print "Generate Matrix"
    #matrix_food(force=True)
    print "Generate Ranks"
    insert_update_db_ranking()

