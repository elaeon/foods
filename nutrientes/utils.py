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


def category_avg_omegas(ids=False, dataset=None):
    _, cursor = conection()
    if ids:
        if dataset is None:
            query = """
                SELECT fd_group.fdgrp_cd, fd_group.fdgrp_desc_es, AVG(omega.radio)
                FROM food_des, fd_group, omega
                WHERE fd_group.fdgrp_cd=food_des.fdgrp_cd
                AND omega.omega3 > 0
                AND omega.ndb_no=food_des.ndb_no GROUP BY fd_group.fdgrp_cd, fd_group.fdgrp_desc_es;
            """
            cursor.execute(query)
        elif type(dataset) == type([]):
            query = """SELECT AVG(omega.radio)
                    FROM food_des, fd_group, omega
                    WHERE fd_group.fdgrp_cd=food_des.fdgrp_cd
                    AND omega.omega3 > 0
                    AND omega.ndb_no=food_des.ndb_no
                    AND food_des.ndb_no IN ({ids})
                    """.format(ids=",".join(("%s" for e in dataset)))
            cursor.execute(query, dataset)
        else:
            query = """
            SELECT fd_group.fdgrp_cd, fd_group.fdgrp_desc_es, AVG(omega.radio)
            FROM food_des, fd_group, omega, nutrientes_fooddescimg
            WHERE fd_group.fdgrp_cd=food_des.fdgrp_cd
            AND nutrientes_fooddescimg.ndb_no_t=food_des.ndb_no
            AND omega.omega3 > 0
            AND omega.ndb_no=food_des.ndb_no GROUP BY fd_group.fdgrp_cd, fd_group.fdgrp_desc_es;
            """
            cursor.execute(query)
        return {food_id: (round(avg, 1), fdgrp_desc_es) for food_id, fdgrp_desc_es, avg in cursor.fetchall()}
    else:
        query = """
            SELECT fd_group.fdgrp_desc_es, AVG(omega.radio)
            FROM food_des, fd_group, omega
            WHERE fd_group.fdgrp_cd=food_des.fdgrp_cd
            AND omega.omega3 > 0
            AND omega.ndb_no=food_des.ndb_no GROUP BY fd_group.fdgrp_desc_es;
        """
        cursor.execute(query)
        return {food_group: round(avg, 1) for food_group, avg in cursor.fetchall()}

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
            set_base = set(ndb_no for ndb_no, v in cat.values()[0]["data"].items() if v > 0)
            for v in cat.values()[1:]:
                set_base = set_base.intersection(set(ndb_no for ndb_no, v in v["data"].items() if v > 0))
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
        query = """SELECT food_des.ndb_no, food_des.long_desc_es, food_des.long_desc
                FROM food_des, ranking, fd_group
                WHERE food_des.ndb_no=ranking.ndb_no
                AND fd_group.fdgrp_cd=food_des.fdgrp_cd
                AND type_position = 'category'
                AND fd_group.fdgrp_cd='{category}'
                ORDER BY position""".format(category=category_food)

    cursor.execute(query)
    return cursor.fetchall()


