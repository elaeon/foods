from nutrientes.utils import Food, conection, best_of_general_2
from django.core.exceptions import ImproperlyConfigured

try:
    from django.conf import settings
    PREPROCESSED_DATA_DIR = settings.PREPROCESSED_DATA_DIR
except ImproperlyConfigured:
    import os
    PREPROCESSED_DATA_DIR = os.path.dirname(os.path.dirname(__file__)) + '/preprocessed_data/'

def generate_matrix_food():
    matrix = Food.get_matrix(PREPROCESSED_DATA_DIR+'matrix.p')
    fields = Food.create_vector_fields_nutr()
    ndb_nos = Food.alimentos(limit="limit 9000")#ALL FOOD
    for ndb_no in ndb_nos:
        records = Food.get_raw_nutrients(ndb_no)
        vector = Food.vector_features(fields, records)
        matrix.append((ndb_no, vector.values()))
    Food.save_matrix(settings.PREPROCESSED_DATA_DIR+'matrix.p', matrix)


def ranking_global():
    global_ = Food.get_matrix(PREPROCESSED_DATA_DIR+"ranking.p")
    if len(global_) == 0:
        ranking_list = best_of_general_2()
        global_ = {ndb_no: (i, v) for i, (v, ndb_no, _, _, _) in enumerate(ranking_list, 1)}
        Food.save_matrix(PREPROCESSED_DATA_DIR+"ranking.p", global_)
    return global_


def ranking_category(group):
    category = Food.get_matrix("%s%s.p" % (PREPROCESSED_DATA_DIR, group["id"],))
    if len(category) == 0:
        ranking_cat_list = best_of_general_2(group["id"])
        category = {ndb_no: (i, v) for i, (v, ndb_no, _, _, _) in enumerate(ranking_cat_list, 1)}
        Food.save_matrix("%s%s.p" % (PREPROCESSED_DATA_DIR, group["id"],), category)
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


def insert_update_db_ranking():
    conn, cursor = conection()
    ndb_nos = Food.alimentos(limit="limit 9000")
    for ndb_no in ndb_nos:
        query = """SELECT Count(ndb_no) FROM ranking WHERE ndb_no='{ndb_no}'""".format(ndb_no=ndb_no)
        cursor.execute(query)
        result = cursor.fetchall()
        if result[0][0] == 0:
            print "CHECK", ndb_no
            food = Food(ndb_no, avg=False)
            rig, rvg = ranking_global()[ndb_no]
            ric, rvc = ranking_category(food.group)[ndb_no]
            query = """INSERT INTO ranking VALUES ('{ndb_no}', {global_value}, {category_value}, {category_position}, {global_position});""".format(
                ndb_no=ndb_no, 
                global_value=rvg, 
                category_value=rvc,
                category_position=ric,
                global_position=rig)
            cursor.execute(query)
        conn.commit()


