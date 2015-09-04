# -*- coding: utf-8 -*-
import pandas as pd

df = pd.read_csv(filepath_or_buffer="encuesta_alimentos_alumnos2.csv")

columns = [#"¿Conoce los nutrientes escenciales para que el cuerpo tenga un funcionamiento adecuado?",
#"¿Cuál de los siguientes nutrientes concidera que consume más?",
#"Considero que mi alimentación ___________ satisface mi actividad física diaria.",
#"Considero que mi alimentación ___________ cubre los nutrientes escenciales",
#"Entre semana ¿cuántas veces al dia come platillos preparados en casa?",
#"Los fines de semana ¿cuántas veces al dia come platillos preparados en casa?",
"Huevo o lácteos",
"Café o té descafeinados",
"Café o té con cafeina",
"Refrescos o bebidas endulzadas",
"Refrescos bajos en calorias",
"Carne de res",
"Carne de pollo",
"Carne de cerdo",
"Pescados o mariscos",
"Nueces y semillas",
"Frutas",
"Verduras",
"Legumbres",
"Cereales o pastas",
"Dulces",
"Salchichas o carnes frias",
"Pan dulce",
"Suplementos alimenticios"]#,
#"Considera que llevar una alimentación saludable es:"]

calif = {
    "Regulamente consumo": .8, 
    "Lo que más consumo": 1, 
    "Muy poco": .4, 
    "Raras veces": .1, 
    "Nada": 0
}

#for column in columns:
#    print("*********", column)
#    df_g = df[[column]].groupby([column])
#    order = sorted(df_g.groups.items(), key=lambda x:len(x[1]), reverse=True)
#    for k,v in order:
#        print(k, len(v), calif.get(k, ""))

def resume():
    data = []
    for column in columns:
        #print("*********", column)
        df_g = df[[column]].groupby([column])
        #order = sorted(df_g.groups.items(), key=lambda x:len(x[1]), reverse=True)
        count = 0
        for k,v in df_g.groups.items():
            count += len(v) * calif.get(k, "")
        data.append((column, count/4))
    return sorted(data, key=lambda x:x[1], reverse=True)

def transform():
    matrix = df.loc[:,columns]
    matrix = matrix.dropna(subset=columns)
    for column in columns:
        for k, v in calif.items():
            matrix[column].loc[matrix[column] == k] = v
    matrix.to_csv(path_or_buf="encuesta_alimentos_alumnos_vector.csv", index=False)

if __name__ == '__main__':
    print(resume())
    #transform()
