import psycopg2
import re
import pickle

from itertools import izip

USERNAME = 'agmartinez'

VALUE = """
Omega 3
"""

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

def nutr_features():
    _, cursor = conection()
    query  = """SELECT nutr_no, nutrdesc FROM nutr_def order by sr_order""";
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
        query = """INSERT INTO omega VALUES ({ndb_no}, {omega3}, {omega6}, {omega7}, {omega9}, {radio});""".format(
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
    query = """SELECT fd_group.fdgrp_desc, AVG(nutr_val) as avg
            FROM nut_data, food_des, fd_group
            WHERE fd_group.fdgrp_cd=food_des.fdgrp_cd
            AND nut_data.ndb_no=food_des.ndb_no
            AND nut_data.nutr_no='{nutr_no}' GROUP BY fd_group.fdgrp_desc ORDER BY {order};""".format(nutr_no=nutr_no, order=order_by)
    cursor.execute(query)
    return cursor.fetchall()

def avg_nutrients_group():
    _, cursor = conection()
    query = """SELECT nut_data.nutr_no, fd_group.fdgrp_desc, AVG(nutr_val)
            FROM nut_data, food_des, fd_group, nutr_def
            WHERE fd_group.fdgrp_cd=food_des.fdgrp_cd
            AND nut_data.ndb_no=food_des.ndb_no
            AND nutr_def.nutr_no=nut_data.nutr_no GROUP BY fd_group.fdgrp_desc, nut_data.nutr_no;"""
    cursor.execute(query)
    nutr = {e[0]:[i, e[0], e[1]] for i, e in enumerate(nutr_features())}
    for nutr_no, fdgrp_desc, avg in cursor.fetchall():
        nutr[nutr_no].append(float(avg))
    return nutr

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
        SELECT fd_group.fdgrp_desc, COUNT(fd_group.fdgrp_desc)
        FROM food_des, fd_group
        WHERE fd_group.fdgrp_cd=food_des.fdgrp_cd GROUP BY fd_group.fdgrp_desc ORDER BY fd_group.fdgrp_desc;
    """
    cursor.execute(query)
    return cursor.fetchall()    

def category_food_list():
    #nutr = avg_nutrients_group()
    for nutr_no in ["601", "204", "269", "262", "307", "208", "209"]:
        l = avg_nutrients_group_nutr(nutr_no, order_by="fd_group.fdgrp_desc")
        #print nutr[nutr_no]
    

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
    "209": "Starch",
    "omega 6": "Omega 6"
}

bases = ["n-3", "n-6", "n-7", "n-9"]
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
                    AND food_des.ndb_no = '{ndb_no}' ORDER BY sr_order""".format(ndb_no=ndb_no)
        cursor.execute(query)
        return cursor.fetchall()

    @classmethod
    def get_food(self, ndb_no):
        _, cursor = conection()
        query  = """SELECT food_des.long_desc_es, fd_group.fdgrp_desc
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
            self.nutr_avg = self.exclude_features(all_nutr) + [(v[0], k, v[1], v[2]) for k, v in omegas.items()]

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

                if molecula_txt in OMEGAS["omega 3"] or tipo_molecula_txt == "n-3":
                    omega = "omega 3"
                elif molecula_txt in OMEGAS["omega 6"] or tipo_molecula_txt == "n-6":
                    omega = "omega 6"
                elif molecula_txt in OMEGAS["omega 7"] or tipo_molecula_txt == "n-7":
                    omega = "omega 7"
                elif molecula_txt in OMEGAS["omega 9"] or tipo_molecula_txt == "n-9":
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
    def create_vector(self, nutrients):
        features = nutr_features()
        fields, omegas = self.subs_omegas([(e[0], e[1], 0, None) for e in features])
        fields = fields + [(v[0], k, v[1], v[2]) for k, v in omegas.items()]
        exclude = set(["208", "268"]) #Energy#ENERC_KCAL", "Energy#ENERC_KJ"
        base = set([v[0] for v in fields])
        fields = [e for e in base.difference(exclude)]
        return self.vector_features(fields, nutrients)

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
        vector_base = self.create_vector(self.nutrients)
        foods = self.min_distance((self.ndb_no, vector_base.values()), matrix)
        return [(ndb_no, self.get_food(ndb_no), v) for ndb_no, v in foods]


    @classmethod
    def alimentos(self, category=None, limit="limit 10"):
        _, cursor = conection()
        if category:
            query  = """SELECT food_des.ndb_no
                        FROM food_des, fd_group
                        WHERE fd_group.fdgrp_cd=food_des.fdgrp_cd
                        AND fd_group.fdgrp_desc='{category} {limit}""".format(category=category)
        else:
            query  = """SELECT food_des.ndb_no
                        FROM food_des, fd_group
                        WHERE fd_group.fdgrp_cd=food_des.fdgrp_cd {limit}""".format(limit=limit)

        cursor.execute(query)
        return (x[0] for x in cursor.fetchall())

    @classmethod
    def train(self):
        matrix = self.get_matrix('matrix.p')
        if len(matrix) == 0:
            print "Not pickle"
            ndb_nos = self.alimentos(limit="limit 9000")#"Fruits and Fruit Juices"
            for ndb_no in ndb_nos:
                records = self.get_raw_nutrients(ndb_no)
                nutrients = group_data(records)
                vector = self.create_vector(nutrients.values()[0])
                matrix.append((ndb_no, vector.values()))
            self.save_matrix('matrix.p', matrix)

    def filter_caution_nutr(self):
        #nutr_no, _, v, _, caution
        nutrients = self.mark_nutrients()
        nutr_avg = self.mark_nutr_avg()
        return filter(lambda x: x[1], ((n[1], (n[2] > avg[2]) and n[4]) for n, avg in izip(nutrients, nutr_avg)))
        
    def mark_caution_nutrients(self):
        nutrients = self.mark_nutrients()
        nutr_avg = self.mark_nutr_avg()
        return ((n[0], n[1], n[2], n[3], int((n[2] > avg[2]) and n[4])) for n, avg in izip(nutrients, nutr_avg))

    def mark_nutrients(self):
        return mark_caution_nutr(self.nutrients)

    def mark_nutr_avg(self):
        return mark_caution_nutr(self.nutr_avg)
