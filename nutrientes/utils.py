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
    conn_string = "host='' dbname='alimentos' user='{username}'".format(username=USERNAME)
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
                ORDER BY global_position"""
    else:
        query = """SELECT food_des.ndb_no, food_des.long_desc_es, food_des.long_desc
                FROM food_des, ranking, fd_group
                WHERE food_des.ndb_no=ranking.ndb_no
                AND fd_group.fdgrp_cd=food_des.fdgrp_cd
                AND fd_group.fdgrp_cd='{category}'
                ORDER BY category_position""".format(category=category_food)

    cursor.execute(query)
    return cursor.fetchall()
 

class Rank(object):
    def __init__(self, base_food_querys):
        self.foods = {}
        self.category_nutr = {}
        self.base_food = None
        self.base_food_querys = base_food_querys
        self.category_nutr = self.get_categories_nutr()

    def get_categories_nutr(self):
        category_nutr = {}
        for nutr_no, caution, avg, result_query in self.base_food_querys:
            category_nutr[nutr_no] = {"caution": caution, "data": {}, "avg": avg, "units": None}
            units = None
            for ndb_no, long_desc_es, nutr_val, units in result_query:
                category_nutr[nutr_no]["data"][ndb_no] = (nutr_val, long_desc_es)
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
                nutr_val, long_desc_es = self.category_nutr[nutr_no]["data"].get(ndb_no, ([0, self.foods.get(ndb_no, None)]))
                nutr_val = float(nutr_val)
                data[nutr_no].append((ndb_no, long_desc_es, nutr_val))
            data[nutr_no].sort(reverse=reverse, key=lambda x: x[2])
        return data

    def enumerateX(self, data):
        indice = 0
        # added extra tuple, because the last element in the list need to be evaluate
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
                # we evaluate if is 'caution' v[5]
                avg = self.category_nutr[nutr_no]["avg"]
                caution = self.category_nutr[nutr_no]["caution"]
                diff_avg = v[2] - avg if not caution else avg - v[2]
                positions[v[0]]["val"].append((v[2], diff_avg, self.category_nutr[nutr_no]["units"]))
        return sorted(positions.values(), key=lambda x: x["i"])

    def rank2natural(self, data):
        base = None
        index = 0
        for d in data:
            if base != d["i"]:
                base = d["i"]
                index += 1
            yield index, d
    
    def order(self):
        return self.rank2natural(self.sorted_data(self.ids2data_sorted()))

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
    

def query_build(nutr_no, category_food, name=None):
    attrs = {"nutr_no": nutr_no}
    if nutr_no.startswith("omega"):
        query = """
            SELECT food_des.ndb_no, food_des.long_desc_es||'#'||food_des.long_desc, {omega}, 'g'
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

    query = query.format(**attrs)
    return query

def best_of_general_2(category=None, name=None):
    _, cursor = conection()
    nutr = Food.get_matrix(PREPROCESSED_DATA_DIR + "nutavg.p")
    # hasheamos las llaves para mantener el orden
    nutr_avg = {nutr_no:(avg, caution) for nutr_no, nutr_desc, avg, _, caution in mark_caution_nutr(nutr)}

    querys_good = []
    querys_bad = []
    for nutr_no, (avg, caution) in nutr_avg.items():
        query = query_build(nutr_no, category)
        cursor.execute(query)
        if caution:
            querys_bad.append((nutr_no, caution, avg, cursor.fetchall()))
        else:
            querys_good.append((nutr_no, caution, avg, cursor.fetchall()))

    rank = Rank(querys_good)
    order_good = rank.order()
    rank = Rank(querys_bad)
    order_bad = rank.order()
    good = ((i, food["attr"][0], food["attr"][1]) for i, food in order_good)
    bad =  ((i, food["attr"][0], food["attr"][1]) for i, food in order_bad)

    total = {ndb_no: {"g": i, "name": name} for i, ndb_no, name in good}
        
    for i, ndb_no, name in bad:
        if ndb_no in total:
            total[ndb_no]["b"] = i
            total[ndb_no]["name"] = name
        else:
            total[ndb_no] = {"b": i, "name": name}

    results = [(v.get("g", 10000) + v.get("b", 0) * 5, ndb_no, v["name"], v.get("g", "-"), v.get("b", "-")) 
                for ndb_no, v in total.items()]
    results.sort()
    return results

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
        query = """SELECT category_position, global_position 
                    FROM ranking 
                    WHERE ndb_no = '{ndb_no}'""".format(ndb_no=self.ndb_no)
        cursor.execute(query)
        result = cursor.fetchall()
        if len(result) > 0:
            return {"global": result[0][1], "category": result[0][0]}
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
                #append the units with blank ''
                omegas = avg_omega()
                nutavg_vector = [e[1:] + [""] for e in sorted(avg_nutrients().values())] +\
                                zip(omegas._fields[:-1], sorted(OMEGAS.keys()), omegas[:-1], ['g'] * len(omegas[:-1]))
                self.save_matrix(PREPROCESSED_DATA_DIR + "nutavg.p", nutavg_vector)

            all_nutr, omegas = self.subs_omegas(nutavg_vector)
            omegas = filter(lambda x: x[1] is not None, ((key, omegas.get(key, None)) for key in self.omegas.keys()))
            self.nutr_avg = self.exclude_features(all_nutr)# + [(v[0], k, v[1], v[2]) for k, v in omegas]

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
        matrix = self.get_matrix(PREPROCESSED_DATA_DIR + 'matrix.p')
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

    def mark_caution_good_nutrients(self):
        #nutr_no, nutr, v, u, caution, good
        nutrients = self.mark_nutrients()
        return ((n[0], n[1], n[2], n[3], int((n[2] > avg[2]) and n[4]), int((n[2] > avg[2]) and not n[4])) 
            for n, avg in izip(nutrients, self.nutr_avg))

    def mark_nutrients(self):
        return mark_caution_nutr(self.nutrients)

    def caution_good_nutr_avg(self):
        good = len(filter(lambda x: x[5], self.mark_caution_good_nutrients()))
        bad = len(filter(lambda x: x[4], self.mark_caution_good_nutrients()))
        return {"total": len(self.nutrients),
            "good": good,
            "bad": bad}

