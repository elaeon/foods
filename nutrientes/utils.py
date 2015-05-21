import psycopg2
import re
import pickle

from itertools import izip

USERNAME = 'agmartinez'


def conection():
    conn_string = "host='' dbname='alimentos' user='{username}'".format(username=USERNAME)
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()
    return conn, cursor

def group_data(data, exclude=set([])):
    from collections import defaultdict
    group = defaultdict(list)
    for food_desc, nutr_no, nut, v, u in data:
        if not nutr_no in exclude:
            group[food_desc].append((nutr_no, nut, float(v), u))
    return group

def nutr_features(order_by="sr_order"):
    _, cursor = conection()
    query  = """SELECT nutr_no, nutrdesc FROM nutr_def ORDER BY {order_by}""".format(order_by=order_by)
    cursor.execute(query)
    return cursor.fetchall()

def nutr_features_group(order_by="sr_order"):
    _, cursor = conection()
    query  = """SELECT nutr_no, nutrdesc, nutr_def.group FROM nutr_def ORDER BY {order_by}""".format(order_by=order_by)
    cursor.execute(query)
    return cursor.fetchall()

def nutr_features_ids(ids):
    _, cursor = conection()
    query  = """SELECT nutr_no, nutrdesc FROM nutr_def WHERE nutr_no IN {ids}""".format(ids=ids)
    cursor.execute(query)
    return cursor.fetchall()

def categories_foods():
    _, cursor = conection()
    query  = """SELECT fdgrp_cd, fdgrp_desc_es FROM fd_group ORDER BY fdgrp_desc_es"""
    cursor.execute(query)
    return cursor.fetchall()

def avg_nutrients():
    _, cursor = conection()
    query = """SELECT nutr_no, AVG(nutr_val) FROM nut_data GROUP BY nutr_no"""
    cursor.execute(query)
    nutr = {e[0]:[i, e[0], e[1]] for i, e in enumerate(nutr_features())}
    for nutr_no, avg in cursor.fetchall():
        nutr[nutr_no].append(float(avg))
    return nutr

def normalize(raw_data, index, base):
    return [list(value[0:index]) + [value[index] / base] + list(value[index+1:len(value)]) for value in raw_data]

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

def avg_nutrients_group_nutr(nutr_no, order_by="avg"):
    _, cursor = conection()
    query = """SELECT fd_group.fdgrp_desc_es, AVG(nutr_val) as avg
            FROM nut_data, food_des, fd_group
            WHERE fd_group.fdgrp_cd=food_des.fdgrp_cd
            AND nut_data.ndb_no=food_des.ndb_no
            AND nut_data.nutr_no='{nutr_no}' GROUP BY fd_group.fdgrp_desc_es ORDER BY {order};""".format(nutr_no=nutr_no, order=order_by)
    cursor.execute(query)
    return cursor.fetchall()

def avg_nutrients_group():
    _, cursor = conection()
    query = """SELECT nut_data.nutr_no, fd_group.fdgrp_desc_es, AVG(nutr_val)
            FROM nut_data, food_des, fd_group, nutr_def
            WHERE fd_group.fdgrp_cd=food_des.fdgrp_cd
            AND nut_data.ndb_no=food_des.ndb_no
            AND nutr_def.nutr_no=nut_data.nutr_no GROUP BY fd_group.fdgrp_desc_es, nut_data.nutr_no;"""
    cursor.execute(query)
    return cursor.fetchall()
    #nutr = {e[0]:[i, e[0], e[1]] for i, e in enumerate(nutr_features())}
    #for nutr_no, fdgrp_desc, avg in cursor.fetchall():
    #    nutr[nutr_no].append(float(avg))
    #return nutr

def get_omegas():
    _, cursor = conection()
    query = """SELECT food_des.long_desc_es, food_des.ndb_no, omega3, omega6, radio 
                FROM omega, food_des
                WHERE food_des.ndb_no=omega.ndb_no
                AND omega3 > 0
                ORDER BY radio, long_desc_es;"""
    cursor.execute(query)
    return cursor.fetchall()

def mark_caution_nutr(features):
    return [(nutr_no, nut, v, u, int(nutr_no in caution_nutr)) for nutr_no, nut, v, u in features]

