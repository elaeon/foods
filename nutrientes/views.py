# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect
from django.http import HttpResponse

from nutrientes.utils import conection
from nutrientes.fuzzy_query import fuzzy_query

import json
import random

DB_VERSION = "9.1"

def perfil(some_func):
    def inner(*args, **kwargs):
        request = args[0]
        if "intake_perfil" in request.session:
            intake_params = request.session["intake_perfil"]
        else:
            intake_params = {"edad": 40, "unidad_edad": u"años", "genero": "H", "rnv_type": 1}
        kwargs["intake_params"] = intake_params
        return some_func(*args, **kwargs)
    return inner

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
        norm_avg_l = [(round((float(v)/float(max_value[0]))*30), category) 
            for v, category in avg_l if max_value[0] > 0]
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

        query = [fuzzy_query(DB_VERSION, term.strip(), ordering=False) for term in search_word.split(" ")]
        if len(query) > 1:
            query = " INTERSECT ".join(query) + "ORDER BY r, name ASC LIMIT 15"
        else:
            query = "".join(query) + "ORDER BY r, name ASC LIMIT 15"

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


@perfil
def food(request, ndb_no, intake_params={}):
    from nutrientes.utils import Food
    food = Food(ndb_no)
    food_compare = request.session.get("food_compare", {})
    recipe = food.food2recipe(intake_params)
    food_score = recipe.score
    resume_intake = recipe.resume_intake()
    return render(request, "food.html", {
        "food": food, 
        "food_compare": food_compare,
        "food_score": food_score,
        "resume_intake": resume_intake})


@perfil
def food_compare(request, intake_params):
    from nutrientes.utils import Food, intake
    from nutrientes.utils import Recipe
    from nutrientes.forms import PerfilIntakeForm, WeightForm
    from django.forms.formsets import formset_factory
    foods = []
    food_list = request.session.get("food_compare", {})
    if request.POST:
        if "analizar" in request.POST or "save" in request.POST:
            WeightFormSet = formset_factory(WeightForm, extra=0)
            if request.POST.get('edad', '') == '':
                intake_form = PerfilIntakeForm(initial=intake_params)
                foods = [{"food": Food(ndb_no, weight=float(100)), "weight": 100, "ndb_no": ndb_no} 
                        for ndb_no in food_list.keys()]
                formset = WeightFormSet(initial=foods)
                recipe = Recipe(
                    intake_params["edad"],
                    intake_params["genero"],
                    intake_params["unidad_edad"].encode("utf8", "replace"),
                    intake_params["rnv_type"])
            else:
                intake_form = PerfilIntakeForm(request.POST)
                formset = WeightFormSet(request.POST)
                if formset.is_valid():
                    for form in formset:
                        weight = form.cleaned_data["weight"]
                        ndb_no = form.cleaned_data["ndb_no"]
                        form.food = Food(ndb_no, weight=weight)

                if intake_form.is_valid():
                    recipe = Recipe(
                        intake_form.cleaned_data["edad"],
                        intake_form.cleaned_data["genero"],
                        intake_form.cleaned_data["unidad_edad"].encode("utf8", "replace"),
                        int(intake_form.cleaned_data["rnv_type"]))
                
            request.session["intake_perfil"] = recipe.perfil
            recipe.from_formset(formset)

            if "save" in request.POST:
                intake_list_name = request.POST["intake_list_name"]
                if intake_list_name != "":
                    try:
                        if type(request.session["intake_names_list"]) != type({}):
                            request.session["intake_names_list"] = {}
                    except KeyError:
                        request.session["intake_names_list"] = {}
                    recipe.name = intake_list_name
                    request.session["intake_names_list"][intake_list_name] = recipe.light_format()
                    request.session["food_compare"] = recipe.food2name()
            else:
                intake_list_name = request.POST.get("intake_list_name", "")

            return render(request, "analize_food.html", {
                "recipe": recipe,
                "intake_form": intake_form,
                "formset": formset,
                "intake_list_name": intake_list_name})
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

