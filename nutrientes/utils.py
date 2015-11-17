# -*- coding: utf-8 -*-
import psycopg2
import re
import pickle
import heapq

from collections import OrderedDict
from functools import wraps
import os

from django.conf import settings
from nutrientes.weights import WEIGHT_NUTRS

PREPROCESSED_DATA_DIR = os.path.dirname(os.path.dirname(__file__)) + '/preprocessed_data/'
USERNAME = settings.DATABASES["default"]["USER"]
RNV_TYPE = {2: "NOM-051-SCFI/SSA1-2010", 1: "USACAN"}
#nutrients excluded from the matrix similarity, because are the sum of others
#nutrients
EXCLUDE_NUTR = {
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
    "203": "Protein",
}

OMEGAS = {
    "omega 3": ["16:3", "18:3", "18:4", "20:3", "20:4", "20:5", "21:5", "22:5", "22:6", "24:5", "24:6"],
    "omega 6": ["18:2", "18:3", "20:2", "20:3", "20:4", "22:2", "22:4", "22:5", "24:4", "24:5"],
    "omega 7": ["12:1", "14:1", "16:1", "18:1", "20:1", "22:1", "24:1"],
    "omega 9": ["18:1", "20:1", "20:3", "22:1", "24:1"]
}

OMEGAS_DOMINAT = {
    "omega 9": ["18:1 undifferentiated", "18:1 c", "18:1 t", "20:1", 
                "20:3 undifferentiated", "22:1 c", "22:1 t", "22:1 undifferentiated", 
                "24:1 c"]
}

def conection():
    conn_string = "host='/var/run/postgresql/' dbname='alimentos' user='{username}'".format(username=USERNAME)
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()
    return conn, cursor

def exclude_data(data, exclude=set([])):
    return [(nutr_no, nut, float(v), u) for nutr_no, nut, v, u in data if not nutr_no in exclude]

def nutr_features(order_by="sr_order"):
    conn, cursor = conection()
    query  = """SELECT nutr_no, nutrdesc FROM nutr_def ORDER BY {order_by}""".format(order_by=order_by)
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()
    return data

def perfiles(rnv_type=1):
    conn, cursor = conection()
    query = """SELECT genero, edad_range, unidad_edad 
                FROM nutr_intake 
                WHERE rnv_type=%s GROUP BY genero, edad_range, unidad_edad 
                ORDER BY genero, unidad_edad, edad_range;"""
    cursor.execute(query, [rnv_type])
    data = cursor.fetchall()
    conn.close()
    return data

def nutr_features_group(order_by="sr_order"):
    _, cursor = conection()
    query  = """SELECT nutr_no, nutrdesc, nutrientes_nutrdesc.group, nutrientes_nutrdesc.desc 
                FROM nutr_def, nutrientes_nutrdesc 
                WHERE nutr_def.nutr_no=nutrientes_nutrdesc.nutr_no_t
                ORDER BY {order_by}""".format(order_by=order_by)
    cursor.execute(query)
    return cursor.fetchall()

def nutr_features_ids(ids):
    _, cursor = conection()
    ids_order = ",".join(("(%s,'%s')" % (i, id) for i, id in enumerate(ids)))
    omegas = {omega.replace(" ", ""): omega for omega in OMEGAS.keys()}
    omegas_index = []
    for omega_k, omega_v in omegas.items():
        try:
            omegas_index.append((ids.index(omega_k), omega_k, omega_v))
        except ValueError:
            pass
    if len(ids_order) > 0:
        query = """SELECT nutr_def.nutr_no, nutrdesc 
                    FROM nutr_def JOIN (VALUES {ids}) as x (ordering, nutr_no) 
                    ON nutr_def.nutr_no = x.nutr_no ORDER BY x.ordering""".format(ids=ids_order)
        cursor.execute(query)
        data = cursor.fetchall()
        for index, omega_k, omega_v in omegas_index:
            data.insert(index, (omega_k, omega_v))
        return data
    else:
        return []

def nutr_units_ids(ids):
    _, cursor = conection()
    ids_order = ",".join(("(%s,'%s')" % (i, id) for i, id in enumerate(ids)))
    omegas = {omega.replace(" ", ""): omega for omega in OMEGAS.keys()}
    omegas_index = []
    for omega_k, omega_v in omegas.items():
        try:
            omegas_index.append((ids.index(omega_k), omega_k))
        except ValueError:
            pass
    if len(ids_order) > 0:
        query = """SELECT nutr_def.nutr_no, units 
                    FROM nutr_def JOIN (VALUES {ids}) as x (ordering, nutr_no) 
                    ON nutr_def.nutr_no = x.nutr_no ORDER BY x.ordering""".format(ids=ids_order)
        cursor.execute(query)
        data = cursor.fetchall()
        for index, omega_k in omegas_index:
            data.insert(index, (omega_k, 'g'))
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

def avg_calification_group_perfil(order_by="avg"):
    _, cursor = conection()
    query = """SELECT fd_group.fdgrp_desc_es, AVG(score) as avg
            FROM ranking_perfil, food_des, fd_group
            WHERE fd_group.fdgrp_cd=food_des.fdgrp_cd
            AND ranking_perfil.ndb_no=food_des.ndb_no
            GROUP BY fd_group.fdgrp_desc_es ORDER BY {order} DESC;""".format(order=order_by)
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

def mark_caution_nutr(features, weights=WEIGHT_NUTRS):
    caution_nutr = {nutr_no: weight for nutr_no, weight in weights.items() if weight > 1}
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
    nutr = avg_nutrients()
    category_results = {}
    category_food_l = category_food()
    #fixed size list, because some categories could don't have values for a nutrient
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
        nutr_calif = len(list(filter(lambda x:x < 0, category_results[category_food_e])))
        omega_calif = 0 if omegas[category_food_e] > 4 else 1
        calif = int(((nutr_calif + omega_calif) / (float(len(category_results[category_food_e]) + 1)))*100)
        yield category_food_e, cat_id, count, category_results[category_food_e], omegas[category_food_e], calif

def category_food_list_perfil():
    category_results = {}
    category_food_l = category_food()
    cat_score = avg_calification_group_perfil(order_by="avg")#"fd_group.fdgrp_desc_es")
    
    for category_food_e, cat_id, count in category_food_l:
        category_results[category_food_e] = (cat_id, count)

    for category_food_e, score in cat_score:
        cat_id, count = category_results[category_food_e]
        yield category_food_e, cat_id, count, score

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

def get_many_food(ids):
    ids_order = ",".join(("(%s,'%s')" % (i, id) for i, id in enumerate(ids)))
    _, cursor = conection()
    query = """SELECT food_des.ndb_no, food_des.long_desc_es
                FROM food_des JOIN (VALUES {ids}) as x (ordering, ndb_no) 
                ON food_des.ndb_no = x.ndb_no ORDER BY x.ordering""".format(ids=ids_order)
    cursor.execute(query)
    return cursor.fetchall()

def best_of_query(nutr_no_list, category_food, exclude=None):
    _, cursor = conection()
    nutr = Food.get_matrix(PREPROCESSED_DATA_DIR + "nutavg.p")
    nutr_avg = {nutr_no: (avg, caution) 
        for nutr_no, nutr_desc, avg, _, caution in mark_caution_nutr(nutr) if nutr_no in nutr_no_list}
    querys = []
    for nutr_no, (avg, caution) in nutr_avg.items():
        query = query_build(nutr_no, category_food, exclude=exclude)
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


def ranking_nutr_perfil(perfil, edad_range, category_food=None):
    _, cursor = conection()
    
    if category_food is None:
        query = """SELECT food_des.ndb_no, long_desc_es, fd_group.fdgrp_cd, fdgrp_desc_es, food_des.long_desc
                FROM food_des, ranking_perfil, fd_group
                WHERE food_des.ndb_no=ranking_perfil.ndb_no
                AND fd_group.fdgrp_cd=food_des.fdgrp_cd
                AND ranking_perfil.unidad_edad=%s
                AND ranking_perfil.genero=%s
                AND ranking_perfil.rnv_type=%s
                AND ranking_perfil.edad_range=%s
                ORDER BY ranking_perfil.score DESC"""
        cursor.execute(query, [
            perfil["unidad_edad"], 
            perfil["genero"], 
            perfil["rnv_type"],
            edad_range])
    else:
        query = """SELECT ranking_perfil.score, food_des.ndb_no, food_des.long_desc_es, food_des.long_desc
                FROM food_des, ranking_perfil, fd_group
                WHERE food_des.ndb_no=ranking_perfil.ndb_no
                AND fd_group.fdgrp_cd=food_des.fdgrp_cd
                AND fd_group.fdgrp_cd=%s
                AND ranking_perfil.unidad_edad=%s
                AND ranking_perfil.genero=%s
                AND ranking_perfil.rnv_type=%s
                AND ranking_perfil.edad_range=%s
                ORDER BY ranking_perfil.score DESC"""
        cursor.execute(query, [
            category_food, 
            perfil["unidad_edad"], 
            perfil["genero"], 
            perfil["rnv_type"],
            edad_range])

    return cursor.fetchall()