def category_food():
    _, cursor = conection()
    query = """
        SELECT fd_group.fdgrp_desc_es, fd_group.fdgrp_cd, COUNT(fd_group.fdgrp_desc_es)
        FROM food_des, fd_group
        WHERE fd_group.fdgrp_cd=food_des.fdgrp_cd GROUP BY fd_group.fdgrp_desc_es, fd_group.fdgrp_cd ORDER BY fd_group.fdgrp_desc_es;
    """
    cursor.execute(query)
    return cursor.fetchall()

def category_avg_omegas():
    _, cursor = conection()
    query = """
        SELECT fd_group.fdgrp_desc_es, AVG(omega.radio)
        FROM food_des, fd_group, omega
        WHERE fd_group.fdgrp_cd=food_des.fdgrp_cd
        AND omega.omega3 > 0
        AND omega.ndb_no=food_des.ndb_no GROUP BY fd_group.fdgrp_desc_es;
    """
    cursor.execute(query)
    return {food_group:round(avg,1) for food_group, avg in cursor.fetchall()}

def category_food_list():
    from collections import defaultdict
    nutr = avg_nutrients()
    category_results = defaultdict(list)
    category_food_l = category_food()
    for cat, _, count in category_food_l:
        category_results[cat] = [None, None, None, None, None, None, None]
    for i, nutr_no in enumerate(["601", "204", "269", "262", "307", "208", "209"]):
        cat_nutr = avg_nutrients_group_nutr(nutr_no, order_by="fd_group.fdgrp_desc_es")
        for cat_avg in cat_nutr:
            category_results[cat_avg[0]][i] = round(float(cat_avg[1]) - nutr[nutr_no][3] , 1)

    omegas = category_avg_omegas()
    for category_food_e, cat_id, count in category_food_l:
        nutr_calif = len(filter(lambda x:x < 0, category_results[category_food_e]))
        omega_calif = 0 if omegas[category_food_e] > 4 else 1
        calif = int(((nutr_calif + omega_calif) / (float(len(category_results[category_food_e]) + 1)))*100)
        yield category_food_e, cat_id, count, category_results[category_food_e], omegas[category_food_e], calif

def alimentos_category(category=None, limit="limit 10"):
    _, cursor = conection()
    query  = """SELECT food_des.ndb_no, food_des.long_desc_es
                FROM food_des, fd_group
                WHERE fd_group.fdgrp_cd=food_des.fdgrp_cd
                AND fd_group.fdgrp_cd='{category}' ORDER BY food_des.long_desc_es {limit}""".format(category=category, limit=limit)

    cursor.execute(query)
    return cursor.fetchall()

def alimentos_category_name(category):
    _, cursor = conection()
    query  = """SELECT fdgrp_desc_es
                FROM fd_group
                WHERE fd_group.fdgrp_cd='{category}'""".format(category=category)

    cursor.execute(query)
    return cursor.fetchall()


def best_of_query(nutr_no_list, category_food):
    _, cursor = conection()
    nutr = Food.get_matrix("nutavg.p")
    nutr_avg = {nutr_no:(avg, caution) for nutr_no, nutr_desc, avg, _, caution in mark_caution_nutr(nutr) if nutr_no in nutr_no_list}
    querys = []
    def query_build(nutr_no, avg, caution, category_food):
        if caution:
            query = """
                SELECT food_des.ndb_no, food_des.long_desc_es, nutr_val
                FROM nut_data, food_des, nutr_def 
                WHERE nut_data.ndb_no=food_des.ndb_no 
                AND nutr_def.nutr_no=nut_data.nutr_no 
                AND nutr_val < {avg}
                AND nut_data.nutr_no='{nutr_no}'
            """
        else:
            query = """
                SELECT food_des.ndb_no, food_des.long_desc_es, nutr_val
                FROM nut_data, food_des, nutr_def 
                WHERE nut_data.ndb_no=food_des.ndb_no 
                AND nutr_def.nutr_no=nut_data.nutr_no 
                AND nutr_val >= {avg}
                AND nut_data.nutr_no='{nutr_no}'
            """

        if category_food:
            query += """ AND food_des.fdgrp_cd='{category_food}'"""
            query = query.format(avg=avg, nutr_no=nutr_no, category_food=category_food)
        else:
            query = query.format(avg=avg, nutr_no=nutr_no)
        return (nutr_no, caution, query)

    for nutr_no, (avg, caution) in nutr_avg.items():
        nutr_no, caution, query = query_build(nutr_no, avg, caution, category_food)
        cursor.execute(query)
        querys.append((nutr_no, caution, cursor.fetchall()))

    def get_ids_intersection(cat):
        set_base = set(cat.values()[0]["data"].keys())
        for v in cat.values()[1:]:
            set_base = set_base.intersection(set(v["data"].keys()))
        return set_base

    rank = Rank()
    cat = rank.get_categories_nutr(querys)
    return rank.order(cat, get_ids_intersection(cat))