def alfabetic_food(category_food=None):
    _, cursor = conection()
    
    if category_food is None:
        query = """SELECT food_des.ndb_no, long_desc_es, fd_group.fdgrp_cd, fdgrp_desc_es, food_des.long_desc
                FROM food_des, fd_group
                WHERE fd_group.fdgrp_cd=food_des.fdgrp_cd
                ORDER BY long_desc_es"""
    else:
        query = """SELECT food_des.ndb_no, food_des.long_desc_es, food_des.long_desc
                FROM food_des, fd_group
                WHERE fd_group.fdgrp_cd=food_des.fdgrp_cd
                AND fd_group.fdgrp_cd='{category}'
                ORDER BY long_desc_es""".format(category=category_food)

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
        #print(u"15212" in self.base_food)
        for nutr_no in self.category_nutr.keys():
            data.setdefault(nutr_no, [])
            reverse = not bool(self.category_nutr[nutr_no]["caution"])
            for ndb_no in self.base_food:
                nutr_val = self.category_nutr[nutr_no]["data"].get(ndb_no, 0.0)
                data[nutr_no].append((ndb_no, self.foods.get(ndb_no, None), nutr_val))
            data[nutr_no].sort(reverse=reverse, key=lambda x: x[2])
        return data
    
    def rank_weight_data(self, category_nutr):
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

        return positions.values()

    def set_rank(self, ndb_no, nutr_no, position):
        if self.ranks is None:
            self.ranks = {}
        self.ranks.setdefault(ndb_no, {})
        self.ranks[ndb_no][nutr_no] = position

    def get_values_food(self, ndb_no):
        if self.ranks is None:
            category_nutr = self.ids2data_sorted()
            self.rank_weight_data(self, category_nutr)            
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
        self.weight_order()
        if limit is None:
            return self.results
        else:
            import itertools as it
            return it.takewhile(lambda x: x[0] < limit, self.results)
    
    def weight_order(self, omegas=None, limit=None, natural=True):
        total = {food["attr"][0]: {"global": food["i"], "name": food["attr"][1], "val": food["val"]} 
                for food in self.rank_weight_data(self.ids2data_sorted())}

        if omegas is not None:
            omegas_d = dict(omegas)
            for ndb_no in total:
                radio = omegas_d[ndb_no]
                total.setdefault(ndb_no, {})

                if 0 < radio <= 4:
                    total[ndb_no]["radio"] = -normal(radio, 1, 1) * 3
                else:
                    total[ndb_no]["radio"] = radio
        
        results = [(v.get("global", 10000)/10000.0 + v.get("radio", 0), ndb_no, v.get("name", ""), v["val"]) 
            for ndb_no, v in total.items()]
        results.sort()
        if limit is not None:
            self.results = results[:limit]
        else:
            self.results = results

        if natural:
            self.results = Rank.rank2natural(self.results, f_index=lambda x: x[0])


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
    rank.weight_order(omegas=radio_omega(category=category))
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
    if radio_o:
        omegas = [(food.ndb_no, food.radio_omega_raw) for food in foods]
    else:
        omegas = None
    rank.weight_order(omegas=omegas, limit=limit)
    return [(i, ndb_no) for i, (_, ndb_no, _, _) in rank.results]

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
        self.energy_density = 0
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

    def calc_energy_density(self):
        n = {k: v for k, name, v, u in self.nutrients}
        try:
            self.energy_density = n["208"] / self.weight
        except KeyError:
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
        #nutrientes = [(nutrdesc, total, units) for nutr_no, nutrdesc, total, units in self.nutrients]
        nutrientes_units_converted = convert_units_scale((total, units) for _, _, total, units in self.nutrients)
        totals = [(nc, n[1], 'g') for n, nc in zip(self.nutrients, nutrientes_units_converted) if nc != None]
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

    def is_weight_nutrients(self, weights_good, weight_avg_nutr):
        def MIN_PORCENTAJE_EXIST(l_weights):
            if l_weights <= 5:
                v = l_weights * .8
            elif 5 <= l_weights <= 10:
                v = l_weights * .6
            elif 10 <= l_weights:
                v = l_weights * .5
            else:
                v = 0
            return round(v, 0)
            
        nutr_weight = {}
        nutrients = {nutr_no: (v, u) for nutr_no, _, v, u in self.nutrients}
        for w_nutr_no, weight in weights_good:
            if weight == 1:
                val_min = self.nutr_avg.get(w_nutr_no, [0,0])[1] * (weight_avg_nutr * .3) 
            else:
                val_min = self.nutr_avg.get(w_nutr_no, [0,0])[1] * weight_avg_nutr
            v_u = nutrients.get(w_nutr_no, [-1, None])
            if val_min <= v_u[0]:
                nutr_weight[w_nutr_no] = (
                    weight,
                    v_u,
                    self.nutr_avg[w_nutr_no][0], 
                    self.nutr_detail.get(w_nutr_no, ""))

        GOOD_LEVEL_OF_NUTR = len([w for w, _, _, _ in nutr_weight.values() if w < 1])
        len_weights_good_w = len([w for n, w in weights_good if w < 1])
        approved = MIN_PORCENTAJE_EXIST(len_weights_good_w) <= GOOD_LEVEL_OF_NUTR
        if approved:
            nutrientes_units_converted = convert_units_scale((v, u) for _, (v, u), _, _ in nutr_weight.values())
            totals = [(nc, n[2], n[3]) 
                for n, nc in zip(nutr_weight.values(), nutrientes_units_converted) if nc != None]
            self.weights_nutrients_approved = sorted(totals, key=lambda x:x[0], reverse=True)
        return approved

    def nutrients_selector(self, seleccion):
        if seleccion == "nutrients":
            return self.nutrients
        else:
            return self.top_nutrients_avg()

    def nutrients_twins(self):
        matrix = MatrixNutr(name=PREPROCESSED_DATA_DIR + 'matrix.csv')
        data = matrix.to_dict(True)
        data_nutr = {}
        for ndb_no, nutrients in data.items():
            for nutr_no, v in nutrients:
                if v > 0:
                    data_nutr.setdefault(nutr_no, {})
                    data_nutr[nutr_no][ndb_no] = v

        nutr_no, _, _, _ = self.nutrients[0]
        data_s = set(data_nutr.get(nutr_no, {}).keys())
        for nutr_no, _, _, _ in self.nutrients[1:]:
            try:
                tmp = set(data_nutr[nutr_no].keys())
                data_s = data_s.intersection(tmp)
            except KeyError:
                pass
        
        v_base = [e for _, e in data[self.ndb_no]]
        v_base_0 = [e for _, e in data[self.ndb_no] if e > 0]
        vectors = []
        for ndb_no in data_s:
            vector_other_0 = [e for _, e in data[ndb_no] if e > 0]
            if len(vector_other_0) == len(v_base_0):
                vectors.append((ndb_no, [e for _, e in data[ndb_no]]))
        foods = self.min_distance((self.ndb_no, v_base), vectors, top=5)
        return ((ndb_no, self.get_food(ndb_no), v) for ndb_no, v in foods)

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