class Rank(object):
    def __init__(self, base_food_querys, weights=WEIGHT_NUTRS):
        self.foods = {}
        self.category_nutr = {}
        self.base_food = None
        self.base_food_querys = base_food_querys
        self.category_nutr = self.get_categories_nutr()
        self.ranks = None
        self.results = None
        self.weight_nutrs = weights

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
    
    def sorted_data(self, category_nutr, limit):
        positions = {}
        for nutr_no in category_nutr.keys():
            weight = self.weight_nutrs.get(nutr_no, 1)
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

        if limit is None:
            return sorted(positions.values(), key=lambda x: x["i"])
        else:
            return sorted(positions.values(), key=lambda x: x["i"])[:limit]

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
    
    def order(self, limit=None):
        return self.rank2natural(self.sorted_data(self.ids2data_sorted(), limit=limit), f_index=lambda x: x["i"])
    
    def weight_order(self, omegas, limit=None, radio_o=True):
        total = {food["attr"][0]: {"global": i, "name": food["attr"][1]} for i, food in self.order(limit=limit)}

        if radio_o:
            omegas_d = dict(omegas)
            for ndb_no in total:
                radio = omegas_d[ndb_no]
                total.setdefault(ndb_no, {})

                if 0 < radio <= 4:
                    total[ndb_no]["radio"] = -normal(radio, 1, 1) * 3
                else:
                    total[ndb_no]["radio"] = normal(radio, 1, 1) * 200
        
        results = [(v.get("global", 10000) + v.get("radio", 0), ndb_no, v.get("name", "")) 
            for ndb_no, v in total.items()]
        results.sort()
        self.results = results

def query_build(nutr_no, category_food, name=None, order_by=None, exclude=None):
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

    if exclude == "processed_food":
        query += """ AND food_des.fdgrp_cd != '3600'""" ## Restaurant Foods
        #query += """ AND food_des.fdgrp_cd != '2500'""" ## Snacks
        query += """ AND food_des.fdgrp_cd != '2200'""" ## Meals, Entrees, and Side Dishes
        query += """ AND food_des.fdgrp_cd != '2100'""" ## Fast Foods

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
    rank.weight_order(radio_omega(category=category))
    return rank

def best_of_selected_food(foods, weights, limit, radio_o=True):
    nutr = Food.get_matrix(PREPROCESSED_DATA_DIR + "nutavg.p")
    nutr_avg = {nutr_no:(avg, caution) 
                for nutr_no, _, avg, _, caution in mark_caution_nutr(nutr, weights=weights)}

    nutr_detail = {}
    for food in foods:
        base_nutr = [e for e in food.nutrients if e[0] in weights]
        for nutr_no, nutrdesc, v, u in base_nutr:
            nutr_detail.setdefault(nutr_no, [])
            nutr_detail[nutr_no].append((food.ndb_no, food.name, v, u))

    querys = []
    for nutr_no, data in nutr_detail.items():
        avg, caution = nutr_avg[nutr_no]
        querys.append((nutr_no, caution, avg, data))

    rank = Rank(querys, weights=weights)
    omegas = [(food.ndb_no, food.radio_omega_raw) for food in foods]
    rank.weight_order(omegas, limit=limit, radio_o=radio_o)
    return [(i, ndb_no) for i, (_, ndb_no, _) in Rank.rank2natural(rank.results, f_index=lambda x: x[0])]

def normal(x, u, s):
    import math
    return math.exp(-((x-u)**2)/(2*(s**2)))/(s*((2*math.pi)**.5))


class Food(object):
    def __init__(self, ndb_no=None, avg=True, weight=100, nutr_detail=None):
        self.nutrients = None
        self.name = None
        self.name_en = None
        self.group = None
        self.radio_omega_raw = 0
        self.nutr_avg = None
        self.ndb_no = ndb_no
        self.omegas = None
        self.weight = weight
        self.nutr_detail = nutr_detail
        if self.ndb_no is not None:
            self.get(ndb_no, avg=avg)

    def name_limit(self):
        if len(self.name) > 20:
            return "%s..." % (self.name[:20],)
        return self.name

    def portion_value(self, v):
        return (v * self.weight) / 100.0

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
        #Energy#ENERC_KJ, 'Vitamin A, IU', 'Folate, food', 'Folate, total', Folic acid
        e_data = exclude_data(records, exclude=set(["268", "318", "432", "417", "431"]))
        food = self.get_food(self.ndb_no)
        self.name = food[0][0]
        self.name_en = food[0][3]
        self.group = {"name": food[0][1], "id": food[0][2]}
        features, omegas = self.subs_omegas([(nutr_no, nut, self.portion_value(v), u) 
                            for nutr_no, nut, v, u in e_data])
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

    def __add__(self, other):
        if isinstance(other, Food):
            if self.ndb_no == other.ndb_no:
                nutrients = [(x[0], x[1], x[2]+y[2], x[3]) for x, y in zip(self.nutrients, other.nutrients)]
                omegas = [(x[0], x[1], x[2]+y[2], x[3]) for x, y in zip(self.omegas, other.omegas)]
                food = Food(ndb_no=None, avg=False, weight=self.weight+other.weight)
                food.ndb_no = self.ndb_no
                food.radio_omega_raw = self.radio_omega_raw
                food.omegas = omegas
                food.nutrients = nutrients
                return food
            else:
                raise Exception("Only I can add food with the same ndb_no")
        else:
            return self
        
    def __radd__(self, other):
        return self.__add__(other)

    @classmethod
    def subs_omegas(self, features):
        """ sustituye los terminos X:X por el nombre omega Y"""
        pattern = r"(?P<molecula>\d{2}:\d{1})"
        pattern_base = r"(?P<tipo>n\-\d{1})"
        s_molecula = re.compile(pattern)
        s_tipo_molecula = re.compile(pattern_base)
        n_features = []
        omegas = {}
        totals_base = {}
        for nutr_no, nut, v, u in features:
            molecula = s_molecula.search(nut)
            if molecula:
                molecula_txt = molecula.groupdict()["molecula"]
                tipo_molecula = s_tipo_molecula.search(nut)
                
                if tipo_molecula:
                    tipo_molecula_txt = tipo_molecula.groupdict()["tipo"]
                else:
                    tipo_molecula_txt = None

                #print(molecula_txt, nut, v)
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
                elif nut in OMEGAS_DOMINAT["omega 9"]:
                    omega = "omega 9"
                elif molecula_txt in OMEGAS["omega 7"]:
                    omega = "omega 7"
                else:
                    omega = None
            
                if omega is not None:
                    if totals_base.get(molecula_txt, "") != omega:
                        omegas.setdefault(omega, [omega.replace(" ", ""), 0, u])
                        omegas[omega][1] += v
                        totals_base[molecula_txt] = omega
                else:
                    n_features.append((nutr_no, nut, v, u))
            else:
                n_features.append((nutr_no, nut, v, u))

        return n_features, omegas

    def exclude_features(self, all_nutr):
        """nutr_no, nut, float(v), u in self.nutrients"""
        base = set([n[0] for n in self.nutrients])
        return [n for n in all_nutr if n[0] in base]

    @classmethod
    def init_features(self, records):
        features = OrderedDict()
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
        sumxy = sum((x*y for x, y in zip(v1, v2)))
        sumxx = sum((x*x for x in v1))
        sumyy = sum((y*y for y in v2))
        return sumxy / (sumxx * sumyy)**.5

    def min_distance(self, vector_base, vectors, top=15):
        distance = lambda x, y: sum((x_i - y_i)**2 for x_i, y_i in zip(x, y))**.5
        #distance = self. cosine_similarity
        distances = ((vector[0], distance(vector_base[1], vector[1])) 
                        for vector in vectors if vector_base[0] != vector[0])
        return heapq.nsmallest(top, distances, key=lambda x: x[1])
        #return heapq.nlargest(15, distances, key=lambda x: x[1])

    @classmethod
    def create_vector_fields_nutr(self, exclude_nutr_l=None):
        if exclude_nutr_l is None:
            exclude_nutr_l = EXCLUDE_NUTR.keys()
        features = nutr_features()
        fields, omegas = self.subs_omegas([(e[0], e[1], 0, None) for e in features])
        fields = fields + [(v[0], None, 0, None) for _, v in omegas.items()]
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
            matrix = MatrixNutr(name=PREPROCESSED_DATA_DIR + 'matrix.csv')
        fields = self.create_vector_fields_nutr()
        vector_base = self.vector_features(fields, self.nutrients)
        foods = self.min_distance((self.ndb_no, vector_base.values()), matrix.rows, top=top)
        if raw:
            return ((ndb_no, v) for ndb_no, v in foods)
        return ((ndb_no, self.get_food(ndb_no), v) for ndb_no, v in foods)

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
        return ((n[0], n[1], n[2], n[3], 
                int((n[2] > self.nutr_avg[n[0]][1]) and n[4]), 
                int((n[2] > self.nutr_avg[n[0]][1]) and not n[4]))
            for n in nutrients)

    def mark_nutrients(self):
        return mark_caution_nutr(self.nutrients)

    def caution_good_nutr_avg(self):
        good = len(list(filter(lambda x: x[5], self.mark_caution_good_nutrients())))
        bad = len(list(filter(lambda x: x[4], self.mark_caution_good_nutrients())))
        return {"total": len(self.nutrients),
            "good": good,
            "bad": bad}

    def score(self, perfil, data=True, features=None):
        recipe = self.food2recipe(perfil, data=data, features=features)
        return recipe.score

    def score_by_complete(self, perfil):
        recipe = self.food2recipe(perfil)
        return recipe.score_by_complete()

    def food2recipe(self, perfil, data=True, features=None):
        light_format = {
            "perfil": perfil,
            "foods": {self.ndb_no:self.weight},
            "name": ""   
        }
        return Recipe.from_light_format(light_format, data=data, features=features)

    def top_nutrients(self):
        units_scale = {"g": 1, "mg": 1000, "µg": 1000000000}
        totals = []
        for nutr_no, nutrdesc, total, units in self.nutrients:
            val = units_scale.get(units, 0)
            if val != 0:
                totals.append((float(total / val), nutrdesc, 'g'))

        totals.sort(reverse=True, key=lambda x:x[0])
        maximum = sum([v for v, _, _ in totals])
        return [(e[0] * 100 / maximum, e[1]) for e in totals]

    def avg_nutrients_best(self):
        diff_nutr = [(nutr_no, nutrdesc, v - self.nutr_avg[nutr_no][1], u) 
            for nutr_no, nutrdesc, v, u in self.nutrients if nutr_no != "255"]
        return sorted(diff_nutr, key=lambda x: x[2], reverse=True)

    def top_nutrients_avg(self):
        result = self.avg_nutrients_best()
        return filter(lambda x:x[2] > 0, result)

    def top_nutrients_detail_avg(self, limit=15):
        return [(nutr_no, nutrdesc, self.nutr_detail.get(nutr_no, ""), mount, u)
                for nutr_no, nutrdesc, mount, u in self.top_nutrients_avg()][:limit]

    def img_obj(self):
        from nutrientes.models import FoodDescImg
        try:
            return FoodDescImg.objects.get(ndb_no_t=self.ndb_no)
        except FoodDescImg.DoesNotExist:
            return None 

    def is_weight_nutrients(self, weights):
        MIN_PORCENTAJE_EXIST = .5
        WEIGHT_AVG_NUTR = .1
        nutr_weight = []
        nutrients = {nutr_no: v for nutr_no, _, v, _ in self.nutrients}
        weights_tmp_good = [(nutr_no, weight) for nutr_no, weight in weights.items() if weight <= 1]

        for w_nutr_no, _ in weights_tmp_good:
            val_min = self.nutr_avg.get(w_nutr_no, [0,0])[1] * WEIGHT_AVG_NUTR
            v = nutrients.get(w_nutr_no, -1)
            if val_min <= v:
                nutr_weight.append((w_nutr_no, 
                    self.nutr_avg.get(w_nutr_no, "")[0], 
                    self.nutr_detail.get(w_nutr_no, "")))

        self.weights_nutrients_approved = nutr_weight
        return (int(len(weights_tmp_good) * MIN_PORCENTAJE_EXIST)) <= len(nutr_weight)
             

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

