from pymongo import MongoClient
import redis

# 1. Conexiones NoSQL con tiempo de espera extendido (socket_timeout=10)
db_mongo = MongoClient("mongodb://localhost:27017/")["añosdeinvestigacion"]
r_redis = redis.Redis(
    host="localhost", port=6379, db=0, decode_responses=True, socket_timeout=10
)

print(
    "=== EJERCICIO 3: HISTORIAL FAMILIAR (REDIS) POR REGIÓN GEOGRÁFICA (MONGO) ==="
)

# 2. Obtener mapa País -> Región desde MongoDB
mapa_regiones = {}
for doc in db_mongo["2015"].find({}, {"_id": 0, "Country": 1, "Region": 1}):
    if doc.get("Country") and doc.get("Region"):
        mapa_regiones[doc["Country"]] = doc["Region"]

# 3. Procesamiento optimizado por LOTES en Redis para EVITAR TIMEOUTS
regionales = {}
TAMANO_LOTE = 5000  # Procesa de a 5,000 llaves para no saturar el socket
pipe = r_redis.pipeline()
contador = 0


def procesar_lote_resultados(resultados):
    """Procesa un bloque de respuestas acumulando contadores por región."""
    for item in resultados:
        if not item or len(item) < 3:
            continue

        pais, historial, treat = item[0], item[1], item[2]
        region = mapa_regiones.get(pais, "Otras Regiones / No Clasificados")

        if region not in regionales:
            regionales[region] = {
                "total": 0,
                "historial_si": 0,
                "tratamiento_si": 0,
            }

        regionales[region]["total"] += 1
        if historial == "Yes":
            regionales[region]["historial_si"] += 1
        if treat == "Yes":
            regionales[region]["tratamiento_si"] += 1


print(" Extrayendo datos de Redis por lotes...")

# Recorre todas las llaves en Redis ejecutando pipelines fragmentados
for key in r_redis.scan_iter("encuesta:*"):
    pipe.hmget(key, ["Country", "family_history", "treatment"])
    contador += 1

    # Vacía y procesa el pipeline cada 5,000 registros
    if contador % TAMANO_LOTE == 0:
        resultados = pipe.execute()
        procesar_lote_resultados(resultados)

# Procesa las llaves restantes que no completaron el último múltiplo
if contador % TAMANO_LOTE != 0:
    resultados = pipe.execute()
    procesar_lote_resultados(resultados)

print(f" Carga lista: {contador:,} registros procesados correctamente.\n")

# 4. Imprimir la tabla de resultados
print("-" * 85)
print(
    f"{'Región Geográfica':<32} | {'Encuestas':<10} | {'% Historial Familiar':<22} | {'% Tratamiento'}"
)
print("-" * 85)

for reg, stats in regionales.items():
    tot = stats["total"]
    if tot > 0:
        pct_hist = round((stats["historial_si"] / tot) * 100, 1)
        pct_treat = round((stats["tratamiento_si"] / tot) * 100, 1)
        print(f"{reg:<32} | {tot:<10,} | {pct_hist:<22}% | {pct_treat}%")