class Rank(object):
    def get_categories_nutr(self, querys):
        category_nutr = {}
        for nutr_no, caution, result_query in querys:
            category_nutr[nutr_no] = {"caution": caution, "data": {}}
            for ndb_no, long_desc_es, nutr_val in result_query:
                category_nutr[nutr_no]["data"][ndb_no] = (nutr_val, long_desc_es)
        return category_nutr

    def ids2data_sorted(self, category_nutr, set_base, names={}):
        data = {}
        for nutr_no in category_nutr.keys():
            data.setdefault(nutr_no, [])
            reverse = not bool(category_nutr[nutr_no]["caution"])
            for ndb_no in set_base:
                nutr_val, long_desc_es = category_nutr[nutr_no]["data"].get(ndb_no, ([0, names.get(ndb_no, None)]))
                data[nutr_no].append((ndb_no, long_desc_es, float(nutr_val)))
            data[nutr_no].sort(reverse=reverse, key=lambda x: x[2])
        return data

    def enumerateX(self, data):
        indice = 0
        data_tmp = data + [(None, None, 0)]
        for x, y in zip(data_tmp, data_tmp[1:]):
            if abs(x[2] - y[2]) > 0:
                yield indice, x
                indice += 1
            else:
                yield indice, x
    
    def sorted_data(self, category_nutr):
        positions = {}
        for nutr_no in category_nutr.keys():
            for i, v in self.enumerateX(category_nutr[nutr_no]):
                positions.setdefault(v[0], {"attr": v[:2], "i": 0, "val": []})
                positions[v[0]]["i"] += i
                positions[v[0]]["val"].append(v[2])
        return sorted(positions.values(), key=lambda x: x["i"])

    def rank2natural(self, data):
        base = None
        index = 0
        for d in data:
            if base != d["i"]:
                base = d["i"]
                index += 1
            yield index, d
    
    def order(self, category_nutr, base_food, names={}):
        return self.rank2natural(self.sorted_data(self.ids2data_sorted(category_nutr, base_food, names=names)))

def best_of_general(name, category):
    from collections import namedtuple
    _, cursor = conection()
    query = """SELECT food_des.ndb_no, food_des.long_desc_es
            FROM food_des, fd_group
            WHERE fd_group.fdgrp_cd=food_des.fdgrp_cd
            AND long_desc_es IS NOT NULL
            AND fd_group.fdgrp_cd='{category}'
            AND long_desc_es ilike '%{term}%'""".format(term=name, category=category)
    cursor.execute(query)
    foods = {ndb_no: Food(ndb_no) for ndb_no, long_desc_es in cursor.fetchall()}
    nutr = []
    for food in foods.values():
        Calif = namedtuple('Calif', 'ndb_no bad good omega')
        bad =  filter(lambda x: x[3], ((t[0], t[1], t[2], t[4]) for t in mark_caution_nutr(food.nutrients)))
        bad_avg = filter(lambda x: x[3], ((t[0], t[1], t[2], t[4]) for t in mark_caution_nutr(food.nutr_avg)))
        bad = sum([b[2] - bavg[2]  for b, bavg in izip(bad, bad_avg)])
        good =  filter(lambda x: not x[3], ((t[0], t[1], t[2], t[4]) for t in mark_caution_nutr(food.nutrients)))
        good_avg = filter(lambda x: not x[3], ((t[0], t[1], t[2], t[4]) for t in mark_caution_nutr(food.nutr_avg)))
        good = sum([g[2] - gavg[2] for g, gavg in izip(good, good_avg)])
        omega = abs(food.radio_omega_raw - 1)
        nutr.append(Calif(food.ndb_no, bad, good, omega))
    
    total = []
    for n in nutr:
        if n.good < 0 and n.bad < 0:
            calif = n.good + n.good
        else:
            calif = n.good - n.bad

        if n.omega < 1:
            calif = calif * n.omega
        elif n.omega > 1:
            calif = calif / n.omega
        else:
            calif = calif + n.omega

        total.append((calif, n.ndb_no))
    print [foods[ndb_no].name for _, ndb_no in sorted(total, reverse=True)[:100]]
    
