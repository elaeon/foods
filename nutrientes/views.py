from django.shortcuts import render
from django.http import HttpResponse

from nutrientes.utils import conection
import json

# Create your views here.
def index(request):
    from nutrientes.utils import category_food_list, nutr_features, Food
    
    features = nutr_features()
    fields, omegas = Food.subs_omegas([(e[0], e[1], 0, None) for e in features])
    nutr = fields + [(v[0], k, v[1], v[2]) for k, v in omegas.items()]
    return render(request, "index.html", {"category_food": category_food_list(), "nutr": nutr})


def ajax_search(request):
    if request.is_ajax():
        conn, cursor = conection()
        search_word = request.GET.get("query", "")
        query = """SELECT ndb_no, long_desc_es FROM food_des WHERE long_desc_es IS NOT NULL AND long_desc_es ilike '%{term}%' LIMIT 10;""".format(term=search_word)
        cursor.execute(query)
        records = cursor.fetchall()
        suggestions = []    
        for ndb_no, long_desc_es in records:
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


def list_food_category(request, category_id):
    from nutrientes.utils import alimentos_category, alimentos_category_name
    foods = alimentos_category(category=category_id, limit="limit 9000")
    categoria = alimentos_category_name(category_id)[0][0]
    return render(request, "food_category.html", {"foods": foods, "categoria": categoria})


def best_of_nutrients(request):
    from nutrientes.utils import best_of

    if request.method == "POST":
        print request.POST
        foods = best_of(request.POST["nutr_no"])
    else:
        foods = []
    categoria = ""
    return render(request, "food_category.html", {"foods": foods, "categoria": categoria})
