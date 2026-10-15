from pymongo import MongoClient
import redis

# 1. Conexiones NoSQL protegidas con timeout para evitar cortes por socket
db_mongo = MongoClient("mongodb://localhost:27017/")["añosdeinvestigacion"]
r_redis = redis.Redis(
    host="localhost", port=6379, db=0, decode_responses=True, socket_timeout=10
)

print(
    "--- CONSULTA 1: APOYO SOCIAL Y PIB (MONGO) VS % EN TRATAMIENTO (REDIS) ---"
)

# 2. Consultar MongoDB
paises_mongo = list(
    db_mongo["2019"].find(
        {},
        {
            "_id": 0,
            "Country or region": 1,
            "GDP per capita": 1,
            "Social support": 1,
            "Score": 1,
        },
    )
)

# 3. Procesamiento en Lotes para Redis
stats_redis = {}
TAMANO_LOTE = 5000
pipe = r_redis.pipeline()
contador = 0


def procesar_lote(resultados):
    """Procesa las respuestas de Redis acumulando conteos por país."""
    for item in resultados:
        if not item or not item[0]:
            continue

        pais, treat = item[0], item[1]
        if pais not in stats_redis:
            stats_redis[pais] = {"total": 0, "tratamiento": 0}

        stats_redis[pais]["total"] += 1
        if treat == "Yes":
            stats_redis[pais]["tratamiento"] += 1


print(" Extrayendo encuestas de Redis por lotes...")

# Iterar por las llaves vaciando el buffer del pipeline en bloques pequeños
for key in r_redis.scan_iter("encuesta:*"):
    pipe.hmget(key, ["Country", "treatment"])
    contador += 1

    if contador % TAMANO_LOTE == 0:
        resultados = pipe.execute()
        procesar_lote(resultados)

# Procesar el último lote remanente
if contador % TAMANO_LOTE != 0:
    resultados = pipe.execute()
    procesar_lote(resultados)

print(f" Carga lista: {contador:,} registros procesados correctamente.\n")

# 4. Cruzar y mostrar los datos
print("-" * 75)
print(
    f"{'País':<20} | {'Score Felicidad':<15} | {'Apoyo Social':<15} | {'% Tratamiento (Redis)'}"
)
print("-" * 75)

for doc in paises_mongo:
    pais = doc.get("Country or region")
    if pais in stats_redis and stats_redis[pais]["total"] >= 100:
        total = stats_redis[pais]["total"]
        pct_treat = round(
            (stats_redis[pais]["tratamiento"] / total) * 100, 1
        )
        score = doc.get("Score")
        apoyo = doc.get("Social support")

        print(
            f"{pais:<20} | {score:<15} | {apoyo:<15} | {pct_treat}% ({total:,} encuestados)"
        )