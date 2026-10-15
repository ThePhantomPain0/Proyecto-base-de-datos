from pymongo import MongoClient

# Conexión a MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["añosdeinvestigacion"]

años = ["2015", "2016", "2017", "2018", "2019"]

print("--- PAÍSES CON PUNTAJE DE FELICIDAD MAYOR A 7.5 (2015 - 2019) ---")

for año in años:
    col = db[año]

    campo_pais = (
        "Country" if año in ["2015", "2016", "2017"] else "Country or region"
    )
    campo_puntaje = (
        "Happiness Score"
        if año in ["2015", "2016"]
        else ("Happiness.Score" if año == "2017" else "Score")
    )

    paises_top = col.find(
        {campo_puntaje: {"$gt": 7.5}},
        {"_id": 0, campo_pais: 1, campo_puntaje: 1},
    ).sort(campo_puntaje, -1)

    print(f"\n==================== AÑO {año} ====================")
    for p in paises_top:
        nombre_pais = p.get(campo_pais)
        puntaje = p.get(campo_puntaje)
        print(f"País: {nombre_pais:<20} | Puntaje: {puntaje}")