@perfil
def analyze_food(request, intake_params):
    from nutrientes.utils import Recipe, MenuRecipe
    from nutrientes.forms import PerfilIntakeForm, WeightForm
    from django.forms.formsets import formset_factory

    WeightFormSet = formset_factory(WeightForm, extra=0)
    foods = []
    intake_list_list = []
    if request.method == "POST":
        try:
            intake_list_names = request.POST.getlist("food_list")
            for intake_name in intake_list_names:
                intake_light_format = request.session["intake_names_list"][intake_name]
                recipe = Recipe.from_light_format(intake_light_format)
                foods += [{"food": food, "weight": food.weight, "ndb_no": food.ndb_no}
                            for food in recipe.foods.values()]
                intake_list_list.append(recipe)
        except KeyError:
            pass
    else:
        try:
            recipes_ids = [request.GET["recipe"]]
        except KeyError:
            return redirect("index")
        else:
            recipes = MenuRecipe.ids2recipes(recipes_ids, intake_params)
            intake_list_names = [recipes[0].name]
            for recipe in recipes:
                foods += [{"food": food, "weight": food.weight, "ndb_no": food.ndb_no}
                            for food in recipe.foods.values()]
            intake_list_list = recipes

    intake_form = PerfilIntakeForm(initial=intake_params)
    formset = WeightFormSet(initial=foods)
    recipe = Recipe.merge(intake_list_list)
    return render(request, "analize_food.html", {
        "recipe": recipe,
        "intake_form": intake_form,
        "formset": formset,
        "intake_list_name": "" if len(intake_list_names) > 1 else intake_list_names[0]})

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
        if "nutr_no" in request.GET:
            nutr_no = request.GET["nutr_no"]
            rank = best_of_query([nutr_no], None)
            nutrs = nutr_features_ids(rank.category_nutr.keys())
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
        query = fuzzy_query(DB_VERSION, term.encode("utf8", "replace"), headline=True)
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
    else:
        data_result = {}
    data_result["food_base"] = food_base
    return render(request, "equivalents.html", data_result)


@perfil
def recipes(request, intake_params):
    from nutrientes.utils import recipes_list
    recipes = recipes_list(10, intake_params, ordered="score")
    return render(request, "recipes.html", {"recipes": recipes})


def best_menu(request):
    from nutrientes.utils import recipes_list_users
    recipes = recipes_list_users(10)
    return render(request, "recipes_test.html", {"author_recipes": recipes})


@perfil
def analyze_menu(request, intake_params):
    from nutrientes.utils import MenuRecipe
    from nutrientes.forms import MenuRecipeForm
    from django.forms.formsets import formset_factory

    MenuRecipeFormSet = formset_factory(MenuRecipeForm, extra=0)
    if request.method == "POST":
        recipes_txt = request.POST.get("menu-recipes", "")
        recipes_ids = recipes_txt.split(",")
        menu_recipe = MenuRecipe(recipes_ids, intake_params)
        recipes = [{"weight": recipe.calc_weight(), "recipe": recipe_id, "name": recipe.name}
                        for recipe, recipe_id in zip(menu_recipe.recipes, recipes_ids)]
        formset = MenuRecipeFormSet(initial=recipes)
        return render(request, "analyze_menu.html", {
            "menu": menu_recipe, 
            "formset": formset})
    else:
        return redirect("index")


def share_recipe(request):
    from nutrientes.utils import Recipe
    if request.is_ajax():
        intake_list_name = request.POST.get("intake_list_name", "")
        author = request.POST.get("author", "").strip()
        try:
            intake_light_format = request.session["intake_names_list"][intake_list_name]
            perfil = intake_light_format["perfil"]
            intake_list = Recipe.from_light_format(intake_light_format)
            recipe_id = intake_list.save2db(intake_list_name, author)
            intake_list.save2bestperfil(recipe_id, perfil, author)
        except KeyError:
            result = "no key"
        else:
            result = "ok"
        return HttpResponse(json.dumps({"result": result}), content_type='text/json')


@perfil
def change_perfil(request, intake_params):
    from nutrientes.forms import PerfilIntakeForm
    from nutrientes.utils import intake, RNV_TYPE

    if request.method == "POST":
        intake_form = PerfilIntakeForm(request.POST)
        if intake_form.is_valid():
            request.session["intake_perfil"] = intake_form.export_perfil()
            intake_params = intake_form.export_perfil()
    else:
        intake_form = PerfilIntakeForm(initial=intake_params)

    nutrs_intake_usacan = intake(
        intake_params["edad"], 
        intake_params["genero"], 
        intake_params["unidad_edad"], 
        1)

    nutrs_intake_mx = intake(
        intake_params["edad"], 
        intake_params["genero"], 
        intake_params["unidad_edad"], 
        2)

    nutrs = {"Folic acid": ["Folate, DFE [Folate food, Folic acid]", "X"]}
    for nutrdesc in nutrs_intake_usacan:
        nutrs[nutrdesc] = [nutrdesc, "X"]

    for nutrdesc in nutrs_intake_mx:
        nutrs.setdefault(nutrdesc, ["X", nutrdesc])
        nutrs[nutrdesc][1] = nutrdesc

    return render(request, "change_perfil.html", {
        "intake_form": intake_form, 
        "nutrs_intake": sorted(nutrs.values(), key=lambda x: x[0] if x[0] != "X" else x[1]),
        "normas": RNV_TYPE.items()})


@perfil
def complex_intake_nutrients(request, intake_params):
    from nutrientes.utils import lower_essencial_nutrients
    data = lower_essencial_nutrients(intake_params)
    return render(request, "complex_intake_nutrients.html", {"data": data})
