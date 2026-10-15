from pymongo import MongoClient
import redis

db_mongo = MongoClient("mongodb://localhost:27017/")["añosdeinvestigacion"]
r_redis = redis.Redis(
    host="localhost", port=6379, db=0, decode_responses=True, socket_timeout=10
)

print(
    "=== EJERCICIO 4: PERCEPCIÓN DE TRANSPARENCIA (MONGO) VS CASOS CRÍTICOS (REDIS) ==="
)

paises_limpios = list(
    db_mongo["2019"].find(
        {"Perceptions of corruption": {"$gt": 0.25}},
        {
            "_id": 0,
            "Country or region": 1,
            "Perceptions of corruption": 1,
            "Score": 1,
        },
    )
)
nombres_limpios = {d["Country or region"]: d for d in paises_limpios}

casos_criticos = {}
TAMANO_LOTE = 5000  
pipe = r_redis.pipeline()
contador = 0


def procesar_lote_resultados(resultados):
    """Procesa un lote de respuestas acumulando casos críticos por país."""
    for item in resultados:
        if not item or len(item) < 3:
            continue

        pais, dias, estres = item[0], item[1], item[2]
        if pais in nombres_limpios:
            if pais not in casos_criticos:
                casos_criticos[pais] = {"total_muestra": 0, "criticos": 0}

            casos_criticos[pais]["total_muestra"] += 1
            if dias in ["31-60 days", "More than 2 months"] and estres == "Yes":
                casos_criticos[pais]["criticos"] += 1


print(" Extrayendo datos de encuestas en Redis por lotes...")

for key in r_redis.scan_iter("encuesta:*"):
    pipe.hmget(key, ["Country", "Days_Indoors", "Growing_Stress"])
    contador += 1

    if contador % TAMANO_LOTE == 0:
        resultados = pipe.execute()
        procesar_lote_resultados(resultados)

if contador % TAMANO_LOTE != 0:
    resultados = pipe.execute()
    procesar_lote_resultados(resultados)

print(f" Carga lista: {contador:,} registros procesados correctamente.\n")

print("-" * 85)
print(
    f"{'País':<20} | {'Transparencia':<15} | {'Score Felicidad':<16} | {'% Casos Críticos en Encierro'}"
)
print("-" * 85)

for pais, info in nombres_limpios.items():
    if pais in casos_criticos and casos_criticos[pais]["total_muestra"] > 0:
        tot = casos_criticos[pais]["total_muestra"]
        crit = casos_criticos[pais]["criticos"]
        pct_crit = round((crit / tot) * 100, 1)

        print(
            f"{pais:<20} | {info['Perceptions of corruption']:<15.3f} | {info['Score']:<16} | {pct_crit}% ({crit:,} de {tot:,})"
        )