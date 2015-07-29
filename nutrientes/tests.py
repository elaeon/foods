# -*- coding: utf-8 -*-

from nutrientes.utils import *

def equivalents():
    ndb_no = "11625" #09326
    similar_food = MostSimilarFood(ndb_no, "1100")
    food_base = similar_food.food_base
    for x in range(10):
        results = similar_food.search()
        if results is not None and len(results) > 0:
            last_result = results.pop()
            print(last_result.total)
            print(last_result.result)
            #print last_result.ids2name(similar_food)["foods"]


def nearest_neighbors():
    ndb_no = "11667"
    if 1: 
        food = Food(ndb_no, avg=False)
        print(list(food.similarity()))
    else:
        from sklearn.neighbors import KDTree, BallTree
        import numpy as np
        matrix = MatrixNutr(name=PREPROCESSED_DATA_DIR + 'matrix.csv')
        matrix_dict = matrix.to_dict()
        X = np.array([row[1] for row in matrix.rows])
        #kdt = KDTree(X, leaf_size=30, metric='euclidean')
        kdt = BallTree(X, leaf_size=300, metric='euclidean')
        m = np.array(matrix_dict[ndb_no])
        dist, ind = kdt.query(m, k=15)
        print(ind)
        print([matrix.rows[i][0] for i in ind[0]])
        #print dist
        #print matrix.rows[4458]

def boost():
    import os
    import csv
    PREPROCESSED_DATA_DIR = os.path.dirname(os.path.dirname(__file__)) + '/preprocessed_data/'
    with open(PREPROCESSED_DATA_DIR+"order_matrix.csv", 'rb') as csvfile:
        data_list = []
        csvreader = csv.reader(csvfile, delimiter=',',
                        quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in csvreader:
            data_list.append({"ndb_no": row[0], "category": row[1]})

    order = OrderSimilarity(data_list)
    print(order.get_top("19042", level=40))
    #order.get_top("15184")

def top_perfil():
    #select long_desc,amount,msre_desc,gm_wgt from food_des,weight where food_des.ndb_no=weight.ndb_no and food_des.ndb_no='11529';
    import heapq
    from nutrientes.utils import Recipe, alimentos_category
    scores = []
    intake_light_format = {
        "perfil": {"edad": 35, "genero": "H", "unidad_edad": u"años", "rnv_type":1}}
    for ndb_no in Food.alimentos(limit="limit 9000"):
        intake_light_format["foods"] = {ndb_no:100}
        recipe = Recipe.from_light_format(intake_light_format)
        scores.append((recipe.score, recipe.foods.values()[0].name))
    print(heapq.nlargest(15, scores, key=lambda x: x))

def test_recipes_list():
    from nutrientes.utils import recipes_list
    recipes = recipes_list(10, {"edad": 35, "genero": "H", "unidad_edad": u"años"})
    print(recipes)


def test_back():
    from itertools import combinations_with_replacement
    rows = [['a', [0.5, 0.3, 0.4]], ['b', [0.4, 0.1, 0.8]], ['c', [0.1, 0.3, 0.4]], ['d', [0.4, 0.1, 0.9]]]
    base = [10.8, 11.2, 11.6]
    for i in range(2, 10):
        for row in combinations_with_replacement(rows, i):
            total = [sum(ab) for ab in zip(*[elem[1] for elem in row])]
            if all([t >= b for t, b in zip(total, base)]):
                print row