def principal_nutrients(category=None, sorted_=True, dataset=None):
    _, cursor = conection()
    if category is None and dataset is None:
        query = """SELECT nutrdesc, AVG(nutr_val) as avg, units 
            FROM nut_data, nutr_def 
            WHERE nut_data.nutr_no=nutr_def.nutr_no 
            GROUP BY nutrdesc,units ORDER BY avg desc"""
        cursor.execute(query)
    else:
        if dataset == "foodimg":
            query = """SELECT nutrdesc, AVG(nutr_val) as avg, units 
                FROM nut_data, nutr_def, food_des, fd_group, nutrientes_fooddescimg
                WHERE nut_data.nutr_no=nutr_def.nutr_no 
                AND fd_group.fdgrp_cd=food_des.fdgrp_cd 
                AND food_des.fdgrp_cd='{category}'
                AND food_des.ndb_no=nutrientes_fooddescimg.ndb_no_t
                AND nutrientes_fooddescimg.ndb_no_t=nut_data.ndb_no
                GROUP BY nutrdesc,units ORDER BY avg desc""".format(category=category)
            cursor.execute(query)
        elif type(dataset) == type([]):
            query = """SELECT nutrdesc, AVG(nutr_val) as avg, units 
                    FROM nut_data, nutr_def, food_des
                    WHERE nut_data.nutr_no=nutr_def.nutr_no
                    AND food_des.ndb_no=nut_data.ndb_no 
                    AND food_des.ndb_no IN ({ids})
                    GROUP BY nutrdesc, units 
                    ORDER BY avg""".format(ids=",".join(("%s" for e in dataset)))
            cursor.execute(query, dataset)
        else:
            query = """SELECT nutrdesc, AVG(nutr_val) as avg, units 
                FROM nut_data, nutr_def, food_des, fd_group 
                WHERE nut_data.nutr_no=nutr_def.nutr_no 
                AND fd_group.fdgrp_cd=food_des.fdgrp_cd 
                AND food_des.ndb_no=nut_data.ndb_no 
                AND food_des.fdgrp_cd='{category}' 
                GROUP BY nutrdesc,units ORDER BY avg desc""".format(category=category)
            cursor.execute(query)
    nutrientes = [(nutrdesc, avg, units) for nutrdesc, avg, units in cursor.fetchall()]
    nutrientes_units_converted = convert_units_scale((avg, units) for _, avg, units in nutrientes)
    totals = [(n[0], nc) for n, nc in zip(nutrientes, nutrientes_units_converted) if nc != None]
    if sorted_:
        return sorted(totals, key=lambda x: x[1], reverse=True)
    else:
        return totals

def principal_nutrients_percentaje(category=None, dataset=None, ndb_no=None):
    if dataset is not None:
        features, omegas = Food.subs_omegas(
            [(e[0], e[0], e[1], None) 
            for e in principal_nutrients(category=category, dataset=dataset)])
        all_nutr = features + [(omega, omega, v, u) for omega, v, u in omegas.values()]
    else:
        all_nutr = Food(ndb_no, avg=False).nutrients
    
    sorted_data = sorted(all_nutr, key=lambda x: x[2], reverse=True)
    maximo = sum((d[2] for d in sorted_data))
    return [(d[2]*100./maximo, d[0]) for d in sorted_data if d[2]*100./maximo > 0]

def principal_nutrients_avg_percentaje(category, all_food_avg=None, dataset=None):
    if all_food_avg is None:
        all_food_avg = {nutrdesc: v for v, nutrdesc in principal_nutrients_percentaje(dataset=dataset)}
    category_avg = principal_nutrients_percentaje(category, dataset=dataset)
    values = ((v, (v / all_food_avg.get(nutrdesc, 0)), nutrdesc)
                for v, nutrdesc in category_avg if 0 < all_food_avg.get(nutrdesc, 0) <= v)
    return sorted(values, key=lambda x:x[1], reverse=True)

def principal_nutrients_avg_percentaje_no_category(all_food_avg, ndb_no):
    print(all_food_avg)
    print("***********")
    category = principal_nutrients_percentaje(ndb_no=ndb_no)
    print(category)
    print("###########")
    values = ((v, (v / all_food_avg.get(nutrdesc, 0)), nutrdesc)
                for v, nutrdesc in category if 0 < all_food_avg.get(nutrdesc, 0) <= v)
    return sorted(values, key=lambda x:x[1], reverse=True)

def convert_units_scale(values):
    units_scale = {"g": 1, "mg": 1000, u"µg": 1000000} #gramo, miligramo, microgramo
    converted = []
    for v, units in values:
        unit_c = units_scale.get(units, 0)
        if unit_c != 0:
            converted.append(float(v / unit_c))
        else:
            converted.append(None)
    return converted

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
        perfil["unidad_edad"], 
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
        return sorted(recipes_l, key=lambda x:x.score, reverse=True)[:max_number]
    else:
        return sorted(recipes_l, key=lambda x:x.score_best(), reverse=True)[:max_number]


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
    def __init__(self, edad, genero, unidad_edad, rnv_type, blank=False, 
                perfil_intake=None, name=None, features=None):
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
        nutrientes = [(nutrdesc, total, units) for nutrdesc, (total, units) in self.total_nutr_names.items()]
        nutrientes_units_converted = convert_units_scale((avg, units) for _, avg, units in nutrientes)
        totals = [(nc, n[0]) for n, nc in zip(nutrientes, nutrientes_units_converted) if nc != None]
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
            return recipe_merge
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


