# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect
from django.http import HttpResponse

from nutrientes.utils import conection
from nutrientes.fuzzy_query import fuzzy_query

import json
import random

DB_VERSION = "9.1"


def index(request):
    from nutrientes.utils import category_food_list
    
    width_img_rand = random.uniform(0, 100) #0 to 100%
    height_img_rand = random.uniform(0, 100) #0 to 100%
    
    return render(request, "index.html", {
        "category_food": category_food_list(), 
        "width_img_rand": width_img_rand,
        "height_img_rand": height_img_rand})


def graph_all_nutr(request):
    from nutrientes.utils import avg_nutrients_group_nutr, nutr_features
    from nutrientes.utils import Food, avg_nutrients_group_omega
    avg_nutr = []
    fields, _ = Food.subs_omegas([(e[0], e[1], 0, None) for e in nutr_features()])
    for nutr_no, name, _, _ in fields:
        avg_l = [(v, category) for category, v in avg_nutrients_group_nutr(nutr_no)]
        max_value = max(avg_l)
        norm_avg_l = [(round((float(v)/float(max_value[0]))*30), category) for v, category in avg_l]
        avg_nutr.append(("%s-%s" % (name, nutr_no), norm_avg_l))

    group = {"omega 3": [], "omega 6": [], "omega 7": [], "omega 9": [], "omega6:omega3": []}
    for category, omega3, omega6, omega7, omega9, radio in avg_nutrients_group_omega():
        group["omega 3"].append((omega3, category))
        group["omega 6"].append((omega6, category)) 
        group["omega 7"].append((omega7, category))
        group["omega 9"].append((omega9, category)) 
        group["omega6:omega3"].append((radio, category))
 
    for nutr_no, avg_l in group.items():
        max_value = max(avg_l, key=lambda x: x[0])
        norm_avg_l = [(round((float(v)/float(max_value[0]))*30), category) for v, category in avg_l if max_value[0] > 0]
        avg_nutr.append((nutr_no, norm_avg_l))

    return render(request, "graph_all_nutr.html", {"avg_nutr": avg_nutr})


def principal_nutrients_graph(request):
    from nutrientes.utils import principal_nutrients, Food, categories_foods
    
    data = []
    for category, category_des in categories_foods():
        features, omegas = Food.subs_omegas(
            [(e[0], e[0], e[1], None) 
            for e in principal_nutrients(category=category)])
        all_nutr = features + [(omega, omega, v, u) for omega, v, u in omegas.values()]
        sorted_data = sorted(all_nutr, key=lambda x: x[2], reverse=True)
        maximo = sum((d[2] for d in sorted_data))
        porcentaje_data = [(round(d[2]*100./maximo, 3), d[0]) for d in sorted_data]
        for val, nutr in porcentaje_data[:10]:
            data.append((category_des, val, nutr))
    return render(request, "principal_nutr_category.html", {"data": data})


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

        query = [fuzzy_query(DB_VERSION, term, ordering=False) for term in search_word.split(" ")]
        if len(query) > 1:
            query = " INTERSECT ".join(query) + "ORDER BY r DESC LIMIT 15"
        else:
            query = "".join(query) + "ORDER BY r DESC LIMIT 15"

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
    from nutrientes.utils import Food, ranking_nutr_detail, category_food_count
    food = Food(ndb_no)
    food_compare = request.session.get("food_compare", {})
    tabla_nutr_rank = food.ranking_nutr_detail_base("global")
    tabla_nutr_rank_f = []
    global_values = [("info", 500), ("success", 2000), ("warning", 5000)]
    for nutr, val, val_fmt in tabla_nutr_rank:
        for k, v in global_values:
            if val < v:
                type_ = k
                break
        else:
            type_ = "danger"
        tabla_nutr_rank_f.append((nutr, val_fmt, type_))
    #category_total = category_food_count(food.group["id"])[0]
    return render(request, "food.html", {
        "food": food, 
        "food_compare": food_compare,
        "tabla_nutr_rank": tabla_nutr_rank_f})


