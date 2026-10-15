import redis

r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

aislamiento = {}

keys = list(r.scan_iter("encuesta:*"))
pipe = r.pipeline()

print("--- IMPACTO DEL AISLAMIENTO (Days_Indoors) EN EL ESTRÉS ---")
for i in range(0, len(keys), 10000):
    bloque = keys[i : i + 10000]
    for k in bloque:
        pipe.hmget(k, ["Days_Indoors", "Growing_Stress"])
    
    resultados = pipe.execute()
    for dias, estres in resultados:
        if not dias:
            continue
        if dias not in aislamiento:
            aislamiento[dias] = {"total": 0, "estres_si": 0}
        
        aislamiento[dias]["total"] += 1
        if estres == "Yes":
            aislamiento[dias]["estres_si"] += 1

print(f"{'Días en Encierro':<20} | {'Total':<10} | {'Con Estrés Creciente':<20} | {'% Estrés'}")
print("-" * 70)
for dias, stats in aislamiento.items():
    pct = round((stats["estres_si"] / stats["total"]) * 100, 2)
    print(f"{dias:<20} | {stats['total']:<10} | {stats['estres_si']:<20} | {pct}%")