class SearchCompleteFoods(object):
    def __init__(self, universe=None):
        from nutrientes.models import FoodDescImg

        self.selector = None
        if universe is None:
            self.universe = FoodDescImg.objects.values_list('ndb_no_t', flat=True)
            #self.universe =  FoodDescImg.objects.exclude(ndb_no_t="09062").values_list('ndb_no_t', flat=True)
            #self.universe = (ndb_no for ndb_no in Food.alimentos(limit="limit 9000"))
        self.min_distance_calculated = None

    def score(self, selector="nutrients"):
        self.selector = selector
        nutrient_map = dict(self.nutrients_to_map(self.universe, selector))
        active_positions = {ndb_no: [i for i, e in enumerate(vector) if e > 0] 
                            for ndb_no, vector in nutrient_map.items()}
        active_positions_v = {ndb_no: [v for v in vector if v > 0] 
                            for ndb_no, vector in nutrient_map.items()}
        probabilities = self.probability(
            filter(lambda x: len(x) > 0, active_positions.values()))
        nutr_row_c = OrderedDict(((k, 0) for k, v in WEIGHT_NUTRS.items() if v <= 1))
        for nutr_no, _, v, _ in Food.get_matrix(PREPROCESSED_DATA_DIR + "nutavg.p"):
            nutr_row_c[nutr_no] = v
        avg_items = nutr_row_c.values()
        totals = []
        for i, v in zip(active_positions.values(), active_positions_v.values()):
            vector = zip(i,v)
            total = 0
            for index, value in vector:
                c = (value * 100) / avg_items[index]
                if c >= 500:
                    c = 500
                total += c * (1 - probabilities[index])
            totals.append(total)
        result = sorted(zip(totals, active_positions), key=lambda x:x[0], reverse=True)
        for e in result[:10]:
           print(e)

    def probability(self, active_positions_values):
        import collections
        total = float(len(active_positions_values))
        counter = collections.Counter()
        for indexes in active_positions_values:
            counter.update(indexes)
        return {k: v/total for k, v in counter.items()}

    def difference(self, v1, v2):
        return sum((e1 > 0) ^ (e2 > 0) for e1, e2 in zip(v1, v2))

    def merge(self, v1, v2):
        return [e1 + e2 for e1, e2 in zip(v1, v2)]

    def nutrients_to_map(self, foods, selector):        
        for food in (Food(ndb_no) for ndb_no in foods):
            nutr_row_c = OrderedDict(((k, 0) for k, v in WEIGHT_NUTRS.items() if v <= 1))
            for nutr in food.nutrients_selector(selector):
                nutr_no, _, v, u = nutr
                if nutr_no in nutr_row_c:
                    nutr_row_c[nutr_no] = v
            yield food.ndb_no, nutr_row_c.values()

    def all_is_1(self, data):
        return all((v == 1 for _, v in data.items()))

    def search(self, selector="nutrients", upper=0.8, lower=0.8):
        self.selector = selector
        nutrient_map = dict(self.nutrients_to_map(self.universe, selector))
        active_positions = {ndb_no: [i for i, e in enumerate(vector) if e > 0] 
                            for ndb_no, vector in nutrient_map.items()}
        min_data_g = 50
        counter = 0
        len_key = 0
        while len_key < 11:
            probabilities = self.probability(
                filter(lambda x: len(x) > 0, active_positions.values()))
            if self.all_is_1(probabilities):
                break
            score = {ndb_no: sum(1 - probabilities[index] for index in vector)
                        for ndb_no, vector in active_positions.items()}

            best_distribution = sorted(score.items(), key=lambda x:x[1], reverse=True)
            upper_best = best_distribution[:int(len(score)*upper)]
            lower_best = best_distribution[int(len(score)*lower):]
            distance = []
            for ndb_no1, v1 in upper_best:
                for ndb_no2, v2 in lower_best:
                    distance.append((
                        self.difference(nutrient_map[ndb_no1], nutrient_map[ndb_no2]),
                        ndb_no1, 
                        ndb_no2))
            if len(distance) == 0:
                break
            max_distance = max(distance)[0]
            print(counter, len(distance), min_data_g)
            best_distance = (e for e in distance if e[0] == max_distance)
            for_delete = set([])
            data_len = []
            tmp_min = min_data_g
            for _, ndb_no_v1, ndb_no_v2 in best_distance:
                vector_merged = self.merge(nutrient_map[ndb_no_v1], nutrient_map[ndb_no_v2])
                for_delete.add(ndb_no_v2)
                min_data_l = len([x for x in vector_merged if x == 0])
                if min_data_l <= min_data_g:
                    n_key = "-".join(set(ndb_no_v1.split("-"))) + "-" + "-".join(set(ndb_no_v2.split("-")))
                    active_positions[n_key] = [i for i, v in enumerate(vector_merged) if v > 0]
                    nutrient_map[n_key] = vector_merged
                else:
                    continue
                if min_data_l < tmp_min:
                    tmp_min = min_data_l
                yield (min_data_l, n_key)

            if tmp_min < min_data_g:
                min_data_g = tmp_min

            for e in for_delete:
                del active_positions[e]
                del nutrient_map[e]
            len_key = max(len(k.split("-")) for k in active_positions)
            counter += 1

    def candidates_vector(self):
        for candidates_key in self.get_bests_candidates():
            candidates = candidates_key.split("-")
            nutrient_map = dict(self.nutrients_to_map(candidates, self.selector))
            vector = [0 for _ in nutrient_map[candidates[0]]]
            while len(candidates) > 0:
                candidate = candidates.pop()
                vector = self.merge(vector, nutrient_map[candidate])
            yield candidates_key, vector

    def get_bests_candidates(self):
        candidates = sorted(self.search(), key=lambda x:x[0])
        self.min_distance_calculated = min(candidates)[0]
        for d, candidate in candidates:
            if d == self.min_distance_calculated:
                yield candidate
            else:
                break

    def calc_results(self):
        self.results = []
        from nutrientes.utils import Food
        light_format = {
            "perfil": {"edad": 40, "genero": "H", "unidad_edad": u"años", "rnv_type": 1},
            "foods": None,
            "name": ""   
        }
        for candidates, v in sorted(self.candidates_vector(), key=lambda x:sum(x[1]), reverse=True):
            foods = {}
            foods_obj = []
            for ndb_no in candidates.split("-"):
                foods[ndb_no] = 100
                foods_obj.append(Food(ndb_no))
            light_format["foods"] = foods
            recipe = Recipe.from_light_format(light_format, data=True)
            self.results.append((recipe.calc_score(), foods_obj))

    def print_(self):
        for score, foods in self.results():
            for food in foods:
                print(food.name, food.ndb_no)
            print score
            print("****")


    def not_found(self):
        nutr_row_c = OrderedDict(((k, 0) for k, v in WEIGHT_NUTRS.items() if v <= 1))
        for _, vector in self.candidates_vector():
            for v, k in zip(vector, nutr_row_c.keys()):
                if v == 0:
                    print(k, v)

    def get_min_distance(self):
        return self.min_distance_calculated

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
    def __init__(self, foods, category):
        self.foods = foods
        self.category = category


