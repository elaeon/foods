#from django.test import TestCase

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

def top():
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
    order.get_top("19042", level=40)
    #order.get_top("15184")
