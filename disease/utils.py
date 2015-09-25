
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