def get_fooddescimg(category=None):
    conn, cursor = conection()
    if category is None:
        query = """SELECT ndb_no_t, fdgrp_desc_es
                FROM nutrientes_fooddescimg, food_des, fd_group 
                WHERE fd_group.fdgrp_cd=food_des.fdgrp_cd
                AND nutrientes_fooddescimg.ndb_no_t=food_des.ndb_no"""
    else:
        query = """SELECT ndb_no_t
                FROM nutrientes_fooddescimg, food_des, fd_group 
                WHERE fd_group.fdgrp_cd=food_des.fdgrp_cd
                AND nutrientes_fooddescimg.ndb_no_t=food_des.ndb_no
                AND fd_group.fdgrp_cd='{category}'""".format(category=category)

    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()
    return data

class OptionSearch(object):
    def __init__(self):
        self.foods = self.get_food_db()
        self.weights = self.set_weights()
        self.nutr_detail = self.fill_nutr_detail()
        self.weights_best_for = None
        self.total_food = sum(len(self.foods[c].foods) for c in self.foods)

    def get_food_db(self):
        foods = {}
        for ndb_no, category in get_fooddescimg():
            foods.setdefault(category, [])
            foods[category].append(ndb_no)

        return {category: FoodType(foods[category], category) for category in foods}
            

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
            "Ayuda a combatir la osteoporosis": weights.WEIGHT_NUTRS_OSTEOPOROSIS, 
            "Bajo en carbohidratos y azucar": weights.WEIGHT_NUTRS_LOW_SUGAR,
            "Anti oxidantes": weights.WEIGHT_NUTRS_FREE_RADICALS_AO,
            "Reduce el colesterol": weights.WEIGHT_NUTRS_ANTI_CHOLESTEROL,
            "Bajo en grasas": weights.WEIGHT_NUTR_LOW_FAT,
            "Ayuda al sistema nervioso": weights.WEIGHT_NUTRS_NEURAL,
            "Ayuda a la prostata": weights.WEIGHT_NUTR_PROSTATE_CARE,
            u"Ayuda a la salud de los músculos": weights.WEIGHT_NUTRS_WEIGHT_BODY,
            u"Ayuda a la memoria y concentración": weights.WEIGHT_NUTRS_BRAIN_MEMORY,
            "Ayuda a la vista": weights.WEIGHT_NUTRS_EYES,
            "Ayuda a la piel": weights.WEIGHT_NUTRS_SKIN,
            "Necesarios durante el embarazo": weights.WEIGHT_NUTRS_PREGNANCY,
            "Ayuda a incrementar la masa muscular": weights.WEIGHT_BODY_MASS,
            "Ayuda al sistema inmune": weights.WEIGHT_IMMUNE_SYSTEM,
            "Ayuda a evitar la anemia nutricional": weights.WEIGHT_NUTRITIONAL_ANEMIA}
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

    def best(self, type_food, weights_for=["all"], limit=10, radio_o=True, weight_avg_nutr=0.1):
        self.weights_best_for = self.best_weights(weights_for)
        foods = [Food(ndb_no, nutr_detail=self.nutr_detail) for ndb_no in self.select_food(type_food)]
        weights_good = [(nutr_no, weight) for nutr_no, weight in self.weights_best_for.items() if weight <= 1]
        candidate_food = [food for food in foods if food.is_weight_nutrients(weights_good, weight_avg_nutr)]
        return self.order_best(candidate_food, self.weights_best_for, limit, radio_o)

    def weights_best_list(self):
        nutavg_vector = {nutr_no: nutrdesc 
            for nutr_no, nutrdesc, _, _ in Food.get_matrix(PREPROCESSED_DATA_DIR + "nutavg.p")}
        return sorted([(nutavg_vector.get(nutr_no, ''), 
                    self.nutr_detail.get(nutr_no, ''),  
                    self.weights_best_for.get(nutr_no) > 1)
                for nutr_no in self.weights_best_for])


class FoodVariant(object):
    def __init__(self, ndb_no, category=None):
        self.ndb_no = ndb_no
        self.category = category

class FoodGroup(object):
    def __init__(self, fv1, fv2, count):
        self.fv1 = fv1
        self.fv2 = fv2
        self.count = count
        self.increased = None
        self.decreased = None

    def set_data(self, increased, decreased):
        self.increased = increased
        self.decreased = decreased
        

def zip_fn(fn):
    def view(*args, **kwargs):
        v1, v2 = fn(*args, **kwargs)
        if len(v1) == len(v2):
            return zip(v1, v2)
        else:
            print("Error: v1 and v2 have distinct length")
    return view

@zip_fn
def data_set_fish_moist_heat():
    raw = ["15177", "15242", "15136", "15144", "15143", "15139", "15164", "15171", "15166"]
    moist_heat = ["15178", "15243", "15137", "15227", "15226", "15140", "15165", "15231", "15230"]
    data_set_fish_moist_heat.resumen_text = u"Los pescados y mariscos tienen la caracteristica que, la gran mayoria de sus nutrientes aumenta con la cocción al vapor, en un promedio de {avg_gain}%."
    return raw, moist_heat

