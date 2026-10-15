from pymongo import MongoClient
import redis

# 1. Conexiones
db_mongo = MongoClient("mongodb://localhost:27017/")["añosdeinvestigacion"]

# Conexión a Redis con protocolo RESP2 y timeout ajustado
r_redis = redis.Redis(
    host="localhost", 
    port=6379, 
    db=0, 
    decode_responses=True,
    protocol=2,
    socket_timeout=30
)

print("--- CONSULTA 2: PAÍSES MÁS FELICES (MONGO) VS ESTRÉS EN AISLAMIENTO (REDIS) ---")

# 2. Obtener el Top 15 de países más felices de MongoDB (2019)
top_felices = list(
    db_mongo["2019"]
    .find(
        {},
        {"_id": 0, "Country or region": 1, "Overall rank": 1, "Score": 1},
    )
    .sort("Overall rank", 1)
    .limit(15)
)
nombres_top = [doc["Country or region"] for doc in top_felices]

# 3. Obtener claves y procesar por bloques (Batches) desde Redis
keys = list(r_redis.scan_iter("encuesta:*"))

if not keys:
    print("\n[ERROR] No se encontraron claves con el prefijo 'encuesta:*' en Redis.")
    print("Asegúrate de haber ejecutado previamente el script de carga de datos.")
else:
    encierro_stats = {}
    batch_size = 10000
    pipe = r_redis.pipeline()

    print(f"Procesando {len(keys):,} encuestas desde Redis...")

    for i in range(0, len(keys), batch_size):
        bloque_keys = keys[i : i + batch_size]
        
        # Encolar comandos del bloque actual
        for k in bloque_keys:
            pipe.hmget(k, ["Country", "Days_Indoors", "Growing_Stress"])
        
        # EJECUTAR PIPELINE DENTRO DEL BUCLE (Bloque por bloque)
        resultados_bloque = pipe.execute()
        
        # Procesar los resultados parciales del bloque
        for pais, dias, estres in resultados_bloque:
            if pais in nombres_top and dias in ["31-60 days", "More than 2 months"]:
                if pais not in encierro_stats:
                    encierro_stats[pais] = {"total_aislados": 0, "estres_alto": 0}
                encierro_stats[pais]["total_aislados"] += 1
                if estres == "Yes":
                    encierro_stats[pais]["estres_alto"] += 1

    print("\n" + "=" * 70 + "\n")

    # 4. Imprimir los resultados cruzados
    for doc in top_felices:
        pais = doc["Country or region"]
        rank = doc["Overall rank"]
        score = doc["Score"]

        if pais in encierro_stats:
            total_aisl = encierro_stats[pais]["total_aislados"]
            estres = encierro_stats[pais]["estres_alto"]
            pct_estres = (
                round((estres / total_aisl) * 100, 1) if total_aisl > 0 else 0
            )

            print(f"#{rank:<2} {pais:<15} (Felicidad: {score})")
            print(
                f" └─ Muestra Aislada (>30 días): {total_aisl:,} personas | Con Estrés Creciente: {pct_estres}%\n"
            )