def create_matrix(ndb_nos, exclude_nutr=None, only=None, weight=100):
    if only is not None:
        fields = only
    else:
        fields = Food.create_vector_fields_nutr(exclude_nutr_l=exclude_nutr)

    rows = [(ndb_no, Food.vector_features(fields, Food(ndb_no, weight=weight).nutrients).items())
                for ndb_no in ndb_nos]
    matrix = MatrixNutr(rows=rows)
    return matrix

def create_order_matrix():
    _, cursor = conection()
    nutr = Food.get_matrix(PREPROCESSED_DATA_DIR + "nutavg.p")
    # hasheamos las llaves para mantener el orden
    nutr_avg = {nutr_no:(avg, caution) for nutr_no, nutr_desc, avg, _, caution in mark_caution_nutr(nutr)}

    querys = []
    for nutr_no, (avg, caution) in nutr_avg.items():
        query = query_build(nutr_no, None)
        cursor.execute(query)
        querys.append((nutr_no, caution, avg, cursor.fetchall()))

    rank = Rank(querys)
    order = [food["attr"][0] for _, food in rank.order()]
    return order

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
    units_scale = {"g": 1, "mg": 1000, "µg": 1000000000}
    totals = []
    for nutrdesc, avg, units in cursor.fetchall():
        val = units_scale.get(units, 0)
        if val != 0:
            totals.append((nutrdesc, float(avg / val)))
    return sorted(totals, key=lambda x: x[1], reverse=True)

class MostSimilarFood(object):
    def __init__(self, ndb_no, category_to_search, exclude_nutr=None):
        self.food_base = Food(ndb_no, avg=False)
        self.category_to_search = category_to_search
        if exclude_nutr is None:
            exclude_nutr = {
                "601": "Cholesterol",
                "307": "Sodium, Na",
                "607": "4:0",
                "609": "8:0",
                "608": "6:0",
            }
            exclude_nutr.update(EXCLUDE_NUTR)

        vector_base = self.food_base.vector_features(
            self.food_base.create_vector_fields_nutr(exclude_nutr_l=exclude_nutr), 
            self.food_base.nutrients)
        self.vector_base_items = [(k, v) for k, v in vector_base.items() if v > 0]
        ndb_nos = (ndb_no for ndb_no, _ in alimentos_category(category=category_to_search, limit="limit 9000"))
        self.matrix = create_matrix(ndb_nos, only=[k for k, _ in self.vector_base_items], weight=25)
        self.matrix_dict = self.matrix.to_dict(nutr_no=True)
        self.max_total_food = 8
        self.total_nutr = len(self.vector_base_items)


    def search_steps(self, base_size, low_grow, data, extra_data=[], min_diff=10):
        down_vectors = []
        every = 5
        count = 0
        for foods in data:
            foods_extra = foods+extra_data
            rows = [self.matrix_dict[ndb_no] for ndb_no, _ in foods_extra]
            sum_nutr = [(sublist[0][0], sum(e[1] for e in sublist)) for sublist in zip(*rows)]
            diff = [(b[0], t[1]-b[1]) for t, b in zip(sum_nutr, self.vector_base_items)]
            up_diff = list(filter(lambda x: x[1] >= 0, diff))
            low_diff = list(filter(lambda x: x[1] < 0, diff))
            if len(low_diff) <= min_diff:
                return EvalSimilarFood(foods_extra, low_diff, sum_nutr, self.total_nutr)

            down_vectors.append(low_diff)
            if count == every:
                null_grow = self.grown(down_vectors)
                down_vectors = []
                count = 0
                low_grow.append(null_grow)
            count += 1
        return None

    def grown(self, vectors):
        null_grow = set([])
        for sublist in zip(*vectors):
            if sublist[0][1] != 0:
                grow_ = abs((((sublist[-1][1] / sublist[0][1])**(1./len(sublist))) - 1) * 100)
                #print grow_, sublist[0][1], sublist[-1][1]
                if grow_ <= 1: #1%
                    null_grow.add(sublist[0][0])

        return null_grow

    def random_select(self, size):
        import random
        indexes = set([])
        #keys = self.matrix.keys()
        for i in range(100):
            blocks = []
            while len(blocks) < size:
                #i = random.randint(0, len(keys) - 1)
                i = random.randint(0, len(self.matrix.rows) - 1)
                if not i in indexes:
                    indexes.add(i)
                    #blocks.append((keys[i], None))
                    blocks.append((self.matrix.rows[i][0], None))
            indexes = set([])
            yield blocks

    def random(self, extra_food=[], min_amount_food=2, max_amount_food=5, min_diff=10):
        counting = {}
        for food_size in range(min_amount_food, max_amount_food):
            data = self.random_select(food_size)
            low = []
            foods = self.search_steps(food_size, low, data, extra_data=extra_food, min_diff=min_diff)
            for s in low:
                for nutr_no in s:
                    counting[nutr_no] = counting.get(nutr_no, 0) + 1
            if foods is not None:
                return foods, True
        return sorted(counting.items(), key=lambda x: x[1], reverse=True), False

    def search(self):
        _, cursor = conection()
        step_best = 1
        count = {}
        nutrs_no = {}
        max_amount_food = 5
        min_amount_food = 2
        min_diff = 10
        results_best = []
        best_extra_food = []
        while True:
            results, ok = self.random(
                extra_food=best_extra_food[:step_best], 
                min_amount_food=min_amount_food, 
                max_amount_food=max_amount_food,
                min_diff=min_diff)

            if ok:
                results_best.append(results)
                min_diff -= 1
                step_best = 1
                continue
            elif not ok and max_amount_food + len(best_extra_food[:step_best]) >= self.max_total_food + 1:
                break
            elif step_best > 10:
                max_amount_food += 1
                step_best = 1
            else:
                step_best += 1

            new = False
            for nutr_no, _ in results:
                if not nutr_no in nutrs_no:
                    nutrs_no.setdefault(nutr_no, set([]))
                    new = True
                    query = query_build(nutr_no, self.category_to_search, order_by="DESC")
                    cursor.execute(query)
                    for r in cursor.fetchall()[:10]:
                        count[r[0]] = count.get(r[0], 0) + 1
                        nutrs_no[nutr_no].add(r[0]) 
            if new:
                best_extra_food = sorted(count.items(), key=lambda x: x[1], reverse=True)

        return results_best