@zip_fn
def data_set_fish_dry_heat():
    raw = ["15245", "15028", "15110", "15115", "15114", "15039", "15043", "15015", "15045", "15074", "15019", "15022", "15007", "15046", "15051", "15050", "15008", "15053", "15104", "15036", "15070", "15072", "15107", "15044", "15112", "15064", "15033", "15132", "15031", "15101", "15057", "15005", "15130", "15062", "15066", "15065", "15068", "15006", "15054", "15129", "15073", "15094", "15055", "15090", "15059", "15097", "15091", "15134", "15103", "15079", "15083", "15085", "15108", "15024", "15261"]
    dry_heat = ["15246", "15029", "15111", "15116", "15219", "15040", "15197", "15016", "15199", "15208", "15192", "15193", "15191", "15047", "15052", "15201", "15009", "15202", "15105", "15037", "15071", "15207", "15217", "15198", "15113", "15204", "15034", "15133", "15032", "15102", "15058", "15189", "15223", "15063", "15067", "15205", "15069", "15190", "15203", "15222", "15232", "15215", "15056", "15213", "15206", "15098", "15092", "15224", "15216", "15211", "15212", "15086", "15218", "15195", "15262"]
    data_set_fish_dry_heat.resumen_text = u"Los pescados y mariscos tienen la caracteristica que, la gran mayoria de sus nutrientes aumenta con la cocción en seco, en un promedio de {avg_gain}%"
    return raw, dry_heat

@zip_fn
def data_set_vegetable_boiled():
    raw = ["11147", "11007", "11143", "11209", "11203", "11613", "11088", "11090", "11026", "11522", "11492", "11477", "11467", "11641", "11475", "11191", "11201", "11197", "11282", "11244", "11149", "11298", "11114", "11109", "11135", "11241", "11161", "11157", "11207", "11011", "11457", "11416", "11447", "11096", "11452", "11653", "11029", "11052", "11300", "11304", "11003", "11418", "11086", "11238", "11233", "11622", "11616", "11564", "11963", "11601", "11258", "11278", "11354", "11355", "11350", "11005", "11430", "11104", "11254", "11080", "11112", "11435", "11260", "11265", "11450", "11518", "11525", "11529", "11427", "11603", "11231", "11124"]
    boiled = ["11148", "11008", "11144", "11210", "11204", "11614", "11089", "11091", "11027", "11523", "11493", "11478", "11468", "11642", "11476", "11192", "11202", "11198", "11283", "11245", "11150", "11299", "11115", "11751", "11136", "11242", "11162", "11158", "11208", "11012", "11458", "11417", "11448", "11097", "11453", "11654", "11030", "11053", "11301", "11305", "11004", "11419", "11087", "11269", "11234", "11623", "11617", "11565", "11964", "11602", "11259", "11279", "11357", "11358", "11351", "11006", "11431", "11105", "11255", "11081", "11113", "11436", "11261", "11243", "11451", "11519", "11526", "11530", "11428", "11604", "11232", "11125"]
    data_set_vegetable_boiled.resumen_text = u"Generalmente es mejor comer los vegetales frescos, sin embargo no siembre se puede disfrutar de su sabor cuando están crudos. Cocerlos o hervirlos disminuye su valor nutricional en un {avg_loss}%"
    return raw, boiled

@zip_fn
def data_set_vegetable_frozen():
    raw = ["11007", "11477", "11485", "11467", "11191", "11282", "11495", "11135", "11457", "11722", "11090", "11011", "11052", "11568", "11300", "11304", "11995", "11270", "11233", "11564", "11278", "11821", "11333", "11124"]
    frozen = ["11009", "11479", "11487", "11473", "11195", "11289", "11501", "11137", "11463", "11730", "11092", "11018", "11060", "11574", "11302", "11312", "11996", "11272", "11235", "11566", "11280", "11917", "11337", "11130"]
    data_set_vegetable_frozen.resumen_text = u"Generalmente es mejor comer los vegetales frescos, sin embargo no siembre se puede disfrutar de su sabor cuando están crudos. Congelarlos disminuye su valor nutricional en un {avg_loss}%"
    return raw, frozen

@zip_fn
def data_set_vegetable_canned():
    raw = ["11026", "11467", "11282", "11011", "11457", "11568", "11304", "11974", "11900", "11352", "11979", "11080", "11588", "11124"]
    canned = ["11028", "11471", "11285", "11015", "11461", "11570", "11308", "11975", "11903", "11374", "11632", "11084", "11590", "11128"]
    data_set_vegetable_canned.resumen_text = u"Generalmente es mejor comer los vegetales frescos, sin embargo no siembre se puede disfrutar de su sabor cuando están crudos. Enlatados disminuye su valor nutricional en {avg_loss}%, y aumenta el sodio en un 8700%."
    return raw, canned

@zip_fn
def data_set_fruits_dehydrated():
    raw = ["09021", "09279", "09236", "09077", "09040"]
    dehydrated = ["09030", "09289", "09244", "09009", "09041"]
    data_set_fruits_dehydrated.resumen_text = "Las frutas deshidratadas tienen un aumento de su valor nutricional en un {avg_gain}%."
    return raw, dehydrated

@zip_fn
def data_set_fruits_dried():
    raw = ["09021", "09050", "09146", "09263", "09279", "09089", "09164", "09172", "09003", "09252"]
    dried = ["09032", "09163", "09147", "09264", "09291", "09094", "09165", "09173", "09011", "09259"]
    data_set_fruits_dried.resumen_text = "Las frutas secas tienen un aumento de su valor nutricional en un {avg_gain}%"
    return raw, dried