def food_compare(request):
    from nutrientes.utils import Food, intake
    from nutrientes.utils import IntakeList
    from nutrientes.forms import IntakeForm, WeightForm
    from django.forms.formsets import formset_factory
    foods = []
    food_list = request.session.get("food_compare", {})
    if request.POST:
        if "analizar" in request.POST or "save" in request.POST:
            WeightFormSet = formset_factory(WeightForm, extra=0)
            if request.POST.get('edad', '') == '':
                if "intake_perfil" in request.session:
                    intake_params = request.session["intake_perfil"]
                else:
                    intake_params = {"edad": 40, "unidad_edad": u"años", "genero": "H"}

                intake_form = IntakeForm(initial=intake_params)
                foods = [{"food": Food(ndb_no, weight=float(100)), "weight": 100, "ndb_no": ndb_no} 
                        for ndb_no in food_list.keys()]
                formset = WeightFormSet(initial=foods)
                intake_list = IntakeList(
                    intake_params["edad"],
                    intake_params["genero"],
                    intake_params["unidad_edad"].encode("utf8", "replace"))
            else:
                intake_form = IntakeForm(request.POST)
                formset = WeightFormSet(request.POST)
                if formset.is_valid():
                    for form in formset:
                        weight = form.cleaned_data["weight"]
                        ndb_no = form.cleaned_data["ndb_no"]
                        form.food = Food(ndb_no, weight=weight)

                if intake_form.is_valid():
                    intake_list = IntakeList(
                        intake_form.cleaned_data["edad"],
                        intake_form.cleaned_data["genero"],
                        intake_form.cleaned_data["unidad_edad"].encode("utf8", "replace"))
                
            request.session["intake_perfil"] = intake_list.perfil
            intake_list.from_formset(formset)
            score, resume_intake = intake_list.score()

            if "save" in request.POST:
                intake_name_list = request.POST["intake_list_name"]
                try:
                    if type(request.session["intake_names_list"]) != type({}):
                        request.session["intake_names_list"] = {}
                except KeyError:
                    request.session["intake_names_list"] = {}

                request.session["intake_names_list"][intake_name_list] = intake_list.light_format()
                request.session["food_compare"] = intake_list.food2name()
            else:
                intake_name_list = request.POST.get("intake_list_name", "")

            return render(request, "analize_food.html", {
                "total_food": intake_list.total_nutr_names, 
                "intake": intake_list.perfil_intake,
                "intake_form": intake_form,
                "formset": formset,
                "type_intake": resume_intake,
                "score": score,
                "energy": intake_list.total_nutr_names.get("Energy", 0),
                "radio_omega": intake_list.radio_omega,
                "principals": intake_list.principals_nutrients(),
                "total_weight": intake_list.calc_weight(),
                "intake_name_list": intake_name_list})
        elif "export" in request.POST:
            intake_list_name = request.POST.get("intake_list_name", "")
            intake_light_format = request.session["intake_names_list"][intake_list_name]
            return HttpResponse(json.dumps(intake_light_format), content_type='text/json')
        elif "borrar" in request.POST:
            name = request.POST.get("intake_list_name", None)
            if name is not None:
                del request.session["intake_names_list"][name]
                request.session["intake_names_list"] = request.session["intake_names_list"]
            return redirect("index")
        else:
            from nutrientes.utils import create_common_table
            dicts = []
            names = []
            if len(food_list.keys()) >= 2:
                from nutrientes.utils import Food
                for ndb_no in food_list.keys():
                    foods.append(Food(ndb_no))
                for food in foods:
                    dicts.append({v[0]: v for v in food.nutrients})
                    names.append(food.name)
                common_table = create_common_table(dicts)
            return render(request, "compare_food.html", 
                {"foods": foods, "common_table": common_table, "names": names})
    else:
        return redirect("index")