class EvalSimilarFood(object):
    def __init__(self, result, low_nutr, sum_nutr, total_nutr):
        self.result = self.sum_equals(result)
        self.low_nutr = low_nutr
        self.sum_nutr = sum_nutr
        if total_nutr > 0:
            self.total = 100 - (len(low_nutr) * 100 / total_nutr)
        else:
            self.total = 0
        self.transform_data = None

    def sum_equals(self, result):
        base = {}
        for ndb_no, _ in result:
            base.setdefault(ndb_no, 0)
            base[ndb_no] += 25
        return base.items()

    def ids2name(self, similar_food):
        ndb_nos = [ndb_no for ndb_no, _ in self.result]
        not_ndb_not_found = [ndb_no for ndb_no, _ in self.low_nutr]
        o_foods = [similar_food.matrix_dict[ndb_no] for ndb_no in ndb_nos]
        nutrs_ids = nutr_features_ids(similar_food.matrix.column)
        nutrs_ids = {k: v for k, v in nutrs_ids}
        total_nutrients = [(nutrs_ids[nutr_no], total) for nutr_no, total in self.sum_nutr]
        nutrs_ids_base = nutr_features_ids([k for k, _ in similar_food.vector_base_items])
        nutrs_ids_base = {k: v for k, v in nutrs_ids_base}
        food_base_nutrients = [(nutrs_ids_base[k], v) for k, v in similar_food.vector_base_items]
        food_not_found_nutr = [nutrs_ids[e] for e in not_ndb_not_found]
        foods = []
        ndb_nos_name = [(data[1][0], data[1][1], data[0][1]) for data in zip(self.result, get_many_food(ndb_nos))]
        for ndb_no, name, _ in ndb_nos_name:
            for nutr_no, v in similar_food.matrix_dict[ndb_no]:
                foods.append((name, nutrs_ids[nutr_no], v))

        self.transform_data = {
            "food_base_nutrients": food_base_nutrients,
            "foods": foods,
            "total_nutrients": total_nutrients,
            "food_not_found_nutr": ", ".join(food_not_found_nutr),
            "o_foods": ndb_nos_name,
            "total_porcentaje": self.total
        }
        return self.transform_data

