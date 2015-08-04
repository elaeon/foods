# -*- coding: utf-8 -*-

from utils import *

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

def test_recipe():
    from nutrientes.utils import MenuRecipe
    perfil = {"edad": 40, "unidad_edad": u"años", "genero": "H", "rnv_type": 1}
    recipe = MenuRecipe.ids2recipes([26], perfil).pop()
    food = recipe.recipe2food()
    #recipe.score_by_complete()
    #recipes = recipes_list(0, perfil, ordered="score")[:5]
    #menu = Recipe.merge(recipes, names=False)
    #print(menu.score)

def test_best():
    from nutrientes.utils import intake, best_of_query
    perfil = {"edad": 40, "unidad_edad": u"años", "genero": "H", "rnv_type": 1}
    perfil_intake = intake(
        perfil["edad"], 
        perfil["genero"], 
        perfil["unidad_edad"].encode("utf8", "replace"),
        perfil["rnv_type"])
    #nutrients = [n.nutr_no for n in perfil_intake.values()]
    nutrients = ['313', '431']
    rank = best_of_query(nutrients, None)
    for e in rank.order(limit=15):
        print(e[1]["attr"][1])
        print("*******")

def top_perfil_complex():
    import heapq
    from nutrientes.utils import Recipe, alimentos_category, intake
    scores = []
    intake_light_format = {
        "perfil": {"edad": 35, "genero": "H", "unidad_edad": u"años", "rnv_type":1}}
    features = Recipe.create_generic_features()
    perfil_intake = intake(
        intake_light_format["perfil"]["edad"], 
        intake_light_format["perfil"]["genero"], 
        intake_light_format["perfil"]["unidad_edad"].encode("utf8", "replace"), 
        intake_light_format["perfil"]["rnv_type"])
    for ndb_no in Food.alimentos(limit="limit 9000"):
        intake_light_format["foods"] = {ndb_no:100}
        recipe = Recipe.from_light_format(intake_light_format, perfil_intake=perfil_intake, features=features)
        #scores.append((recipe.score_best(), recipe.foods.values()[0].name))
        scores.append((recipe.score, recipe.foods.values()[0].name))
    print(heapq.nlargest(15, scores, key=lambda x: x))

if __name__ == '__main__':
    search_menu()
