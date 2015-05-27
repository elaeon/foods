from django.shortcuts import render
from django.http import HttpResponse

from nutrientes.utils import conection
import json
import random

# Create your views here.
def index(request):
    from nutrientes.utils import category_food_list
    
    width_img_rand = random.uniform(0, 60)
    height_img_rand = random.uniform(70, 100)
    return render(request, "index.html", {
        "category_food": category_food_list(), 
        "width_img_rand": width_img_rand,
        "height_img_rand": height_img_rand})


def nutrient_selection(request):
    from collections import defaultdict
    from nutrientes.utils import nutr_features_group, categories_foods, Food

    features = nutr_features_group(order_by="nutrdesc")
    fields, omegas = Food.subs_omegas([(e[0], e[1], 0, e[2]+"#"+str(e[3])) for e in features])
    nutr = fields + [(v[0], k, v[1], v[2]) for k, v in omegas.items()]
    categories = categories_foods()
    
    nutr_group = defaultdict(list)
    for nutr_no, name, _, group_and_desc in nutr:
        group_name, desc = group_and_desc.split("#")
        nutr_group[group_name].append((nutr_no, name, desc))

    nutr_group_order = sorted(nutr_group.items())
    return render(request, "nutrient_selection.html", {
        "nutr_group": nutr_group_order, 
        "categories": categories})


def ajax_search(request):
    if request.is_ajax():
        conn, cursor = conection()
        search_word = request.GET.get("query", "").strip()
        #search_word = " & ".join(search_word.split(" "))
        #query = """SELECT ndb_no, long_desc_es FROM food_des WHERE long_desc_es IS NOT NULL AND long_desc_es ilike '%{term}%' LIMIT 10;""".format(term=search_word)

        query = []
        for term in search_word.split(" "):
            query.append("""
                (SELECT searchall_index.ndb_no, searchall_index.long_desc_es, ts_rank_cd(document, query) as r FROM 
                (SELECT word
                    FROM unique_lexeme
                    WHERE  word <-> '{term}' < 1
                    ORDER BY word <-> '{term}' LIMIT 2) as words, searchall_index, to_tsquery('spanish', words.word) as query
                WHERE document @@ query)
            """.format(term=term))
        if len(query) > 1:
            query = " INTERSECT ".join(query) + "ORDER BY r DESC LIMIT 15"
        else:
            query = "".join(query) + "ORDER BY long_desc_es ASC LIMIT 15"
        #print query
        cursor.execute(query)
        records = cursor.fetchall()
        suggestions = []    
        for ndb_no, long_desc_es, _ in records:
            suggestions.append({
                "value": long_desc_es.decode("utf8", "replace") ,
                "data": {
                    "id": ndb_no,
                    "category": ""}})
        params = {
             'query': search_word,
             'suggestions': suggestions,
        }
        conn.close()
        return HttpResponse(json.dumps(params), content_type='text/json')


def food(request, ndb_no):
    from nutrientes.utils import Food
    food = Food(ndb_no)
    food_compare = request.session.get("food_compare", {})
    return render(request, "food.html", {"food": food, "food_compare": food_compare})


def food_compare(request):
    food_compare = request.session.get("food_compare", {})
    foods = []
    if len(food_compare.keys()) >= 2:
        from nutrientes.utils import Food
        for ndb_no in food_compare.keys():
            foods.append(Food(ndb_no, avg=False))

    return render(request, "compare_food.html", {"foods": foods})


def romega(request):
    from nutrientes.utils import get_omegas
    romegas = get_omegas()
    return render(request, "romegas.html", {"romegas": romegas})


def set_comparation(request, ndb_no, operation):
    from nutrientes.utils import Food
    if request.is_ajax():
        food_compare = request.session.get("food_compare", {})
        name = ""
        if operation == "delete":
            food_compare.pop(ndb_no, 0)
            name = ndb_no
            request.session["food_compare"] = food_compare
        else:
            if not ndb_no in food_compare:
                if len(food_compare.keys()) >= 3:
                    food_compare.pop(food_compare.keys()[0], 0)
                name = Food.get_food(ndb_no)[0][0]
                food_compare[ndb_no] = name
                request.session["food_compare"] = food_compare
    return HttpResponse(name, content_type='text/plain')


def list_food_category(request, category_id, order):
    from nutrientes.utils import alimentos_category, alimentos_category_name
    from nutrientes.utils import best_of_general_2

    categoria = alimentos_category_name(category_id)[0][0]
    if order == u"alfanumeric":
        foods = alimentos_category(category=category_id, limit="limit 9000")        
    else:
        foods = best_of_general_2(category_id)

    return render(request, "food_category.html", {
        "foods": foods, 
        "categoria": categoria, 
        "order": order, 
        "category_id": category_id})


def best_of_nutrients(request):
    from nutrientes.utils import nutr_features_ids, alimentos_category_name
    from nutrientes.utils import best_of_query

    if request.method == "POST":
        #print request.POST
        nutr_nos = request.POST.getlist("nutr_no")
        category_food = request.POST.get("category_food", '0')
        category_food = None if category_food == '0' else category_food
        rank = best_of_query(nutr_nos, category_food)
        nutrs = nutr_features_ids(rank.category_nutr.keys())
        try:
            categoria = alimentos_category_name(category_food)[0][0]
        except IndexError:
            categoria = ""
    else:
        foods = []
        categoria = ""
        nutrs = []
    return render(request, "food_attr_check.html", {
        "foods": rank.order(),
        "categoria": categoria, 
        "nutrs": nutrs})

def about(request):
    return render(request, "about.html", {})
