
def load_csv_mortality():
    import csv
    with open("/home/agmartinez/Escritorio/mortalidad_inegi.csv", 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in reader:
            header = row
            break
        years = header[2:]
        data = []
        for row in reader:
            element = {}
            element["clave"] = row[0]
            element["description"] = row[1]
            #for year in years:
            element["years"] = zip(years, row[2:])
            data.append(element)

    return data

def csv2json(path, items):
    import csv
    import json
    with open(path, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        data = []
        for row in reader:
            data.append(dict(zip(items, row)))
        data_json = json.dumps(data)

    n_path = path.split("/")
    filename = n_path.pop()
    nfilename = filename.split(".")
    nfilename.pop()
    json_filename = ".".join(nfilename) + ".json"
    with open("/".join(n_path)+"/"+json_filename, 'w') as jsonfile:
        jsonfile.write(data_json)


def save_mortality():
    from disease.models import CausaMortality, MortalityYears

    data = load_csv_mortality()
    for datum in data:
        cm, _ = CausaMortality.objects.get_or_create(
            cie_10=datum["clave"],
            defaults={"description": datum["description"]})
        for year, amount in datum["years"]:
            MortalityYears.objects.get_or_create(
                causa_mortality=cm,
                year=int(year),
                defaults={"amount": int(amount.replace(" ", ""))})
    print("saved")
