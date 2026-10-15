from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["añosdeinvestigacion"]

años = ["2015", "2016",  "2018", "2019"]

print("--- HISTÓRICO DE PIB PER CÁPITA POR AÑO Y PAÍS (2015 - 2019) ---")

for año in años:
    col = db[año]

    campo_pais = (
        "Country" if año in ["2015", "2016", "2017"] else "Country or region"
    )
    campo_pib = (
        "Economy (GDP per Capita)"
        if año in ["2015", "2016"]
        else ("Economy..GDP.per.Capita." if año == "2017" else "GDP per capita")
    )
    campo_ranking = (
        "Happiness Rank"
        if año in ["2015", "2016"]
        else ("Happiness.Rank" if año == "2017" else "Overall rank")
    )

    print(f"\n==================== AÑO {año} ====================")

    cursor = col.find(
        {},
        {"_id": 0, campo_pais: 1, campo_pib: 1, campo_ranking: 1}
    ).sort(campo_pib, -1)

    for idx, doc in enumerate(cursor, start=1):
        pais = doc.get(campo_pais)
        pib = doc.get(campo_pib)
        rank = doc.get(campo_ranking)

        print(f"#{idx:<3} | País: {pais:<25} | PIB per Cápita: {pib} | Ranking Felicidad: #{rank}")