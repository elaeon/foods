from nutrientes.utils import RNV_TYPE

def my_food_list(request):
    genero = {"H": "Hombre", "M": "Mujer",  "pregnancy": "Embarazo", "lactation": "Lactancia"}
    perfil = request.session.get("intake_perfil", {})
    perfil["rnv_type_txt"] = RNV_TYPE[int(perfil.get("rnv_type", "1"))]
    perfil["genero_txt"] = genero[perfil.get("genero", "H")]
    return {
        'my_food_list': request.session.get("intake_names_list", {}),
        'perfil': perfil
    }