def analyze_food(request):
    from nutrientes.utils import IntakeList
    from nutrientes.forms import IntakeForm, WeightForm
    from django.forms.formsets import formset_factory
    if request.method == "POST":
        try:
            WeightFormSet = formset_factory(WeightForm, extra=0)
            foods = []
            intake_list_list = []
            intake_names_list = request.POST.getlist("food_list")
            for intake_list_name in intake_names_list:
                intake_light_format = request.session["intake_names_list"][intake_list_name]
                intake_list = IntakeList.from_light_format(intake_light_format)
                foods += [{"food": food, "weight": food.weight, "ndb_no": food.ndb_no}
                            for food in intake_list.foods.values()]
                intake_list_list.append(intake_list)
            intake_params = intake_light_format["perfil"]
            intake_form = IntakeForm(initial=intake_params)
            formset = WeightFormSet(initial=foods)
            intake_list = IntakeList.merge(*intake_list_list)
            score, resume_intake = intake_list.score()
            return render(request, "analize_food.html", {
                "total_food": intake_list.total_nutr_names, 
                "intake": intake_list.perfil_intake,
                "intake_form": intake_form,
                "formset": formset,
                "type_intake": resume_intake,
                "score": score,
                "energy": intake_list.total_nutr_names.get("Energy", 0),
                "radio_omega": intake_list.radio_omega,
                "principals": intake_list.principals_nutrients(),
                "total_weight": intake_list.calc_weight(),
                "intake_name_list": "" if len(intake_names_list) > 1 else intake_names_list[0]})
        except KeyError:
            pass

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
                #if len(food_compare.keys()) >= 3:
                #food_compare.pop(food_compare.keys()[0], 0)
                name = Food.get_food(ndb_no)[0][0]
                food_compare[ndb_no] = name
                request.session["food_compare"] = food_compare
    return HttpResponse(name, content_type='text/plain')


def list_food_category(request, category_id, order):
    from nutrientes.utils import alimentos_category, alimentos_category_name
    from nutrientes.utils import ranking_nutr

    categoria = alimentos_category_name(category_id)[0][0]
    if order == u"alfanumeric":
        foods = alimentos_category(category=category_id, limit="limit 9000")        
    else:
        foods = ranking_nutr(category_food=category_id)

    return render(request, "food_category.html", {
        "foods": foods, 
        "categoria": categoria, 
        "order": order, 
        "category_id": category_id})


def best_of_nutrients(request):
    from nutrientes.utils import nutr_features_ids, alimentos_category_name
    from nutrientes.utils import best_of_query

    if request.method == "POST":
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
        return redirect("index")
    return render(request, "food_attr_check.html", {
        "foods": rank.order(),
        "categoria": categoria, 
        "nutrs": nutrs})


def about(request):
    return render(request, "about.html", {})


def contact(request):
    return render(request, "contact.html", {})


def ranking_list(request):
    from utils import ranking_nutr
    foods = ranking_nutr()
    return render(request, "ranking_list.html", {
        "foods": foods})


def result_long_search(request):
    if request.method == "POST":
        conn, cursor = conection()
        term = request.POST.get("text-input", "").strip()
        query = fuzzy_query(DB_VERSION, term, headline=True)
        cursor.execute(query)
        foods = cursor.fetchall()
        conn.close()
    return render(request, "result_search.html", {
        "foods": foods})


def equivalents(request, ndb_no):
    from nutrientes.utils import MostSimilarFood, nutr_features_ids, get_many_food
    similar_food = MostSimilarFood(ndb_no, "1100")
    food_base = similar_food.food_base
    results = similar_food.search()
    if results is not None and len(results) > 0:
        last_result = results.pop()
        data_result = last_result.ids2name(similar_food)
        data_result["food_base"] = food_base
    return render(request, "equivalents.html", data_result)