def best_of_general_2(name, category):
    _, cursor = conection()
    nutr = Food.get_matrix("nutavg.p")
    # haseamos las llaves para mantener el orden
    nutr_avg = {nutr_no:(avg, caution) for nutr_no, nutr_desc, avg, _, caution in mark_caution_nutr(nutr)}
    querys = []
    def query_build(nutr_no, category_food):
        query = """
            SELECT food_des.ndb_no, food_des.long_desc_es, nutr_val
            FROM nut_data, food_des, nutr_def 
            WHERE nut_data.ndb_no=food_des.ndb_no 
            AND nutr_def.nutr_no=nut_data.nutr_no 
            AND nut_data.nutr_no='{nutr_no}'
        """

        if category_food:
            query += """ AND food_des.fdgrp_cd='{category_food}'"""
            query = query.format(nutr_no=nutr_no, category_food=category_food)
        else:
            query = query.format(nutr_no=nutr_no)
        return (nutr_no, caution, query)

    for nutr_no, (avg, caution) in nutr_avg.items():
        nutr_no, caution, query = query_build(nutr_no, category)
        cursor.execute(query)
        querys.append((nutr_no, caution, cursor.fetchall()))

    good = querys
    rank = Rank()
    category_nutr = rank.get_categories_nutr(good)
    foods = {e[0]: e[1] for _, _, food in good for e in food}
    rg = rank.order(category_nutr, set(foods.keys()), names=foods)
    #nd = {d["attr"][0]: (d["i"], d["attr"][0], d["attr"][1]) for _, d in rg}

    #category_nutr = rank.get_categories_nutr(bad)
    #foods = {e[0]: e[1] for _, _, food in bad for e in food}
    #rb = rank.order(category_nutr, set(foods.keys()), names=foods)
    #nb = {d["attr"][0]: (d["i"], d["attr"][0], d["attr"][1]) for _, d in rb}
    
    #t = [(nd[k][0] + nb[k][0], nd[k][1], nd[k][2]) for k in nd.keys()]
    #t = sorted(t)
    #for e in t:
    #    print e

    #for e in rg:
    #    print e[0], e[1]["attr"][1]

    
caution_nutr = {
    "601": "Cholesterol",
    "204": "Total lipid (fat)",
    "205": "Carbohydrate, by difference",
    "269": "Sugars, total",
    "262": "Caffeine",
    "605": "Fatty acids, total trans",
    "693": "Fatty acids, total trans-monoenoic",
    "695": "Fatty acids, total trans-polyenoic",
    "606": "Fatty acids, total saturated",
    "307": "Sodium, Na",
    "208": "Energy",
    "209": "Starch"
}

exclude_nutr = {
    "268": "Energy",
    "269": "Sugars, total",
    "605": "Fatty acids, total trans",
    "606": "Fatty acids, total saturated",
    "645": "Fatty acids, total monounsaturated",
    "646": "Fatty acids, total polyunsaturated",
    "208": "Energy",
    "695": "Fatty acids, total trans-polyenoic",
    "693": "Fatty acids, total trans-monoenoic",
    "204": "Total lipid (fat)",
    #"205": "Carbohydrate, by difference",
    "203": "Protein",
    #"318": "Vitamin A, IU", 
    #"320": "Vitamin A, RAE"
}

OMEGAS = {
    "omega 3": ["16:3", "18:3", "18:4", "20:3", "20:4", "20:5", "21:5", "22:5", "22:6", "24:5", "24:6"],
    "omega 6": ["18:2", "18:3", "20:2", "20:3", "20:4", "22:2", "22:4", "22:5", "24:4", "24:5"],
    "omega 7": ["12:1", "14:1", "16:1", "18:1", "20:1", "22:1", "24:1"],
    "omega 9": ["18:1", "20:1", "20:3", "22:1", "24:1"]
}

