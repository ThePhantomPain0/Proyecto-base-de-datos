from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["añosdeinvestigacion"]

años = ["2015", "2016", "2018", "2019"]

print("--- RANKING COMPLETO DE TODOS LOS PAÍSES POR AÑO ---")

for año in años:
    print(f"\n==================== AÑO {año} ====================")

    campo_pais = (
        "Country" if año in ["2015", "2016", "2017"] else "Country or region"
    )
    campo_ranking = (
        "Happiness Rank"
        if año in ["2015", "2016"]
        else ("Happiness.Rank" if año == "2017" else "Overall rank")
    )
    campo_puntaje = (
        "Happiness Score"
        if año in ["2015", "2016"]
        else ("Happiness.Score" if año == "2017" else "Score")
    )

    cursor = db[año].find().sort(campo_ranking, 1)

    for doc in cursor:
        pais = doc.get(campo_pais)
        rank = doc.get(campo_ranking)
        score = doc.get(campo_puntaje)

        print(f"  Posición #{rank:<3} | {pais:<25} | Puntaje: {score}")