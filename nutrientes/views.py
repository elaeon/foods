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
    width_img_rand = random.uniform(0, 100) #0 to 100%
    height_img_rand = random.uniform(0, 100) #0 to 100%
        
    if request.method == "GET" and "table_type" in request.GET:
        if request.GET["table_type"] == "perfil":
            from nutrientes.utils import category_food_list_perfil
            category_food_list = category_food_list_perfil()
            table_type = "perfil"
    else:
        from nutrientes.utils import category_food_list
        category_food_list = category_food_list()
        table_type = "avg"

    return render(request, "index.html", {
        "category_food": category_food_list, 
        "width_img_rand": width_img_rand,
        "height_img_rand": height_img_rand,
        "table_type": table_type})


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
    from nutrientes.utils import categories_foods
    from nutrientes.utils import principal_nutrients_avg_percentaje
    from nutrientes.utils import principal_nutrients_percentaje

    data = []
    limit = 10
    all_food_avg = {nutrdesc: v for v, nutrdesc in principal_nutrients_percentaje()}
    for category, category_des in categories_foods():
        percentaje_data = principal_nutrients_avg_percentaje(category, all_food_avg=all_food_avg)
        for _, val, nutr in percentaje_data[:limit]:
            data.append((category_des, val, nutr))
    return render(request, "principal_nutr_category.html", {"data": data, "limit": limit})


def nutrient_selection(request):
    from collections import defaultdict
    from nutrientes.utils import nutr_features_group, categories_foods, Food

    features = nutr_features_group(order_by="nutrdesc")
    fields, omegas = Food.subs_omegas([(e[0], e[1], 0, e[2]+"#"+unicode(e[3])) for e in features])
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
                "value": long_desc_es,
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
            nutr = []
            if len(food_list.keys()) >= 2:
                from nutrientes.utils import Food
                for ndb_no in food_list.keys():
                    foods.append(Food(ndb_no))
                for food in foods:
                    dicts.append({v[0]: v for v in food.nutrients})
                    names.append(food.name)
                common_table = create_common_table(dicts)
                if len(food_list) == 2:
                    from nutrientes.utils import ExamineFoodVariants
                    v = ExamineFoodVariants()
                    data = []
                    for k, v in v.evaluate_inc_dec(lambda: [food_list.keys()], ndb_no=food_list.keys()[0]).items():
                        if v[0] == 0 and v[1] == 0 and v[2] == 0:
                            pass
                        else:
                            data.append((k, v))
                    nutr = sorted(data, key=lambda x: x[1])
            return render(request, "compare_food.html", 
                {"foods": foods, "common_table": common_table, "names": names, "nutr": nutr})
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


@perfil
def list_food_category(request, category_id, order, intake_params={}):
    from nutrientes.utils import alimentos_category_name, get_range
    from nutrientes.utils import alfabetic_food, ranking_nutr_perfil
    from nutrientes.utils import ExamineFoodVariants, principal_nutrients_avg_percentaje
    from nutrientes.utils import principal_nutrients_percentaje

    categoria = alimentos_category_name(category_id)[0][0]
    if order == u"perfil":
        edad_range = get_range(intake_params["edad"], intake_params["unidad_edad"])
        foods = ranking_nutr_perfil(intake_params, edad_range, category_food=category_id)
    else:
        foods = alfabetic_food(category_food=category_id)

    food_variants = ExamineFoodVariants()
    types_variants = []
    for i, (variants, resumen_text) in enumerate(food_variants.category(category_id)):
        variants_esp = [(k, v[1], "incremento") for k, v in variants if v[0] >= 50]
        variants_esp.extend([(k, v[2], "decremento") for k, v in variants if v[0] < 50 and v[2] < 0])
        types_variants.append((i, variants_esp, resumen_text))

    all_food_avg = {nutrdesc: v for v, nutrdesc in principal_nutrients_percentaje()}
    return render(request, "food_category.html", {
        "variants": types_variants,
        "foods": foods, 
        "categoria": categoria, 
        "order": order, 
        "best_nutr": principal_nutrients_avg_percentaje(category_id, all_food_avg)[:20],
        "category_id": category_id})


def best_of_nutrients(request):
    from nutrientes.utils import nutr_features_ids, alimentos_category_name
    from nutrientes.utils import best_of_query

    if request.method == "POST":
        nutr_nos = request.POST.getlist("nutr_no")
        category_food = request.POST.get("category_food", 'X')

        if category_food == "X":
            exclude = "processed_food"
            category_food = None
        elif category_food == "XX":
            category_food = None
            exclude = None
        else:
            category_food = category_food
            exclude = None
            
        rank = best_of_query(nutr_nos, category_food, exclude=exclude)
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


