def my_food_list(request):
    return {'my_food_list': request.session.get("intake_names_list", {})}