@zip_fn
def data_set_beans():
    raw = ["16001", "16019", "16042", "16030", "16035", "16027", "16040", "16024", "16045", "16016", "16080", "16083", "16101", "16056", "16069"]
    boiled = ["16002", "16020", "16043", "16031", "16036", "16028", "16041", "16025", "16046", "16017", "16081", "16084", "16102", "16057", "16070"]
    data_set_beans.resumen_text = "Especificamente los frijoles, lentejas, alubias, etc, al ser cocinadas o hervidas pierden un promedio de {avg_loss}% de sus nutrientes. Los nutrientes más afectados son el calcio, omega 3, cholina, fibra y vitamina k, con una perdida de su valor de entre 40% a 45%."
    return raw, boiled


class ExamineFoodVariants(object):
    def __init__(self):
        self.data = self.data_food()
        self.nutr = {nutr_no: nutrdesc for nutr_no, nutrdesc in nutr_features()}

    def data_food(self):
        matrix = MatrixNutr(name=PREPROCESSED_DATA_DIR + 'matrix.csv')
        return matrix.to_dict(True)

    def compare(self, ndb_no1, ndb_no2, count):
        increased = {}
        decreased = {}
        for v1, v2 in zip(self.data[ndb_no1], self.data[ndb_no2]):
            diff = v1[1] - v2[1]
            try:
                v = ((v2[1] * 100) / v1[1])
            except ZeroDivisionError:
                continue
            if diff < 0:
                increased[self.nutr.get(v1[0], v1[0])] = v - 100
            elif diff > 0:
                decreased[self.nutr.get(v1[0], v1[0])] = -v
        fg = FoodGroup(FoodVariant(ndb_no1, 0), FoodVariant(ndb_no2, 1), count)
        fg.set_data(increased, decreased)
        return fg

    def process(self, function_dataset, ndb_no):
        foods = {}
        if ndb_no is not None:
            for i, (ndb_no1, ndb_no2) in enumerate(function_dataset(), 1):
                if ndb_no == ndb_no1:
                    foods[i] = self.compare(ndb_no1, ndb_no2, i)
        else:
            for i, (ndb_no1, ndb_no2) in enumerate(function_dataset(), 1):
                foods[i] = self.compare(ndb_no1, ndb_no2, i)

        #variants = total_i.intersection(total_d)
        #self.csv(foods, variants)
        return foods

    def evaluate_inc_dec(self, function_, ndb_no=None):
        foods = self.process(function_, ndb_no=ndb_no)
        nutr = {}
        k = self.data.keys()[0]
        nutr_list = [nutr_no for nutr_no, _ in self.data[k]]
        for nutr_no in nutr_list:
            count = 0
            nutrdesc = self.nutr.get(nutr_no, nutr_no)
            count_null = 0
            prom_i = 0
            prom_d = 0
            for food in foods.values():
                if nutrdesc in food.increased:
                    count += 1
                    prom_i += food.increased[nutrdesc]
                elif not nutrdesc in food.decreased:
                    count_null += 1
                else:
                    prom_d += food.decreased[nutrdesc]
            if count_null != len(foods):
                total = float(len(foods)) - count_null
                nutr[nutrdesc] = (round(count/total * 100, 2), 
                    round(prom_i/total, 2), round(prom_d/total, 2))
        return nutr

    def category(self, category, sub_category=None):
        categories = {"1500": 
                        {"dry_heat": data_set_fish_dry_heat,
                        "moist_heat": data_set_fish_moist_heat},
                    "1100": 
                        {"boiled": data_set_vegetable_boiled,
                        "frozen": data_set_vegetable_frozen,
                        "canned": data_set_vegetable_canned},
                    "0900":
                        {"dehydrated": data_set_fruits_dehydrated,
                        "dried": data_set_fruits_dried},
                    "1600":
                        {"heat": data_set_beans}
                    }
        functions = []
        if sub_category is None:
            for sub_category_f in categories.get(category, {}).values():
                functions.append(sub_category_f)
        else:
            functions.append(categories.get(category, {}).get(sub_category, {}))

        for function_ in functions:
            data = []
            count_loss = 0.0
            count_gain = 0.0
            avg_loss = 0
            avg_gain = 0
            for k, v in self.evaluate_inc_dec(function_).items():
                if v[0] == 0 and v[1] == 0 and v[2] == 0:
                    pass
                else:
                    data.append((k, v))
                if v[2] < 0 and v[0] < 50:
                    count_loss += 1
                    avg_loss += v[2]
                if v[1] > 0 and v[0] >= 50:
                    count_gain += 1
                    avg_gain += v[1]

            function_.resumen_text = function_.resumen_text.format(
                avg_loss=abs(round(avg_loss/count_loss, 2)),
                avg_gain=abs(round(avg_gain/count_gain, 2)))
            yield data, function_.resumen_text

    def prepare_variants(self, foods, variants):
        for food_group in foods.values():
            for fv in [food_group.fv1, food_group.fv2]:
                ndb_no = fv.ndb_no
                nutrs = {self.nutr.get(nutr_no, nutr_no).encode('utf-8'): v 
                    for nutr_no, v in self.data[ndb_no] if self.nutr.get(nutr_no, nutr_no) in variants}
                yield fv, food_group.count, nutrs

    def csv(self, foods, variants):
        import csv
        with open('variants.csv', 'w') as csvfile:
            fieldnames = [e.encode('utf-8') for e in variants]
            writer = csv.DictWriter(csvfile, fieldnames=["count", "ndb_no", "desc", "category"] + fieldnames)
            writer.writeheader()
            for fv, count, nutrs in self.prepare_variants(foods, variants):
                dict_ = {"ndb_no": fv.ndb_no, "category": fv.category, "count": count}
                dict_.update(nutrs)
                writer.writerow(dict_)