class Food(object):
    def __init__(self, ndb_no=None, avg=True):
        self.nutrients = None
        self.name = None
        self.radio_omega_raw = 0
        self.nutr_avg = None
        self.ndb_no = ndb_no
        self.omegas = None
        if self.ndb_no is not None:
            self.get(ndb_no, avg=avg)

    def name_limit(self):
        if len(self.name) > 20:
            return "%s..." % (self.name[:20],)
        return self.name

    def radio_raw(self, omega6, omega3):
        try:
            return round(omega6/omega3, 2)
        except ZeroDivisionError:
            return 0

    def radio(self):
        if self.radio_omega_raw == 0 and self.omegas.get("omega3", [0,0])[1] == 0:
            return "%s:0" % (round(self.omegas.get("omega6", [0,0])[1], 2),)
        else:
            return "%s:1" % (self.radio_omega_raw,)

    @classmethod
    def get_raw_nutrients(self, ndb_no):
        _, cursor = conection()
        query  = """SELECT food_des.long_desc_es, nutr_def.nutr_no, nutrdesc, nutr_val, units
                    FROM food_des, nut_data, nutr_def
                    WHERE nut_data.ndb_no=food_des.ndb_no 
                    AND nutr_def.nutr_no=nut_data.nutr_no
                    AND nutr_val > 0
                    AND food_des.ndb_no='{ndb_no}' ORDER BY sr_order""".format(ndb_no=ndb_no)
        cursor.execute(query)
        return cursor.fetchall()

    @classmethod
    def get_food(self, ndb_no):
        _, cursor = conection()
        query  = """SELECT food_des.long_desc_es, fd_group.fdgrp_desc_es
                    FROM food_des, fd_group
                    WHERE fd_group.fdgrp_cd=food_des.fdgrp_cd 
                    AND food_des.ndb_no = '{ndb_no}'""".format(ndb_no=ndb_no)
        cursor.execute(query)
        return cursor.fetchall()

    def get(self, ndb_no=None, avg=True):
        if self.ndb_no is None and ndb_no is not None:
            self.ndb_no = ndb_no
        records = self.get_raw_nutrients(self.ndb_no)
        g_data = group_data(records, exclude=set(["268"])) #Energy#ENERC_KJ
        self.name = g_data.keys().pop()
        features, omegas = self.subs_omegas(g_data.values()[0])
        self.nutrients = features + [(v[0], k, v[1], v[2]) for k, v in omegas.items()]
        self.radio_omega_raw = self.radio_raw(omegas.get("omega 6", [0,0,0])[1], omegas.get("omega 3", [0,0,0])[1])
        self.omegas = omegas
        if avg:
            nutavg_vector = self.get_matrix("nutavg.p")
            if len(nutavg_vector) == 0:
                nutavg_vector = [e[1:] + [""] for e in sorted(avg_nutrients().values())]
                self.save_matrix("nutavg.p", nutavg_vector)

            all_nutr, omegas = self.subs_omegas(nutavg_vector)
            omegas = filter(lambda x: x[1] is not None, ((key, omegas.get(key, None)) for key in self.omegas.keys()))
            self.nutr_avg = self.exclude_features(all_nutr) + [(v[0], k, v[1], v[2]) for k, v in omegas]

    @classmethod
    def subs_omegas(self, features):
        """ sustituye los terminos X:X por el nombre omega Y"""
        pattern = r"(?P<molecula>\d{2}:\d{1})"
        pattern_base = r"(?P<tipo>n\-\d{1})"
        s_molecula = re.compile(pattern)
        s_tipo_molecula = re.compile(pattern_base)
        n_features = []
        omegas = {}
        for nutr_no, nut, v, u in features:
            molecula = s_molecula.search(nut)
            if molecula:
                molecula_txt = molecula.groupdict()["molecula"]
                tipo_molecula = s_tipo_molecula.search(nut)
                if tipo_molecula:
                    tipo_molecula_txt = tipo_molecula.groupdict()["tipo"]
                else:
                    tipo_molecula_txt = None

                if tipo_molecula_txt == "n-3":
                    omega = "omega 3"
                elif tipo_molecula_txt == "n-6":
                    omega = "omega 6"
                elif tipo_molecula_txt == "n-7":
                    omega = "omega 7"
                elif tipo_molecula_txt == "n-9":
                    omega = "omega 9"
                elif molecula_txt in OMEGAS["omega 3"]:
                    omega = "omega 3"
                elif molecula_txt in OMEGAS["omega 6"]:
                    omega = "omega 6"
                elif molecula_txt in OMEGAS["omega 7"]:
                    omega = "omega 7"
                elif molecula_txt in OMEGAS["omega 9"]:
                    omega = "omega 9"
                else:
                    omega = None
            
                if omega is not None:
                    omegas.setdefault(omega, [omega, 0, u])
                    omegas[omega][1] += v
            else:
                n_features.append((nutr_no, nut, v, u))

        return n_features, omegas

    def exclude_features(self, all_nutr):
        """nutr_no, nut, float(v), u in self.nutrients"""
        base = set([n[0] for n in self.nutrients])
        return [n for n in all_nutr if n[0] in base]

    @classmethod
    def init_features(self, records):
        features = {}
        for record in records:
            features[record] = 0

        return features

    @classmethod
    def vector_features(self, fields, records):
        features = self.init_features(fields)
        for nutr_no, nutrdesc, nutr_val, units in records:
            if nutr_no in features:
                features[nutr_no] = float(nutr_val)
        return features

    def cosine_similarity(self, v1, v2):
        "compute cosine similarity of v1 to v2: (v1 dot v1)/{||v1||*||v2||)"
        sumxy = sum((x*y for x, y in izip(v1, v2)))
        sumxx = sum((x*x for x in v1))
        sumyy = sum((y*y for y in v2))
        return sumxy / (sumxx * sumyy)**.5

    def min_distance(self, vector_base, vectors):
        import heapq
        distance = lambda x, y: sum((x_i - y_i)**2 for x_i, y_i in izip(x, y))**.5
        #distance = self. cosine_similarity
        distances = [(vector[0], distance(vector_base[1], vector[1])) for vector in vectors if vector_base[0] != vector[0]]
        return heapq.nsmallest(15, distances, key=lambda x: x[1])
        #return heapq.nlargest(15, distances, key=lambda x: x[1])

    @classmethod
    def create_vector_fields_nutr(self):
        features = nutr_features()
        fields, omegas = self.subs_omegas([(e[0], e[1], 0, None) for e in features])
        fields = fields + [(v[0], k, v[1], v[2]) for k, v in omegas.items()]
        #exclude = set(["208", "268"]) #Energy#ENERC_KCAL", "Energy#ENERC_KJ"
        base = set([v[0] for v in fields])
        return [e for e in base.difference(set(exclude_nutr.keys()))]

    @classmethod
    def get_matrix(self, name):
        try:
            matrix = pickle.load(open(name, 'rb'))
        except IOError:
            matrix = []
        return matrix

    @classmethod
    def save_matrix(self, name, matrix):
        pickle.dump(matrix, open(name, 'wb'))

    def similarity(self):
        matrix = self.get_matrix('matrix.p')
        fields = self.create_vector_fields_nutr()
        vector_base = self.vector_features(fields, self.nutrients)
        foods = self.min_distance((self.ndb_no, vector_base.values()), matrix)
        return [(ndb_no, self.get_food(ndb_no), v) for ndb_no, v in foods]

    @classmethod
    def alimentos(self, category=None, limit="limit 10"):
        _, cursor = conection()
        if category:
            query  = """SELECT food_des.ndb_no
                        FROM food_des, fd_group
                        WHERE fd_group.fdgrp_cd=food_des.fdgrp_cd
                        AND fd_group.fdgrp_cd='{category}' {limit}""".format(category=category, limit=limit)
        else:
            query  = """SELECT food_des.ndb_no
                        FROM food_des, fd_group
                        WHERE fd_group.fdgrp_cd=food_des.fdgrp_cd {limit}""".format(limit=limit)

        cursor.execute(query)
        return (x[0] for x in cursor.fetchall())

    @classmethod
    def train(self):
        matrix = self.get_matrix('matrix.p')
        fields = self.create_vector_fields_nutr()
        if len(matrix) == 0:
            print "Not pickle"
            ndb_nos = self.alimentos(limit="limit 9000")#"Fruits and Fruit Juices"
            for ndb_no in ndb_nos:
                records = self.get_raw_nutrients(ndb_no)
                vector = self.vector_features(fields, records)
                #nutrients = group_data(records, exclude=set(exclude_nutr.keys()))
                #vector = self.vector_features(fields, nutrients.values()[0])
                matrix.append((ndb_no, vector.values()))
            self.save_matrix('matrix.p', matrix)

    def mark_caution_good_nutrients(self):
        #nutr_no, nutr, v, u, caution, good
        nutrients = self.mark_nutrients()
        return ((n[0], n[1], n[2], n[3], int((n[2] > avg[2]) and n[4]), int((n[2] > avg[2]) and not n[4])) 
            for n, avg in izip(nutrients, self.nutr_avg))

    def mark_nutrients(self):
        return mark_caution_nutr(self.nutrients)

