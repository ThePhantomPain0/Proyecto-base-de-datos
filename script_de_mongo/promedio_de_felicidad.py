from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["añosdeinvestigacion"]

años = ["2015", "2016", "2017", "2018", "2019"]

print("--- PROMEDIO DE FELICIDAD GLOBAL POR AÑO ---")

for año in años:
    campo_puntaje = (
        "Happiness Score"
        if año in ["2015", "2016"]
        else ("Happiness.Score" if año == "2017" else "Score")
    )

    pipeline = [
        {"$group": {"_id": None, "promedio": {"$avg": f"${campo_puntaje}"}}}
    ]

    res = list(db[año].aggregate(pipeline))
    if res:
        print(f"Año {año}: Promedio Global = {res[0]['promedio']:.3f}")