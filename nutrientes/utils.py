# -*- coding: utf-8 -*-
import psycopg2
import re
import pickle

from itertools import izip
from django.core.exceptions import ImproperlyConfigured

try:
    from django.conf import settings
    PREPROCESSED_DATA_DIR = settings.PREPROCESSED_DATA_DIR
except ImproperlyConfigured:
    import os
    PREPROCESSED_DATA_DIR = os.path.dirname(os.path.dirname(__file__)) + '/preprocessed_data/'

USERNAME = 'agmartinez'


def conection():
    conn_string = "host='/var/run/postgresql/' dbname='alimentos' user='{username}'".format(username=USERNAME)
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()
    return conn, cursor

def exclude_data(data, exclude=set([])):
    return [(nutr_no, nut, float(v), u) for nutr_no, nut, v, u in data if not nutr_no in exclude]

def nutr_features(order_by="sr_order"):
    _, cursor = conection()
    query  = """SELECT nutr_no, nutrdesc FROM nutr_def ORDER BY {order_by}""".format(order_by=order_by)
    cursor.execute(query)
    return cursor.fetchall()

def nutr_features_group(order_by="sr_order"):
    _, cursor = conection()
    query  = """SELECT nutr_no, nutrdesc, nutr_def.group, nutr_def.desc FROM nutr_def ORDER BY {order_by}""".format(order_by=order_by)
    cursor.execute(query)
    return cursor.fetchall()

def nutr_features_ids(ids):
    _, cursor = conection()
    ids_order = ",".join(("(%s,'%s')" % (i, id) for i, id in enumerate(ids)))
    omegas = set([omega.replace(" ", "") for omega in OMEGAS.keys()])
    omegas_index = []
    for omega in omegas:
        try:
            omegas_index.append((ids.index(omega), omega))
        except ValueError:
            pass
    if len(ids_order) > 0:
        query = """SELECT nutr_def.nutr_no, nutrdesc 
                    FROM nutr_def JOIN (VALUES {ids}) as x (ordering, nutr_no) 
                    ON nutr_def.nutr_no = x.nutr_no ORDER BY x.ordering""".format(ids=ids_order)
        cursor.execute(query)
        data = cursor.fetchall()
        for index, omega in omegas_index:
            data.insert(index, (omega, omega))
        return data
    else:
        return []

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

def avg_omega():
    from collections import namedtuple
    Omegas = namedtuple('Omega', 'omega3 omega6 omega7 omega9 radio')
    _, cursor = conection()
    query = """SELECT AVG(omega3), AVG(omega6), AVG(omega7), AVG(omega9), AVG(radio) FROM omega"""
    cursor.execute(query)
    return Omegas(*map(float, cursor.fetchall()[0]))

def normalize(raw_data, index, base):
    return [list(value[0:index]) + [value[index] / base] + list(value[index+1:len(value)]) for value in raw_data]

def avg_nutrients_group_nutr(nutr_no, order_by="avg"):
    _, cursor = conection()
    query = """SELECT fd_group.fdgrp_desc_es, AVG(nutr_val) as avg
            FROM nut_data, food_des, fd_group
            WHERE fd_group.fdgrp_cd=food_des.fdgrp_cd
            AND nut_data.ndb_no=food_des.ndb_no
            AND nut_data.nutr_no='{nutr_no}' GROUP BY fd_group.fdgrp_desc_es ORDER BY {order};""".format(nutr_no=nutr_no, order=order_by)
    cursor.execute(query)
    return cursor.fetchall()

def avg_nutrients_group_omega():
    _, cursor = conection()
    query = """SELECT fd_group.fdgrp_desc_es, AVG(omega3), AVG(omega6), AVG(omega7), AVG(omega9), AVG(radio)
            FROM omega, food_des, fd_group
            WHERE fd_group.fdgrp_cd=food_des.fdgrp_cd
            AND omega.ndb_no=food_des.ndb_no
            GROUP BY fd_group.fdgrp_desc_es"""
    cursor.execute(query)
    return cursor.fetchall()

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