@perfil
def ranking_list(request, order, intake_params={}):
    from nutrientes.utils import ranking_nutr, get_range, ranking_nutr_perfil
    if order == u"perfil":
        edad_range = get_range(intake_params["edad"], intake_params["unidad_edad"])
        foods = ranking_nutr_perfil(intake_params, edad_range)
    else:
        foods = ranking_nutr()
    return render(request, "ranking_list.html", {
        "foods": foods,
        "order": order})


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
    #from nutrientes.utils import MostSimilarFood, nutr_features_ids, get_many_food
    #similar_food = MostSimilarFood(ndb_no, "1100")
    #food_base = similar_food.food_base
    #results = similar_food.search()
    #if results is not None and len(results) > 0:
    #    last_result = results.pop()
    #    data_result = last_result.ids2name(similar_food)
    #else:
    #    data_result = {}
    #data_result["food_base"] = food_base
    return render(request, "equivalents.html", {})
    #pass


@perfil
def recipes(request, intake_params):
    from nutrientes.utils import recipes_list
    recipes = recipes_list(5, intake_params, ordered="score")
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

    nutrs = {"Folic acid": ["X", "X"]} #Folate, DFE [Folate food, Folic acid]
    for nutrdesc, nutr in nutrs_intake_usacan.items():
        nutrs[nutrdesc] = [nutr, "X"]

    for nutrdesc, nutr in nutrs_intake_mx.items():
        nutrs.setdefault(nutrdesc, ["X", None])
        nutrs[nutrdesc][1] = nutr

    print(nutrs.values())
    return render(request, "change_perfil.html", {
        "intake_form": intake_form, 
        "nutrs_intake": sorted(nutrs.values(), key=lambda x: x[0].nutrdesc if x[0] != "X" else x[1]),
        "normas": RNV_TYPE.items()})


@perfil
def complex_intake_nutrients(request, intake_params):
    from nutrientes.utils import lower_essencial_nutrients
    data = lower_essencial_nutrients(intake_params)
    return render(request, "complex_intake_nutrients.html", {"data": data})


def news(request):
    from news.models import News
    latest_news = News.objects.latest("date_pub")
    return render(request, "news.html", {"latest_news": latest_news})


def recomended_food(request):
    from nutrientes.utils import OptionSearch, Food
    from nutrientes.forms import CategoryForm, WeightFoodForm, OmegaRadioForm
    from django.forms.formsets import formset_factory

    CategoryFormSet = formset_factory(CategoryForm, extra=0)
    WeightFoodFormSet = formset_factory(WeightFoodForm, extra=0)
    search = OptionSearch()
    initial_w = [{'key': k, 'name': k} for k in sorted(search.weights)]
    initial = [{'key': k, 'food_type': v} 
            for k, v in sorted(search.foods.items(), key=lambda x: x[1].category)]

    def basic_state():
        type_food_formset = CategoryFormSet(initial=initial, prefix='type_food')
        weight_formset = WeightFoodFormSet(initial=initial_w, prefix='weight')
        radio_omega_form = OmegaRadioForm({"radio_omega": True, "quantity": "0.1"})
        foods_dict = {}
        for _, food_type in search.foods.items():
            for ndb_no in food_type.foods:
                foods_dict.setdefault(food_type.category, [])
                foods_dict[food_type.category].append(Food(ndb_no, avg=False))
        for k, v in foods_dict.items():
            v.sort(key=lambda x: x.img_obj().name if x.img_obj() is not None else "")

        return render(request, "recommended_food_intro.html", {
            "foods": sorted(foods_dict.items(), key=lambda x:x[0]),
            "weight_formset": weight_formset,
            "total_food": search.total_food,
            "type_food_formset": type_food_formset,
            "radio_omega_form": radio_omega_form})

    if request.method == "POST":
        type_food_formset = CategoryFormSet(request.POST, initial=initial, prefix='type_food')
        weight_formset = WeightFoodFormSet(request.POST, initial=initial_w, prefix='weight')
        radio_omega_form = OmegaRadioForm(request.POST)
        if type_food_formset.is_valid() and weight_formset.is_valid() and radio_omega_form.is_valid():
            radio_o = radio_omega_form.cleaned_data["radio_omega"]
            limit = int(radio_omega_form.cleaned_data["data_size"])
            type_food_raw = [form.cleaned_data["key"] 
                for form in type_food_formset.forms if form.cleaned_data["check"]]
            weight_avg_nutr = float(radio_omega_form.cleaned_data["quantity"])
            if len(type_food_raw) > 0:
                best_for = [form.cleaned_data["key"] 
                    for form in weight_formset.forms if form.cleaned_data["check"]]
                best_for_text = ", ".join(best_for)
                foods = search.best(
                    type_food_raw, 
                    weights_for=best_for, 
                    limit=limit, 
                    radio_o=radio_o, 
                    weight_avg_nutr=weight_avg_nutr)
                return render(request, "recommended_food.html", {
                    "foods": foods,
                    "weight_formset": weight_formset,
                    "type_food_formset": type_food_formset,
                    "best_for_text": best_for_text,
                    "radio_omega_form": radio_omega_form})
            else:
                return basic_state()
    else:
        return basic_state()