class PiramidFood(object):
    def __init__(self, meat="fish", dataset="foodimg", categories="all", 
                weight_nutrs=WEIGHT_NUTRS, radio_omega=True):
        self.dataset = dataset
        self.base_value = 0
        self.weight_nutrs = weight_nutrs
        self.radio_omega = radio_omega
        if categories == "meats":
            self.categories = set(["1500", "1300", "1700", "1000", "0500", "0700"])
        elif categories == "no-meats":
            self.categories = set(["0800", "0200", "0900", "2000", "1600", "1200", 
                                "1800", "1100", "2500", "1900"]) #"0600" sopas y salsas
        else:
            self.categories = set(["0800", "0200", "0900", "2000", "0100", 
                        "1600", "1200", "1800", "1100"])
            self.categories.add("2500") #Aperitivos
            self.categories.add("1900") #Dulces
            
            self.categories.add("1500")
            if meat == "beef":
                self.categories.add("1300")
            elif meat == "hunt":
                self.categories.add("1700")
            elif meat == "pork":
                self.categories.add("1000")
            elif meat == "luncheon":
                self.categories.add("0700")
            else:
                self.categories.add("0500")

    def process(self):
        nutr = Food.get_matrix(PREPROCESSED_DATA_DIR + "nutavg.p")
        nutr_avg = {nutr_desc: (avg, caution, nutr_no) 
            for nutr_no, nutr_desc, avg, _, caution in mark_caution_nutr(nutr)}
        
        categories_data = {}
        if type(self.dataset) == type([]):
            all_food_avg = {nutrdesc: v for v, nutrdesc in principal_nutrients_percentaje(dataset=self.dataset)}
            for ndb_no in self.dataset:
                percentaje_data = principal_nutrients_avg_percentaje_no_category(
                    all_food_avg, ndb_no)
                categories_data[ndb_no] = percentaje_data
            print(categories_data)
        else:
            all_food_avg = {nutrdesc: v for v, nutrdesc in principal_nutrients_percentaje()}
            for category in self.categories:
                percentaje_data = principal_nutrients_avg_percentaje(
                    category, all_food_avg=all_food_avg, dataset=self.dataset)
                categories_data[category] = percentaje_data
        nutrients = {}
        category_to_name = {}
        for category, values in categories_data.items():
            #print(category, values)
            for v, radio_v, nutrdesc in values:
                if nutrdesc in nutr_avg:
                    _, caution, nutr_no = nutr_avg[nutrdesc]
                    if nutr_no in self.weight_nutrs:
                        nutrients.setdefault(nutrdesc, [])
                        nutrients[nutrdesc].append((v, category, caution))
                else:
                    if nutrdesc in self.weight_nutrs:
                        caution = self.weight_nutrs.get(nutrdesc, 2) > 1
                        nutrients.setdefault(nutrdesc, [])
                        nutrients[nutrdesc].append((v, category, caution))
        if self.radio_omega:
            nutrients["radio"] = []
            if type(self.dataset) == type([]):
                for ndb_no in self.dataset:
                    food = Food(ndb_no, avg=False)
                    radio_raw = food.radio_omega_raw
                    if radio_raw > 4:
                        caution = True
                    elif radio_raw == 0:
                        caution = False
                    else:
                        radio_raw = 4 / radio_raw
                        caution = False
                    nutrients["radio"].append((radio_raw, ndb_no, caution))
            else:
                omegas = category_avg_omegas(ids=True, dataset=self.dataset)
                subcategories = set([c for c, v in categories_data.items() if c in self.categories])        
                for category, (radio_raw, category_desc) in omegas.items():
                    if category in subcategories:
                        category_to_name[category] = category_desc 
                        nutrients["radio"].append((radio_raw, category, True if radio_raw > 4 else False))

        total_categories = len([c for c, v in categories_data.items() if len(v) > 0])
        try:
            self.base_value = 100.0 / (total_categories * len(nutrients))
        except ZeroDivisionError:
            self.base_value = 0
        nutrs_value_good = []
        #print(nutrients.keys())
        for nutrdesc, categories_values in nutrients.items():
            #print(nutrdesc, categories_values)
            categories = sorted(categories_values, reverse=True)
            max_value = categories[0][0] * ((1. / self.weight_nutrs.get(nutrdesc, 1)) * .17)
            nutrs_value_good.extend([
                (self.base_value * (v / max_value), category) 
                for v, category, caution in categories if not caution])
            nutrs_value_good.extend([
                (self.base_value * (-v / max_value), category) 
                for v, category, caution in categories if caution])

        #print(nutrs_value_good)
        def create_values(nutrs_value, total_categories):
            category_new_values = {}
            for value, category in nutrs_value:
                category_new_values.setdefault(category, 0)
                category_new_values[category] += value

            diff = (100.0 - sum(category_new_values.values())) / total_categories
            for category in category_new_values:
                category_new_values[category] += diff
            return category_new_values.items()

        good = sorted(create_values(nutrs_value_good, total_categories), key=lambda x:x[1])
        if type(self.dataset) == type([]):
            for category, value in good:
                yield category, value
        else:
            for category, value in good:
                yield category_to_name.get(category, category), value