class MatrixNutr(object):
    def __init__(self, name=None, rows=None):
        if rows is not None:
            self.convert_rows(rows)
        else:
            self.get_matrix(name)

    def convert_rows(self, items):
        if len(items) > 0:
            column = [nutr_no for nutr_no, _ in items[0][1]]
            rows = [(ndb_no, [v for _, v in vector]) for ndb_no, vector in items]
        else:
            column = []
            rows = []
        self.rows = rows
        self.column = column

    def get_matrix(self, name):
        import csv
        with open(name, 'rb') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
            for row in spamreader:
                self.column = row
                break
            self.rows = [(row[0], map(float, row[1:])) for row in spamreader]

    def save_matrix(self, name):
        import csv
        with open(name, 'wb') as csvfile:
            spamwriter = csv.writer(csvfile, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
            spamwriter.writerow(self.column)
            for nutr_no, row in self.rows:
                spamwriter.writerow([nutr_no]+row)

    def get_row(self, i):
        row = self.rows[i]
        return (row[0], zip(self.column, row[1]))

    def to_dict(self, nutr_no=False):
        if nutr_no is True:
            return {ndb_no: list(zip(self.column, vector)) for ndb_no, vector in self.rows}
        return {ndb_no: vector for ndb_no, vector in self.rows}

class NodeNeighbors(object):
    def __init__(self, category):
        self.nodes = {}
        self.category = category
        
    def add(self, key, best):
        self.nodes[key] = best

    def sequence(self, k, items=10):
        data = []
        nk = k
        category = self.category[nk]
        while len(data) < items:
            ndb_no = self.nodes[nk]
            if ndb_no is None:
                return data
            if self.category[ndb_no] == category:
                data.append(ndb_no)
            nk = ndb_no
        return data

    def get(self, k):
        return self.nodes[k]

class OrderSimilarity(object):
    def __init__(self, data_list):
        self.nodes = self.list2order(data_list)

    def list2order(self, data_list):
        nodes = NodeNeighbors({e["ndb_no"]: e["category"] for e in data_list})
        nodes.add(data_list[0]["ndb_no"], None)
        for x1, base in zip(data_list, data_list[1:]):
            nodes.add(base["ndb_no"], x1["ndb_no"])
        nodes.add(data_list[-1]["ndb_no"], data_list[-2]["ndb_no"])
        return nodes

    def get_top(self, k, level=10):
        return self.nodes.sequence(k, items=level).pop()

def boost_food(ndb_no):
    import csv
    with open(PREPROCESSED_DATA_DIR+"order_matrix.csv", 'rb') as csvfile:
        data_list = []
        csvreader = csv.reader(csvfile, delimiter=',',
                        quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in csvreader:
            data_list.append({"ndb_no": row[0], "category": row[1]})

    order = OrderSimilarity(data_list)
    food = Food(order.get_top(ndb_no, level=10))
    return food

def intake(edad, genero, unidad_edad, rnv_type):
    conn, cursor = conection()
    edad_range_c = get_range(int(edad), unidad_edad, int(rnv_type))
    query = """SELECT nutr_def.nutr_no, nutrdesc, units, value, type, edad_range
                FROM nutr_def, nutr_intake 
                WHERE nutr_def.nutr_no=nutr_intake.nutr_no
                AND unidad_edad=%s
                AND genero=%s
                AND rnv_type=%s
                AND edad_range=%s"""

    nutrs = {}
    for edad_range in edad_range_c:
        cursor.execute(query, [unidad_edad, genero, rnv_type, edad_range])
        for nutr_no, nutrdesc, units, value, label, edad_range in cursor.fetchall():
            if not nutrdesc in nutrs:
                nutrs[nutrdesc] = NutrIntake(nutr_no, nutrdesc)
                nutrs[nutrdesc].units = units
            nutrs[nutrdesc].add_value(float(value), label)
    conn.close()
    return nutrs

def get_range(edad, unidad_edad, rnv_type=1):
    if unidad_edad == "meses":
        edad_range_list = ["0-6", "7-12"]
    else:
        if rnv_type == 1:
            edad_range_list = ["1-3", "4-8", "9-13", "14-18", "19-30", "19-50", "31-50", "51-70", "51-150", "71-150"]
        else:
            edad_range_list = ["1-150"]

    candidates = []
    for edad_range in edad_range_list:
        min_year, max_year = edad_range.split("-")
        min_year = int(min_year)
        if max_year == '':            
            max_year = 200
        else:
            max_year = int(max_year)
        if min_year <= edad <= max_year:
            candidates.append(edad_range)
    return candidates

class NutrIntake(object):
    def __init__(self, nutr_no, nutrdesc):
        self.nutr_no = nutr_no
        self.nutrdesc = nutrdesc
        self.labels = {"AI": "Ingesta adecuada", 
                        "RDA": "Recomendada", 
                        "UL": "Máxima ingesta tolerable"}
        self.values = {label: None for label in self.labels}
        self.units = None

    def add_value(self, value, label):
        self.values[label] = value

    def raw(self):
        return [(self.nutrdesc, value, self.units, self.labels[label])
                for label, value in self.values.items() if value != None]

    def get_value(self):
        AI = self.values.get("AI", None)
        RDA = self.values.get("RDA", None)
        UL = self.values.get("UL", None)
        if AI is not None:
            return AI
        elif RDA is not None:
            return RDA
        elif UL is not None:
            return UL
            
    def resumen(self, other_value):
        data = {}
        for label, ref_value in self.values.items():
            if (label == "AI" or label == "RDA") and ref_value is not None:
                if other_value < ref_value:
                    data[self.labels[label]] = other_value * 100 / ref_value
            elif label == "UL" and ref_value is not None:
                if ref_value < other_value:
                    data[self.labels[label]] = ref_value * 100 / other_value
        return data
    
    def all_intake(self, other_value):
        return {self.labels[label]: other_value * 100 / ref_value 
                for label, ref_value in self.values.items() if ref_value is not None}
   
    def score(self, resumen):
        if len(resumen) == 0:
            return 100
        else:
            AI = resumen.get("Ingesta adecuada", None)
            RDA = resumen.get("Recomendada", None)
            UL = resumen.get("Máxima ingesta tolerable", None)
            if AI is not None:
                return AI
            elif RDA is not None:
                return RDA
            elif UL is not None:
                return UL - 100
            else:
                return 100

    def score_by_type(self, resumen):
        AI = resumen.get(self.labels["AI"], None)
        RDA = resumen.get(self.labels["RDA"], None)
        UL = resumen.get(self.labels["UL"], None)
        if UL is None or UL < 100:
            if RDA is not None:
                return RDA, "RDA"
            elif AI is not None:
                return AI, "AI"  
        elif UL is not None:
            return UL, "UL"
        else:
            return 0, ""

def magnitude(number):
    try:
        left, right = str(float(number)).split(".")
    except ValueError:
        return -int(str(float(number)).split("-").pop())
    if left == '0':
        for i, digit in enumerate(right, 1):
            if digit != '0':
                return -i
        return 0
    else:
        return len(left) - 1

def recipes_list(max_number, perfil, ordered="score", visible=True):
    from collections import defaultdict
    _, cursor = conection()
    query = """SELECT recipe.id, recipe.name, recipe_ingredient.ndb_no, recipe_ingredient.weight
                FROM recipe, recipe_ingredient 
                WHERE recipe.id=recipe_ingredient.recipe
                AND recipe.visible=%s"""
    cursor.execute(query, [visible])
    recipes = defaultdict(dict)
    for recipe_id, name, ndb_no, weight in cursor.fetchall():
        recipes[u"{}-{}".format(recipe_id, name)][ndb_no] = float(weight)

    recipes_l = []
    perfil_intake = intake(
        perfil["edad"], 
        perfil["genero"], 
        perfil["unidad_edad"],#.encode("utf8", "replace"), 
        perfil["rnv_type"])
    features = Recipe.create_generic_features()
    for recipe_id_name, foods in recipes.items():
        recipe_id, name = recipe_id_name.split("-")
        light_format = {
            "perfil": perfil,
            "foods": foods,
            "name": name
        }
        
        recipe = Recipe.from_light_format(light_format, perfil_intake=perfil_intake, features=features)
        recipe.id = recipe_id
        recipes_l.append(recipe)

    if ordered == "score":
        return sorted(recipes_l, key=lambda x:x.score, reverse=True)
    else:
        return sorted(recipes_l, key=lambda x:x.score_best(), reverse=True)


def recipes_list_users(max_number):
    from collections import defaultdict
    _, cursor = conection()
    query = """SELECT recipe.id, recipe.name, recipe_ingredient.ndb_no,
                    recipe_ingredient.weight, recipe_best_perfil.perfil, recipe.author
                FROM recipe, recipe_ingredient, recipe_best_perfil
                WHERE recipe.id=recipe_ingredient.recipe
                AND recipe.visible=%s
                AND recipe_best_perfil.recipe=recipe.id"""
    cursor.execute(query, [False])
    authors_recipes = defaultdict(dict)
    recipes_l = {}
    for recipe_id, name, ndb_no, weight, perfil, author in cursor.fetchall():
        try:
            authors_recipes[author]["{}_{}_{}".format(recipe_id, name, perfil.encode("utf8", "replace"))][ndb_no] = float(weight)
        except KeyError:
            authors_recipes[author]["{}_{}_{}".format(recipe_id, name, perfil.encode("utf8", "replace"))] = {ndb_no:float(weight)}
            recipes_l[author] = {"total": {"score": 0, "kcal": 0, "weight": 0}, "recipes": []}

    cache = {}
    features = Recipe.create_generic_features()
    for author, recipes in authors_recipes.items():
        for k, foods_ndb_no in recipes.items():
            reciple_id, name, recipe_txt = k.split("_")
            if k not in cache:
                edad, genero, unidad_edad, rnv_type = recipe_txt.split("-")
                perfil_intake = intake(
                    edad, 
                    genero, 
                    unidad_edad, 
                    rnv_type)
                cache[k] = perfil_intake
            else:
                perfil_intake = cache[k]
        
            light_format = {
               "perfil": {"edad": None, "unidad_edad": "", "genero": None, "rnv_type": None},
                "foods": foods_ndb_no,
                "name": name
            }
            
            recipe = Recipe.from_light_format(light_format, perfil_intake=perfil_intake, features=features)
            recipe.id = recipe_id
            recipes_l[author]["total"]["score"] = recipes_l[author]["total"]["score"] + recipe.score
            recipes_l[author]["total"]["kcal"] = recipes_l[author]["total"]["kcal"] + recipe.energy()[0]
            recipes_l[author]["total"]["weight"] = recipes_l[author]["total"]["weight"] + recipe.weight
            recipes_l[author]["recipes"].append(recipe)
    return sorted(recipes_l.items(), key=lambda x:x[1]["total"], reverse=True)


class MenuRecipe(object):
    def __init__(self, recipes_ids, perfil):
        self.recipes = self.ids2recipes(recipes_ids, perfil)
        self.merged_recipes = Recipe.merge(self.recipes)

    @classmethod
    def ids2recipes(self, recipes_ids, perfil, data=True, features=None):
        from collections import defaultdict
        _, cursor = conection()
        ids = ["%s" for e in recipes_ids]
        query = """SELECT recipe.id, recipe.name, recipe_ingredient.ndb_no, recipe_ingredient.weight
                    FROM recipe, recipe_ingredient 
                    WHERE recipe.id=recipe_ingredient.recipe
                    AND recipe.id IN ({ids})""".format(ids=",".join(ids))
        cursor.execute(query, recipes_ids)
        duplicates = {}
        for recipe_id in recipes_ids:
            duplicates.setdefault(int(recipe_id), 0)
            duplicates[int(recipe_id)] += 1
        recipes = defaultdict(dict)
        for recipe_id, name, ndb_no, weight in cursor.fetchall():
            recipes["{}-{}".format(recipe_id, name)][ndb_no] = duplicates[recipe_id] * float(weight)

        intake_recipes = []
        perfil_intake = intake(
            perfil["edad"], 
            perfil["genero"], 
            perfil["unidad_edad"].encode("utf8", "replace"),
            perfil["rnv_type"])
        for recipe_id_name, foods in recipes.items():
            _, name = recipe_id_name.split("-")
            light_format = {
                "perfil": perfil,
                "foods": foods,
                "name": name   
            }
            intake_recipes.append(Recipe.from_light_format(
                light_format, perfil_intake=perfil_intake, data=data, features=features))
        return intake_recipes

    def best(self):
        rank = best_of_query([nutr_no for nutr_no, _, _ in self.insuficient_intake()], None)
        return rank.order(limit=5)

    def score(self):
        return self.merged_recipes.score

    def insuficient_intake(self):
        return self.merged_recipes.insuficient_intake

    def suficient_intake(self):
        return self.merged_recipes.suficient_intake

    def resume_intake(self):
        return self.merged_recipes.resume_intake()

    def energy(self):
        return self.merged_recipes.energy()

    def weight(self):
        return self.merged_recipes.weight

    def radio_omega(self):
        return self.merged_recipes.radio_omega

class Recipe(object):
    def __init__(self, edad, genero, unidad_edad, rnv_type, blank=False, perfil_intake=None, name=None, features=None):
        if not blank:
            self.perfil = self.build_perfil(edad, genero, unidad_edad, rnv_type)
            if perfil_intake is None:
                self.perfil_intake = self.perfil_intake()
            else:
                self.perfil_intake = perfil_intake
        else:
            self.perfil = None
            self.perfil_intake = None
        self.foods = None
        self.weight = None
        self.radio_omega = None
        self.total_nutr_names = None
        self.name = name
        self.score = None
        self.insuficient_intake = None
        self.suficient_intake = None
        self.set_nutr_id("nutrdesc")
        if features is None:
            self.features = self.create_generic_features()
        else:
            self.features = features

    def energy(self):
        energy = "Energy" if self.nutr_id_key == "nutrdesc" else "208"
        return self.total_nutr_names.get(energy, 0)

    def set_nutr_id(self, type_id):
        self.nutr_id_key = "nutr_no" if type_id == "id" else "nutrdesc"

    def from_formset(self, formset):
        self.foods = {form.food.ndb_no: form.food for form in formset}
        self.total_nutr_data()

    def build_perfil(self, edad, genero, unidad_edad, rnv_type):
        return {"edad": edad, "genero": genero, "unidad_edad": unidad_edad, "rnv_type": rnv_type}

    def vector_features(self):
        return [food.vector_features(
            self.features,
            food.nutrients).items() for food in self.foods.values()]

    def set_features(self, features):
        self.features = features

    @classmethod
    def create_generic_features(self):
        return Food.create_vector_fields_nutr(exclude_nutr_l=set([]))

    def calc_weight(self, force=False):
        if self.weight is None or force:
            if self.foods is not None:
                self.weight = sum(food.weight for food in self.foods.values())
        return self.weight

    def calc_radio_omega(self):
        try:
            self.radio_omega = round(
                self.total_nutr_names.get("omega 6", [0])[0] / self.total_nutr_names.get("omega 3", [0])[0], 2)
        except ZeroDivisionError:
            self.radio_omega = 0

    def total_nutr_data(self, vector_features_opt=None):
        if vector_features_opt is None:
            vectors_features = self.vector_features()
        else:
            vectors_features = vector_features_opt

        total_food = [(v[0][0], sum(e[1] for e in v)) for v in zip(*vectors_features)]
        total_food = [(nutr_no, total) for nutr_no, total in total_food if total > 0]
        if self.nutr_id_key == "nutrdesc":
            total_nutr_names = nutr_features_ids([nutr_no for nutr_no, _ in total_food])
            total_nutr_units = nutr_units_ids([nutr_no for nutr_no, _ in total_food])
            total_nutr_names = {name[1]: (total[1], units[1]) 
                for name, total, units in zip(total_nutr_names, total_food, total_nutr_units)}
        else:
            total_nutr_names = {nutr_no: (total, None) for nutr_no, total in total_food}

        self.total_nutr_names = total_nutr_names
        self.calc_weight()
        self.calc_score()
        self.calc_radio_omega()

    def foods_intake(self):
        pass

    def score_resume(self):
        insuficient_intake = []
        suficient_intake = []
        total_nutr_score = 0
        for nutr_intake in self.perfil_intake.values():
            nutr_id = getattr(nutr_intake, self.nutr_id_key)
            resumen = nutr_intake.resumen(self.total_nutr_names.get(nutr_id, [0])[0])
            nutr_score = nutr_intake.score(resumen)
            total_nutr_score += nutr_score
            if len(resumen) > 0:
                insuficient_intake.append((nutr_intake.nutr_no, nutr_intake.nutrdesc, nutr_score))
            else:
                suficient_intake.append((nutr_intake.nutr_no, nutr_intake.nutrdesc, nutr_score))
        score = round(total_nutr_score / len(self.perfil_intake), 2)
        return score, insuficient_intake, suficient_intake

    def score_by_nutr(self, limit=5):
        resume_intake = []
        for nutr_intake in self.perfil_intake.values():
            nutr_id = getattr(nutr_intake, self.nutr_id_key)
            intake = nutr_intake.all_intake(self.total_nutr_names.get(nutr_id, [0])[0])
            score, type_intake = nutr_intake.score_by_type(intake)
            resume_intake.append((nutr_intake.nutrdesc, score, type_intake))
        return heapq.nlargest(limit, resume_intake, key=lambda x: x[1])
        
    def score_by_complete(self):
        total = len(self.insuficient_intake) + len(self.suficient_intake)
        ins_intake = [v for _, _, v in self.insuficient_intake if v > 0]
        sf_intake = [v for _, _, v in self.suficient_intake]
        intake = ins_intake + sf_intake
        try:
            avg = sum(intake) / len(intake)
            spectrum = len(intake) / float(total)
            variance = sum(((v - avg)**2 for v in intake)) / len(intake) 
        except ZeroDivisionError:
            spectrum = 0
            variance = 0
        
        return spectrum, variance

    def score_best(self):
        spectrum, variance = self.score_by_complete()
        #(100, 1, 0)
        variance = variance if variance <= 1000 else 1000
        return round(100 - ((100 - self.score + ((1 - spectrum) * 100) + (variance / 100.)) / 3.), 2)

    def calc_score(self):
        if self.score is None:
            self.score, self.insuficient_intake, self.suficient_intake = self.score_resume()
        return self.score

    def calc_insuficient_intake(self):
        if self.insuficient_intake is None:
            self.score, self.insuficient_intake, self.suficient_intake = self.score_resume()
        return self.insuficient_intake

    def principals_nutrients(self, percentage=False):
        units_scale = {"g": 1, "mg": 1000, "µg": 1000000000}
        totals = []
        for nutrdesc, (total, units) in self.total_nutr_names.items():
            val = units_scale.get(units, 0)
            if val != 0:
                totals.append((float(total / val), nutrdesc))

        totals.sort(reverse=True, key=lambda x:x[0])
        otros_total = (sum([v for v, _ in totals[9:]]), "Vitaminas, Minerales, Aminoacidos, Acidos grasos, etc.")
        base = totals[:9]
        base.append(otros_total)
        if percentage:
            maximum = sum([v for v, _ in base])
            return [(round(e[0] * 100 / maximum, 2), e[1]) for e in base]
        else:
            return base

    def principals_nutrients_percentage(self):
        return self.principals_nutrients(percentage=True)

    def resume_intake(self):
        return self.insuficient_intake + self.suficient_intake

    def resume_intake_raw(self):
        for nutrdesc, nutr_intake in self.perfil_intake.items():
            value, units = self.total_nutr_names.get(nutrdesc, [0, 'g'])
            yield (nutrdesc, value, units)

    def perfil_intake(self):
        return intake(
            self.perfil["edad"], 
            self.perfil["genero"], 
            self.perfil["unidad_edad"],
            self.perfil["rnv_type"])

    def light_format(self):
        return {"perfil": self.perfil,
                "foods": {food.ndb_no: food.weight for food in self.foods.values()},
                "score": self.calc_score(),
                "name": self.name}

    def food2name(self):
        return {food.ndb_no: food.name for food in self.foods.values()}

    def save2db(self, name, author):
        conn, cursor = conection()
        query = """SELECT id FROM recipe WHERE name=%s AND author=%s"""
        cursor.execute(query, [name, author])
        recipe_id = cursor.fetchone()
        if recipe_id:
            for food in self.foods.values():
                query = """UPDATE recipe_ingredient SET weight=%s WHERE recipe=%s AND ndb_no=%s"""
                cursor.execute(query, [food.weight, recipe_id[0], food.ndb_no])
        else:
            query = """INSERT INTO recipe (name, author, visible) VALUES (%s, %s, false) RETURNING id"""
            cursor.execute(query, [name, author])
            recipe_id = cursor.fetchone()[0]
            for food in self.foods.values():
                query = """INSERT INTO recipe_ingredient 
                        (recipe, ndb_no, weight) 
                        VALUES (%s, %s, %s)"""
                cursor.execute(query, [recipe_id, food.ndb_no, food.weight])
        conn.commit()
        conn.close()
        return recipe_id

    def save2bestperfil(self, recipe_id, perfil, author):
        conn, cursor = conection()
        query = """SELECT recipe_best_perfil.id 
            FROM recipe, recipe_best_perfil 
            WHERE recipe.id=recipe_best_perfil.recipe
            AND recipe=%s 
            AND author=%s"""
        cursor.execute(query, [recipe_id, author])
        recipe_best_id = cursor.fetchone()
        perfil_str = u"{edad}-{genero}-{unidad_edad}-{rnv_type}".format(**perfil)
        if recipe_best_id:
            pass
        else:
            query = """INSERT INTO recipe_best_perfil (recipe, perfil) VALUES (%s, %s) RETURNING id"""
            cursor.execute(query, [recipe_id, perfil_str])
            recipe_best_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        return recipe_best_id

    @classmethod
    def from_light_format(self, intake_light_format, perfil_intake=None, data=True, features=None):
        perfil = intake_light_format["perfil"]
        foods = intake_light_format["foods"]
        recipe = Recipe(
            perfil["edad"], 
            perfil["genero"], 
            perfil["unidad_edad"].encode("utf8", "replace"),
            perfil.get("rnv_type", 1),
            perfil_intake=perfil_intake,
            name=intake_light_format.get("name", None),
            features=features)
        recipe.foods = {ndb_no: Food(ndb_no, weight=weight, avg=False)
            for ndb_no, weight in foods.items()}
        if data:
            recipe.total_nutr_data()
        return recipe

    @classmethod
    def from_vector_format(self, intake_light_format, perfil_intake, features, vector_features):
        perfil = intake_light_format["perfil"]
        recipe = Recipe(
            perfil["edad"], 
            perfil["genero"], 
            perfil["unidad_edad"].encode("utf8", "replace"),
            perfil.get("rnv_type", 1),
            perfil_intake=perfil_intake,
            name=intake_light_format.get("name", None),
            features=features)
        recipe.total_nutr_data(vector_features_opt=[vector_features])
        return recipe

    @classmethod
    def merge(self, intake_list_list, names=True):
        if len(intake_list_list) > 1:
            recipe_merge = Recipe('', '', '', None, blank=True, features=intake_list_list[0].features)
            recipe_merge.set_nutr_id("nutrdesc" if names else "id")
            recipe_merge.perfil = intake_list_list[0].perfil
            recipe_merge.perfil_intake = intake_list_list[0].perfil_intake
            foods_tmp = {}
            for intake_list in intake_list_list:
                for ndb_no, food in intake_list.foods.items():
                    if ndb_no in foods_tmp:
                        foods_tmp[ndb_no].append(food)
                    else:
                        foods_tmp[ndb_no] = [food]
            foods = {}
            for ndb_no, foods_ndb_no in foods_tmp.items():
                if len(foods_ndb_no) > 1:
                    foods[ndb_no] = sum(foods_ndb_no)
                else:
                    foods[ndb_no] = foods_ndb_no.pop()
            recipe_merge.foods = foods
            recipe_merge.total_nutr_data()
            return intake_total
        else:
            return intake_list_list[0]

    @classmethod
    def merge_with_vector_features(self, perfil_intake, features, vector_features):
        recipe_merge = Recipe('', '', '', None, blank=True, features=features)
        recipe_merge.perfil_intake = perfil_intake
        recipe_merge.total_nutr_data(vector_features_opt=vector_features)
        return recipe_merge

    def recipe2food(self):
        food = Food(weight=self.weight, avg=False)
        food.radio_omega_raw = self.radio_omega
        omegas_names = ["omega 3", "omega 6", "omega 7"]
        food.omegas = [(omega, self.total_nutr_names.get(omega, [0, ''])[0]) for omega in omegas_names]
        nutrients = [(vector[0][0], sum(v for _, v in vector)) for vector in zip(*self.vector_features())]
        food.nutrients = [(nutr_no, v) for nutr_no, v in nutrients if v > 0]
        return food

def lower_essencial_nutrients(perfil):
    nutr_avg = Food.get_matrix(PREPROCESSED_DATA_DIR + "nutavg.p")
    edad = perfil["edad"]
    genero = perfil["genero"]
    unidad_edad = perfil["unidad_edad"]
    rnv_type = perfil["rnv_type"] 
    nutrs_intake = intake(edad, genero, unidad_edad, rnv_type)
    values = []
    for nutr_no, nutrdesc, avg_val, _ in nutr_avg:
        try:
            if nutrs_intake[nutrdesc].nutr_no == nutr_no:
                ref_value = nutrs_intake[nutrdesc].get_value()
                values.append((nutr_no, nutrdesc, avg_val * 100 / ref_value))
        except KeyError:
            pass
    return sorted(values, key=lambda x:x[2])


def memoize(f):
    cache = {}
    @wraps(f)
    def inner(arg, **kwargs):
        if arg not in cache:
            cache[arg] = f(arg, **kwargs)
        return cache[arg]
    return inner

@memoize
def aux(recipe_id, features=None, intake_params=None):
    return MenuRecipe.ids2recipes([recipe_id], intake_params, features=features).pop()

def search_menu():
    from itertools import combinations_with_replacement, combinations
    import gc
    #import resource
    conn, cursor = conection()
    query = """SELECT recipe.id FROM recipe"""
    cursor.execute(query)
    ids = [e[0] for e in cursor.fetchall()]
    conn.close()
    results = [(0,0,0), (0,0,0), (0,0,0), (0,0,0), (0,0,0)]
    features = Recipe.create_generic_features()
    intake_params = {"edad": 40, "unidad_edad": u"años", "genero": "H", "rnv_type": 1}
    for i in range(7, 8):
        for j, row in enumerate(combinations(ids, i)):
            #print(j)
            recipes = [aux(recipe_id, intake_params=intake_params, features=features) for recipe_id in row]
            menu = Recipe.merge(recipes, names=False)
            print("____", row, menu.score)
            heapq.heappushpop(results, (menu.score, row, menu.energy()))
            if j % 1000 == 0:
                #print("RESOURCE", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1000)
                #print("COLLECT")
                gc.collect(0)
    print(sorted(results, key=lambda x:x[0], reverse=True))


def categories_calif(data, cache):
    import random
    conn, cursor = conection()
    categories = {"Carne de pollo": [{"id": "0500", "search": None}], 
        "Legumbres": [{"id": "1600", "search": None}],
        "Carne de res": [{"id": "1300", "search": None}],
        "Salchichas o carnes frias": [{"id": "0700", "search": None}],
        "Huevo o l\xc3\xa1cteos": [{"id": "0100", "search": "leche"}, {"id": "0100", "search": "huevo"}],
        "Verduras": [{"id": "1100", "search": None}],
        "Frutas": [{"id": "0900", "search": None}],
        "Caf\xc3\xa9 o t\xc3\xa9 descafeinados": [{"id": "1400", "search": "te"}, {"id": "1400", "search": "cafe"}],
        "Caf\xc3\xa9 o t\xc3\xa9 con cafeina": [{"id": "1400", "search": "te"}, {"id": "1400", "search": "cafe"}],
        "Refrescos o bebidas endulzadas": [{"id": "1400", "search": "coca"}],
        "Refrescos bajos en calorias": [{"id": "1400", "search": "coca"}],
        "Pescados o mariscos": [{"id": "1500", "search": None}],
        "Nueces y semillas": [{"id": "1200", "search": None}],
        "Cereales o pastas": [{"id": "0800", "search": None}],
        "Carne de cerdo": [{"id": "1000", "search": None}],
        "Dulces": [{"id": "1900", "search": None}]}
    features = Recipe.create_generic_features()
    perfil = {"edad": 26, "genero": "H", "unidad_edad": u"años", "rnv_type": 1}
    perfil_intake = intake(
        perfil["edad"], 
        perfil["genero"], 
        perfil["unidad_edad"].encode("utf8", "replace"), 
        perfil["rnv_type"])
    intake_light_format = {
        "perfil": perfil,
        "foods": [],
        "name": "test"}
    vector_features_list = []
    data_dict = dict(data)
    count = 0
    totals = []
    while count < 7:
        for category_name, category in categories.items():
            value = data_dict[category_name]
            rand = random.uniform(0, 1)
            if rand <= value:
                for type_category in category:
                    key = category_name+type_category["id"]+str(type_category["search"])
                    if not key in cache:
                        if type_category["search"] is not None:
                            query = """SELECT nut_data.nutr_no, nutrdesc, AVG(nutr_val) as avg
                            FROM nut_data, nutr_def, food_des, fd_group 
                            WHERE nut_data.nutr_no=nutr_def.nutr_no 
                            AND fd_group.fdgrp_cd=food_des.fdgrp_cd 
                            AND food_des.ndb_no=nut_data.ndb_no 
                            AND food_des.fdgrp_cd='{category}'
                            AND nutr_val > 0
                            AND long_desc_es ilike '%{search}%'
                            GROUP BY nutrdesc, nut_data.nutr_no""".format(
                                category=type_category["id"], 
                                search=type_category["search"])
                            cursor.execute(query)
                        else:
                            query = """SELECT nut_data.nutr_no, nutrdesc, AVG(nutr_val) as avg
                                FROM nut_data, nutr_def, food_des, fd_group 
                                WHERE nut_data.nutr_no=nutr_def.nutr_no 
                                AND fd_group.fdgrp_cd=food_des.fdgrp_cd 
                                AND food_des.ndb_no=nut_data.ndb_no 
                                AND food_des.fdgrp_cd=%s
                                AND nutr_val > 0
                                GROUP BY nutrdesc, nut_data.nutr_no"""
                            cursor.execute(query, [type_category["id"]])
                        cache[key] = cursor.fetchall()
                    nutrs, _ = Food.subs_omegas([(nutr_no, nut, (float(v) * 50) / 100.0, "") 
                                        for nutr_no, nut, v in cache[key]])
                    vector_features = Food.vector_features(features, nutrs).items()
                    vector_features_list.append(vector_features)
        totals.append(Recipe.merge_with_vector_features(perfil_intake, features, vector_features_list).score)
        count += 1
    conn.close()
    return sum(totals)/len(totals)

def read_vector_food():
    import csv
    with open("/home/agmartinez/Programas/alimentos/data_survey/students/encuesta_alimentos_alumnos_vector.csv", 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in reader:
            header = row
            break
        results = []
        cache = {}
        for i, row in enumerate(reader):
            results.append(categories_calif(zip(header, map(float, row)), cache))
            #if i == 10:
            #    break
        print("****AVG", sum(results)/len(results))
        print(results)


class FoodType(object):
    def __init__(self, foods, desc, category):
        self.desc = desc
        self.foods = foods
        self.category = category


class OptionSearch(object):
    def __init__(self):
        self.foods = {
            "fruits": FoodType(["09139", "09037", "09200", "09266", "09218", 
                        "09500", "09277", "09086", "09252", "09414", 
                        "09412", "09340", "09415", "09129", "09132", 
                        "09131", "09236", "09316", "09167", "09302", 
                        "09174", "09181", "09148", "09326", "09226", 
                        "09279", "09089", "09286", "09322", "09030", "09176",
                        "09287", "09150", "09112", "09042", "09050", "09078",
                        "09079", "09163", "09298"], "", "Frutas"),
            "vegetables": FoodType(["11603", "11205", "11529", "11446", "11457", 
                            "11091", "11964", "11124", "11216", "11357", "11080", 
                            "11984"], "", "Vegetales"),
            "spices_herbs": FoodType(["02003", "02009", "02066", "02044", "02012", 
                        "02029", "02049", "02030", "02027", "02020", "02032", 
                        "02063", "02037"], "", "Especias y Hierbas"),
            "nuts_seeds": FoodType(["12036", "12065", "12151", "12220", "12006",
                        "12155"], "", "Nueces y Semillas"),
            "legumes": FoodType(["16109", "16139", "16168", "16027", "16069", 
                                "16014", "16389", "16087", "16057"], "", "Legumbres"),
            "grains": FoodType(["20078", "20038", "20035", "20001", "20137", 
                    "20035", "20034", "20033", "02013"], "", "Granos y pastas"),
            "drinks": FoodType(["14096", "14106", "14352", "43479", "14649", 
                                "14545", "14219", "14003"], "", "Bebidas")}
        self.weights = self.set_weights()
        self.nutr_detail = self.fill_nutr_detail()
        self.weights_best_for = None

    def join(self, food_values):
        import itertools
        data_list = itertools.chain.from_iterable(food_values)
        return data_list

    def select_food(self, type_food):
        return self.join(self.foods[type_].foods for type_ in type_food)

    @classmethod
    def set_weights(self):
        from nutrientes import weights
        weights = {
            "Ayuda a combatir la Osteoporosis": weights.WEIGHT_NUTRS_OSTEOPOROSIS, 
            "Bajo en carbohidratos y azucar": weights.WEIGHT_NUTRS_LOW_SUGAR,
            "Anti oxidantes": weights.WEIGHT_NUTRS_FREE_RADICALS_AO,
            "Anti colesterol": weights.WEIGHT_NUTRS_ANTI_CHOLESTEROL,
            "Bajo en grasas": weights.WEIGHT_NUTR_LOW_FAT,
            "Ayuda al sistema nervioso": weights.WEIGHT_NUTRS_NEURAL,
            "Ayuda a la prostata": weights.WEIGHT_NUTR_PROSTATE_CARE,
            "Ayuda a los musculos": weights.WEIGHT_NUTRS_WEIGHT_BODY}
        return weights

    def extra_nutr_detail(self):
        return {"omega3": """Los ácidos grasos omega 3 son ácidos grasos poliinsaturados esenciales (el organismo humano no los puede fabricar a partir de otras sustancias). Algunas fuentes de omega 3 pueden contener otros ácidos grasos como los omega 6. Se ha demostrado experimentalmente que el consumo de grandes cantidades de omega-3 aumenta considerablemente el tiempo de coagulación de la sangre, son benéficos para el corazón y entre sus efectos positivos se pueden mencionar, entre otros: acciones antiinflamatorias y anticoagulantes, disminución de los niveles de colesterol y triglicéridos y la reducción de la presión sanguínea. Estos ácidos grasos también pueden reducir los riesgos y síntomas de otros trastornos, incluyendo diabetes, accidente cerebrovascular, algunos cánceres, artritis reumatoidea, asma, enfermedad intestinal inflamatoria, colitis ulcerativa y deterioro mental.  Los estudios han demostrado que los omega-3 y omega-6 no sólo hay que tomarlos en cantidades suficientes, además hay que guardar una cierta proporción entre ambos tipos, de preferencia 1:1.""",
        "omega6": """
        Los ácidos grasos omega-6 (ω-6) son un tipo de ácido graso comúnmente encontrados en los alimentos grasos o la piel de animales. Estudios recientes han encontrado que niveles excesivos de omega-6, comparado con omega-3, incrementan el riesgo de contraer diferentes enfermedades, incluyendo depresión.

Las dietas modernas usualmente tienen una proporción 10:1 de ácidos grasos omega-6 a omega-3, algunos de 30 a 1. La proporción sugerida es de 4 a 1 o menor. Los riesgos de alta concentración o consumo de omega-6 están asociados con ataques al corazón, ACV, artritis, osteoporosis, inflamación, cambios de ánimo, obesidad y cáncer. 
""",
        "omega7": """Es un acido graso monoinsaturado que ayuda de forma muy específica en la regeneración y nutrición de la piel y mucosas. Sin embargo, su consumo incrementa la resistencia a la insulina.
""",
        "omega9": """Los ácidos grasos omega-9 (ω-9) son un tipo de ácido graso monoinsaturado. Es una grasa que esta presente en la membrana de las células y vasos sanguineos. El omega 9 ayuda a bajar la hipertensión arterial y ayuda a prevenir problemas circulatorios. Sin embargo, su consumo incrementa la resistencia a la insulina.
"""}

    def fill_nutr_detail(self):
        from nutrientes.models import NutrDesc
        base = {nutrdesc.nutr_no_t: nutrdesc.desc for nutrdesc in NutrDesc.objects.all()}
        base.update(self.extra_nutr_detail())
        return base

    def order_best(self, foods, weights_best_for, limit, radio_o):
        rank_results = best_of_selected_food(foods, weights_best_for, limit, radio_o)
        foods_dict = {food.ndb_no: food for food in foods}
        return ((i, foods_dict[ndb_no]) for i, ndb_no in rank_results)

    def best_weights(self, weights):
        if len(weights) == 1:
            return self.weights.get(weights[0], WEIGHT_NUTRS)
        else:
            nutrs = {}
            for weight in weights:
                for nutr_no, value in self.weights[weight].items():
                    if nutr_no in nutrs:
                        if 1 <= nutrs[nutr_no] < value:
                            nutrs[nutr_no] = value
                    else:
                        nutrs[nutr_no] = value
            return nutrs

    def best(self, type_food, weights_for=["all"], limit=10, radio_o=True):
        self.weights_best_for = self.best_weights(weights_for)
        foods = [Food(ndb_no, nutr_detail=self.nutr_detail) for ndb_no in self.select_food(type_food)]
        candidate_food = [food for food in foods if food.is_weight_nutrients(self.weights_best_for)]
        return self.order_best(candidate_food, self.weights_best_for, limit, radio_o)

    def weights_best_list(self):
        nutavg_vector = {nutr_no: nutrdesc 
            for nutr_no, nutrdesc, _, _ in Food.get_matrix(PREPROCESSED_DATA_DIR + "nutavg.p")}
        return sorted([(nutavg_vector.get(nutr_no, ''), 
                    self.nutr_detail.get(nutr_no, ''),  
                    self.weights_best_for.get(nutr_no) > 1)
                for nutr_no in self.weights_best_for])
