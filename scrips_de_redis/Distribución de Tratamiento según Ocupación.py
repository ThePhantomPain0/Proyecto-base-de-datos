import redis

r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

ocupaciones = {}

keys = list(r.scan_iter("encuesta:*"))
pipe = r.pipeline()

print("--- ANÁLISIS DE TRATAMIENTO POR OCUPACIÓN ---")
for i in range(0, len(keys), 10000):
    bloque = keys[i : i + 10000]
    for k in bloque:
        pipe.hmget(k, ["Occupation", "treatment"])
    
    resultados = pipe.execute()
    for ocu, treat in resultados:
        if not ocu:
            continue
        if ocu not in ocupaciones:
            ocupaciones[ocu] = {"total": 0, "tratamiento": 0}
        
        ocupaciones[ocu]["total"] += 1
        if treat == "Yes":
            ocupaciones[ocu]["tratamiento"] += 1

print(f"{'Ocupación':<20} | {'Total':<10} | {'En Tratamiento':<15} | {'% Tratamiento'}")
print("-" * 65)
for ocu, stats in ocupaciones.items():
    pct = round((stats["tratamiento"] / stats["total"]) * 100, 2)
    print(f"{ocu:<20} | {stats['total']:<10} | {stats['tratamiento']:<15} | {pct}%")