def category_food_count(category):
    _, cursor = conection()
    query = """
        SELECT COUNT(food_des.fdgrp_cd)
        FROM food_des, fd_group
        WHERE fd_group.fdgrp_cd=food_des.fdgrp_cd 
        AND food_des.fdgrp_cd='{category}';
    """.format(category=category)
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
    # 606 grasa saturada
    # 204 total grasas
    for i, nutr_no in enumerate(["601", "606", "269", "262", "307", "208", "209"]):
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
                AND fd_group.fdgrp_cd='{category}'
                ORDER BY food_des.long_desc_es {limit}""".format(category=category, limit=limit)

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
    nutr = Food.get_matrix(PREPROCESSED_DATA_DIR + "nutavg.p")
    nutr_avg = {nutr_no:(avg, caution) for nutr_no, nutr_desc, avg, _, caution in mark_caution_nutr(nutr) if nutr_no in nutr_no_list}
    querys = []

    for nutr_no, (avg, caution) in nutr_avg.items():
        query = query_build(nutr_no, category_food)
        cursor.execute(query)
        querys.append((nutr_no, caution, avg, cursor.fetchall()))

    def get_ids_intersection(cat):
        if len(cat.values()) > 0:
            set_base = set(cat.values()[0]["data"].keys())
            for v in cat.values()[1:]:
                set_base = set_base.intersection(set(v["data"].keys()))
            return set_base
        else:
            return set([])

    rank = Rank(querys)
    rank.base_food = get_ids_intersection(rank.category_nutr)
    return rank

def ranking_nutr(category_food=None):
    _, cursor = conection()
    
    if category_food is None:
        query = """SELECT food_des.ndb_no, long_desc_es, fd_group.fdgrp_cd, fdgrp_desc_es, food_des.long_desc
                FROM food_des, ranking, fd_group
                WHERE food_des.ndb_no=ranking.ndb_no
                AND fd_group.fdgrp_cd=food_des.fdgrp_cd
                AND type_position = 'global'
                ORDER BY position"""
    else:
        query = """SELECT position, food_des.ndb_no, food_des.long_desc_es, food_des.long_desc
                FROM food_des, ranking, fd_group
                WHERE food_des.ndb_no=ranking.ndb_no
                AND fd_group.fdgrp_cd=food_des.fdgrp_cd
                AND type_position = 'category'
                AND fd_group.fdgrp_cd='{category}'
                ORDER BY position""".format(category=category_food)

    cursor.execute(query)
    return cursor.fetchall()


def ranking_nutr_detail(ndb_no, type_position):
    _, cursor = conection()
    
    if type_position is "global":
        query = """SELECT nutr_def.nutr_no, nutr_def.nutrdesc, position
                FROM nutr_def, ranking_food_detail
                WHERE ranking_food_detail.ndb_no='{ndb_no}'
                AND nutr_def.nutr_no=ranking_food_detail.nutr_no
                AND type_position = 'global'
                ORDER BY nutr_def.nutrdesc""".format(ndb_no=ndb_no)
    else:
        query = """SELECT nutr_def.nutr_no, nutr_def.nutrdesc, position
                FROM nutr_def, ranking_food_detail
                WHERE ranking_food_detail.ndb_no='{ndb_no}'
                AND nutr_def.nutr_no=ranking_food_detail.nutr_no
                AND type_position = 'category'
                ORDER BY nutr_def.nutrdesc""".format(ndb_no=ndb_no)

    cursor.execute(query)
    return cursor.fetchall()
 

class Rank(object):
    def __init__(self, base_food_querys):
        self.foods = {}
        self.category_nutr = {}
        self.base_food = None
        self.base_food_querys = base_food_querys
        self.category_nutr = self.get_categories_nutr()
        self.ranks = None
        self.results = None

    def get_categories_nutr(self):
        category_nutr = {}
        for nutr_no, caution, avg, result_query in self.base_food_querys:
            category_nutr[nutr_no] = {"caution": caution, "data": {}, "avg": avg, "units": None}
            units = None
            for ndb_no, long_desc_es, nutr_val, units in result_query:
                category_nutr[nutr_no]["data"][ndb_no] = float(nutr_val)
                self.foods[ndb_no] = long_desc_es
            category_nutr[nutr_no]["units"] = units
        return category_nutr

    def ids2data_sorted(self):
        from collections import OrderedDict
        data = OrderedDict()
        if self.base_food is None:
            self.base_food = set(self.foods.keys())
        for nutr_no in self.category_nutr.keys():
            data.setdefault(nutr_no, [])
            reverse = not bool(self.category_nutr[nutr_no]["caution"])
            for ndb_no in self.base_food:
                nutr_val = self.category_nutr[nutr_no]["data"].get(ndb_no, 0.0)
                data[nutr_no].append((ndb_no, self.foods.get(ndb_no, None), nutr_val))
            data[nutr_no].sort(reverse=reverse, key=lambda x: x[2])
        return data
    
    def sorted_data(self, category_nutr):
        positions = {}
        for nutr_no in category_nutr.keys():
            weight = weight_nutrs.get(nutr_no, 1)
            for i, v in self.rank2natural(category_nutr[nutr_no], f_index=lambda x: x[2]):
                positions.setdefault(v[0], {"attr": v[:2], "i": 0, "val": []})
                positions[v[0]]["i"] += i * weight
                # we evaluate if is 'caution' v[5]
                avg = self.category_nutr[nutr_no]["avg"]
                caution = self.category_nutr[nutr_no]["caution"]
                diff_avg = v[2] - avg if not caution else avg - v[2]
                positions[v[0]]["val"].append(
                    (v[2], diff_avg, self.category_nutr[nutr_no]["units"]))
                self.set_rank(v[0], nutr_no, i)
        return sorted(positions.values(), key=lambda x: x["i"])

    def set_rank(self, ndb_no, nutr_no, position):
        if self.ranks is None:
            self.ranks = {}
        self.ranks.setdefault(ndb_no, {})
        self.ranks[ndb_no][nutr_no] = position

    def get_values_food(self, ndb_no):
        if self.ranks is None:
            category_nutr = self.ids2data_sorted()
            self.sorted_data(self, category_nutr)            
        return self.ranks[ndb_no]

    @classmethod
    def rank2natural(self, data, f_index):
        base = None
        index = 0
        for d in data:
            if base != f_index(d):
                base = f_index(d)
                index += 1
            yield index, d
    
    def order(self):
        return self.rank2natural(self.sorted_data(self.ids2data_sorted()), f_index=lambda x: x["i"])
    

def query_build(nutr_no, category_food, name=None, order_by=None):
    attrs = {"nutr_no": nutr_no}
    if nutr_no.startswith("omega"):
        query = """
            SELECT food_des.ndb_no, food_des.long_desc_es||'#'||food_des.long_desc, {omega} as nutr_val, 'g'
            FROM food_des, omega 
            WHERE omega.ndb_no=food_des.ndb_no"""
        attrs["omega"] = nutr_no
    else:
        query = """
            SELECT food_des.ndb_no, food_des.long_desc_es||'#'||food_des.long_desc, nutr_val, units
            FROM nut_data, food_des, nutr_def
            WHERE nut_data.ndb_no=food_des.ndb_no
            AND nutr_def.nutr_no=nut_data.nutr_no
            AND nut_data.nutr_no='{nutr_no}'"""

    if name is not None:
        query += """ AND long_desc_es ilike '%{name}%'"""
        attrs["name"] = name

    if category_food:
        query += """ AND food_des.fdgrp_cd='{category_food}'"""
        attrs["category_food"] = category_food

    if order_by is not None:
        query += """ ORDER BY nutr_val {order_by}""".format(order_by=order_by)
    query = query.format(**attrs)
    return query

def radio_omega(category=None):
    _, cursor = conection()
    if category is None:
        query = """SELECT ndb_no, radio FROM omega"""
    else:
        query = """SELECT food_des.ndb_no, radio 
                    FROM omega, food_des, fd_group
                WHERE food_des.ndb_no=omega.ndb_no
                AND fd_group.fdgrp_cd=food_des.fdgrp_cd
                AND fd_group.fdgrp_cd='{category}'""".format(category=category)
    cursor.execute(query)
    return cursor.fetchall()

def best_of_general_2(category=None, name=None):
    _, cursor = conection()
    nutr = Food.get_matrix(PREPROCESSED_DATA_DIR + "nutavg.p")
    # hasheamos las llaves para mantener el orden
    nutr_avg = {nutr_no:(avg, caution) for nutr_no, nutr_desc, avg, _, caution in mark_caution_nutr(nutr)}

    querys = []
    for nutr_no, (avg, caution) in nutr_avg.items():
        query = query_build(nutr_no, category)
        cursor.execute(query)
        querys.append((nutr_no, caution, avg, cursor.fetchall()))

    rank = Rank(querys)
    total = {food["attr"][0]: {"global": i, "name": food["attr"][1]} for i, food in rank.order()}

    for ndb_no, radio in radio_omega(category=category):
        if not ndb_no in total:
            total[ndb_no] = {}

        if 0 < radio <= 4:
            total[ndb_no]["radio"] = -normal(float(radio-1), 0, 0.3993)
        elif radio == 0:
            total[ndb_no]["radio"] = 6533/150.
        else:
            total[ndb_no]["radio"] = float(radio)
    
    results = [(v.get("global", 10000) + v.get("radio", 0), ndb_no, v.get("name", "")) 
        for ndb_no, v in total.items()]
    results.sort()
    rank.results = results
    return rank

def normal(x, u, s):
    import math
    return math.exp(-((x-u)**2)/(2*(s**2)))/(s*((2*math.pi)**.5))

weight_nutrs = {
    "255": 10.0, #Water
    "601": 10.0, #Cholesterol
    "269": 8.0, #Sugars, total
    "262": 10.5, #Caffeine
    "307": 7.5, #Sodium, Na
    "605": 9.6, #Fatty acids, total trans
    "606": 9.5, #Fatty acids, total saturated
    "607": 8.5, #4:0
    "609": 8.5, #8:0
    "608": 8.5, #6:0
    "204": 1.1, #Total lipid (fat)
    "omega3": 0.05,
    "205": 1.5, #Carbohydrate, by difference
    "211": 5.0, #Glucose (dextrose)
    "212": 7.0, #Fructose
    "210": 3.0, #Sucrose
    "203": .5,  #Protein
    "209": 3.0, #Starch
    "431": .5,  #Folic acid
    "213": 4.0, #Lactose
    "287": 4.0, #Galactose
    "214": 3.0, #Maltose
    "207": 3.0,  #Ash
    "291": .5,   #Fiber, total dietary
    "313": 8.5,  #Fluoride, F
    "omega6": 1.8
}

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
    "607": "4:0",
    "609": "8:0",
    "608": "6:0",
    "313": "Fluoride, F",
    "212": "Fructose",
    "211": "Glucose (dextrose)",
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
        self.name_en = None
        self.group = None
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

    def ranking(self):
        _, cursor = conection()
        query = """SELECT position 
                    FROM ranking 
                    WHERE ndb_no = '{ndb_no}'
                    AND type_position='global'""".format(ndb_no=self.ndb_no)
        cursor.execute(query)
        global_ = cursor.fetchall()
        query = """SELECT position 
                    FROM ranking 
                    WHERE ndb_no = '{ndb_no}'
                    AND type_position='category'""".format(ndb_no=self.ndb_no)
        cursor.execute(query)
        category = cursor.fetchall()
        if len(global_) > 0:
            return {"global": global_[0][0], "category": category[0][0]}
        return None

    def ranking_nutr(self):
        _, cursor = conection()
        nutr = Food.get_matrix(PREPROCESSED_DATA_DIR + "nutavg.p")
        # hasheamos las llaves para mantener el orden
        nutr_avg = {nutr_no:(avg, caution) for nutr_no, nutr_desc, avg, _, caution in mark_caution_nutr(nutr)}

        querys = []
        for nutr_no, (avg, caution) in nutr_avg.items():
            query = query_build(nutr_no, category)
            cursor.execute(query)
            querys.append((nutr_no, caution, avg, cursor.fetchall()))

        rank = Rank(querys)
        total = {food["attr"][0]: {"global": i, "name": food["attr"][1]} for i, food in rank.order()}

    def radio(self):
        if self.radio_omega_raw == 0 and self.omegas.get("omega3", [0,0])[1] == 0:
            return "%s:0" % (round(self.omegas.get("omega6", [0,0])[1], 2),)
        else:
            return "%s:1" % (self.radio_omega_raw,)

    @classmethod
    def get_raw_nutrients(self, ndb_no):
        _, cursor = conection()
        query  = """SELECT nutr_def.nutr_no, nutrdesc, nutr_val, units
                    FROM nut_data, nutr_def
                    WHERE nutr_def.nutr_no=nut_data.nutr_no
                    AND nutr_val > 0
                    AND nut_data.ndb_no='{ndb_no}' ORDER BY sr_order""".format(ndb_no=ndb_no)
        cursor.execute(query)
        return cursor.fetchall()

    @classmethod
    def get_food(self, ndb_no):
        _, cursor = conection()
        query  = """SELECT food_des.long_desc_es, fd_group.fdgrp_desc_es, fd_group.fdgrp_cd, food_des.long_desc
                    FROM food_des, fd_group
                    WHERE fd_group.fdgrp_cd=food_des.fdgrp_cd 
                    AND food_des.ndb_no = '{ndb_no}'""".format(ndb_no=ndb_no)
        cursor.execute(query)
        return cursor.fetchall()

    def get(self, ndb_no=None, avg=True):
        if self.ndb_no is None and ndb_no is not None:
            self.ndb_no = ndb_no
        records = self.get_raw_nutrients(self.ndb_no)
        e_data = exclude_data(records, exclude=set(["268"])) #Energy#ENERC_KJ
        food = self.get_food(self.ndb_no)
        self.name = food[0][0]
        self.name_en = food[0][3]
        self.group = {"name": food[0][1], "id": food[0][2]}
        features, omegas = self.subs_omegas(e_data)
        self.nutrients = features + [(v[0], k, v[1], v[2]) for k, v in omegas.items()]
        self.radio_omega_raw = self.radio_raw(omegas.get("omega 6", [0,0,0])[1], omegas.get("omega 3", [0,0,0])[1])
        self.omegas = omegas
        if avg:
            nutavg_vector = self.get_matrix(PREPROCESSED_DATA_DIR + "nutavg.p")
            if len(nutavg_vector) == 0:
                #appended the units with blank ''
                omegas = avg_omega()
                allnutavg_vector = [e[1:] + [""] for e in sorted(avg_nutrients().values())] +\
                                zip(omegas._fields[:-1], sorted(OMEGAS.keys()), omegas[:-1], ['g'] * len(omegas[:-1]))
                nutavg_vector, _ = self.subs_omegas(allnutavg_vector)
                self.save_matrix(PREPROCESSED_DATA_DIR + "nutavg.p", nutavg_vector)
            self.nutr_avg = {k: (name, v, u) for k, name, v, u in self.exclude_features(nutavg_vector)}

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
                    omegas.setdefault(omega, [omega.replace(" ", ""), 0, u])
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

    def min_distance(self, vector_base, vectors, top=15):
        import heapq
        distance = lambda x, y: sum((x_i - y_i)**2 for x_i, y_i in izip(x, y))**.5
        #distance = self. cosine_similarity
        distances = ((vector[0], distance(vector_base[1], vector[1])) for vector in vectors if vector_base[0] != vector[0])
        return heapq.nsmallest(top, distances, key=lambda x: x[1])
        #return heapq.nlargest(15, distances, key=lambda x: x[1])

    @classmethod
    def create_vector_fields_nutr(self, exclude_nutr_l=None):
        if exclude_nutr_l is None:
            exclude_nutr_l = exclude_nutr.keys()
        features = nutr_features()
        fields, omegas = self.subs_omegas([(e[0], e[1], 0, None) for e in features])
        fields = fields + [(v[0], k, v[1], v[2]) for k, v in omegas.items()]
        base = set([v[0] for v in fields])
        return [e for e in base.difference(set(exclude_nutr_l))]

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

    def similarity(self, matrix=None, raw=False, top=15):
        if matrix is None:
            matrix = self.get_matrix(PREPROCESSED_DATA_DIR + 'matrix.p')
        fields = self.create_vector_fields_nutr()
        vector_base = self.vector_features(fields, self.nutrients)
        foods = self.min_distance((self.ndb_no, vector_base.values()), matrix, top=top)
        if raw:
            return [(ndb_no, v) for ndb_no, v in foods]
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

    def mark_caution_good_nutrients(self):
        #nutr_no, nutr, v, u, caution, good
        nutrients = self.mark_nutrients()
        return ((n[0], n[1], n[2], n[3], int((n[2] > self.nutr_avg[n[0]][1]) and n[4]), int((n[2] > self.nutr_avg[n[0]][1]) and not n[4])) 
            for n in nutrients)

    def mark_nutrients(self):
        return mark_caution_nutr(self.nutrients)

    def caution_good_nutr_avg(self):
        good = len(filter(lambda x: x[5], self.mark_caution_good_nutrients()))
        bad = len(filter(lambda x: x[4], self.mark_caution_good_nutrients()))
        return {"total": len(self.nutrients),
            "good": good,
            "bad": bad}

    def ranking_nutr_detail_base(self, type_category):
        tabla_nutr_rank = ranking_nutr_detail(self.ndb_no, type_category)
        nutr_base = set([nutr_no for nutr_no, _, _, _ in self.nutrients])
        tabla_nutr_rank = [(desc, position, "{0:04d}".format(position)) 
                for nutr, desc , position in tabla_nutr_rank if nutr in nutr_base]
        return tabla_nutr_rank


def create_common_table(dicts):
    common_keys = set(dicts[0].keys())
    not_common_keys = set(dicts[0].keys())
    global_keys = {}
    for dict_ in dicts[1:]:
        not_common_keys = not_common_keys.union(dict_.keys())
        common_keys = common_keys.intersection(dict_.keys())
    
    for dict_ in dicts:
        for k, v in dict_.items():
            if k not in global_keys:
                global_keys[k] = v[1]
    not_common_keys = not_common_keys.difference(common_keys)

    table = []
    for dict_ in dicts:
        data_c = [dict_[key] for key in common_keys]
        data_nc = [dict_.get(key, ('', global_keys[key], 0, '')) for key in not_common_keys]
        table.append(data_c+data_nc)
    return table

def create_matrix(ndb_nos, exclude_nutr=None):
    fields = Food.create_vector_fields_nutr(exclude_nutr_l=exclude_nutr)
    matrix = [(ndb_no, Food.vector_features(fields, Food.get_raw_nutrients(ndb_no)).values()) 
                for ndb_no in ndb_nos]
    return matrix


def principal_nutrients(category=None):
    _, cursor = conection()
    if category is None:
        query = """SELECT nutrdesc, AVG(nutr_val) as avg, units 
                FROM nut_data, nutr_def 
                WHERE nut_data.nutr_no=nutr_def.nutr_no 
                GROUP BY nutrdesc,units ORDER BY avg desc"""
    else:
        query = """SELECT nutrdesc, AVG(nutr_val) as avg, units 
                FROM nut_data, nutr_def, food_des, fd_group 
                WHERE nut_data.nutr_no=nutr_def.nutr_no 
                AND fd_group.fdgrp_cd=food_des.fdgrp_cd 
                AND food_des.ndb_no=nut_data.ndb_no 
                AND food_des.fdgrp_cd='{category}' 
                GROUP BY nutrdesc,units ORDER BY avg desc""".format(category=category)
    cursor.execute(query)
    units_scale = {"g": 1, "mg": 1000, "µg": 1000000}
    totals = []
    for nutrdesc, avg, units in cursor.fetchall():
        val = units_scale.get(units, 0)
        if val != 0:
            totals.append((nutrdesc, float(avg / val)))
    return sorted(totals, key=lambda x: x[1], reverse=True)

def most_similar_food(ndb_no, category_to_search, exclude_nutr=None):
    _, cursor = conection()
    #from numba import jit
    food_base = Food(ndb_no, avg=False)

    exclude_nutr = {
        "601": "Cholesterol",
        "269": "Sugars, total",
        "605": "Fatty acids, total trans",
        "606": "Fatty acids, total saturated",
        "645": "Fatty acids, total monounsaturated",
        "646": "Fatty acids, total polyunsaturated",
        "695": "Fatty acids, total trans-polyenoic",
        "693": "Fatty acids, total trans-monoenoic",
        "204": "Total lipid (fat)",
        "307": "Sodium, Na",
        "607": "4:0",
        "609": "8:0",
        "608": "6:0",
    }

    vector_base = food_base.vector_features(
        food_base.create_vector_fields_nutr(exclude_nutr_l=exclude_nutr), 
        food_base.nutrients)
    ndb_nos = (ndb_no for ndb_no, _ in alimentos_category(category=category_to_search, limit="limit 9000"))
    matrix = create_matrix(ndb_nos, exclude_nutr=exclude_nutr)
    matrix_dict = {ndb_no: vector for ndb_no, vector in matrix}
    vector_base_values = vector_base.items()


    def search(base_size, low_grow, data, extra_data=[], min_diff=10):
        diffs = []
        down_vectors = []
        every = 5
        count = 0
        for foods in data:
            foods_extra = foods+extra_data
            rows = (matrix_dict[ndb_no] for ndb_no, _ in foods_extra)
            total = (sum(sublist) for sublist in izip(*rows))
            diff = [(t-b[1], b[0]) for t, b in izip(total, vector_base_values)]
            up_diff = filter(lambda x: x, (r >= 0 for r, _ in diff))
            diffs.append((len(vector_base_values) - len(up_diff)))
            if len(vector_base_values) - len(up_diff) <= min_diff:
                print "....", len(vector_base_values) - len(up_diff)
                return foods_extra

            down_vectors.append(((r, nutr_no) for r, nutr_no in diff if r < 0))
            if count == every:
                null_grow = grown(down_vectors)
                down_vectors = []
                count = 0
                low_grow.append(null_grow)
            count += 1        
        print base_size, "MIN", min(diffs)

    def grown(vectors):
        null_grow = set([])
        for sublist in izip(*vectors):
            if sublist[0][0] != 0:
                grow_ = (((sublist[-1][0] / sublist[0][0])**len(sublist)) - 1) * 100
                if grow_ <= 1: #1%
                    null_grow.add(sublist[0][1])

        return null_grow

    def random_select(matrix, size):
        import random
        indexes = set([])
        for i in xrange(1000):
            blocks = []
            while len(blocks) < size:
                i = random.randint(0, len(matrix) - 1)
                if not i in indexes:
                    indexes.add(i)
                    blocks.append((matrix[i][0], None))
            indexes = set([])
            yield blocks

    def random(extra_food=[], min_amount_food=2, amount_food=5, min_diff=10):
        counting = {}
        for food_size in xrange(min_amount_food, amount_food):
            data = random_select(matrix, food_size)
            low = []
            foods = search(food_size, low, data, extra_data=extra_food, min_diff=min_diff)
            for s in low:
                for nutr_no in s:
                    counting[nutr_no] =  counting.get(nutr_no, 0) + 1
            if foods is not None:
                return foods, True
        return sorted(counting.items(), key=lambda x: x[1], reverse=True), False

    results, ok = random()
    step_best = 1
    count = {}
    nutrs_no = set([])
    amount_food = 5
    min_amount_food = 2
    min_diff = 10
    result_best = None
    while True:
        for nutr_no, _ in results:
            if not nutr_no in nutrs_no:
                query = query_build(nutr_no, category_to_search, order_by="DESC")
                cursor.execute(query)
                for r in cursor.fetchall()[:5]:
                    count[r[0]] = count.get(r[0], 0) + 1
                nutrs_no.add(nutr_no)
        best_extra_food = sorted(count.items(), key=lambda x: x[1], reverse=True)
        if step_best > 10:
            amount_food += 1
            step_best = 1
            min_amount_food = amount_food - 1
        else:
            step_best += 1
        results, ok = random(
            extra_food=best_extra_food[:step_best], 
            min_amount_food=min_amount_food, 
            amount_food=amount_food,
            min_diff=min_diff)

        if ok:
            print "----BEST"
            print best_extra_food[:step_best]
            result_best = results
            min_diff -= 1

        if not ok and amount_food > 6:
            break

        print "Amount Food", amount_food - 1
        print "STEP", step_best
        print min_diff
        #print "----BEST"
        #print best_extra_food

    print "***** ok"
    print result_best
