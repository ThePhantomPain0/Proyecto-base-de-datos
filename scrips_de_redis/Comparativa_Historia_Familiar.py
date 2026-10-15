import redis

r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

matriz = {}

keys = list(r.scan_iter("encuesta:*"))
pipe = r.pipeline()

print("--- ANÁLISIS: GÉNERO + HISTORIAL FAMILIAR VS TRATAMIENTO ---")
for i in range(0, len(keys), 10000):
    bloque = keys[i : i + 10000]
    for k in bloque:
        pipe.hmget(k, ["Gender", "family_history", "treatment"])
    
    resultados = pipe.execute()
    for gen, hist, treat in resultados:
        if not gen or not hist:
            continue
        clave_grupo = f"{gen} | Historial: {hist}"
        if clave_grupo not in matriz:
            matriz[clave_grupo] = {"total": 0, "tratamiento": 0}
        
        matriz[clave_grupo]["total"] += 1
        if treat == "Yes":
            matriz[clave_grupo]["tratamiento"] += 1

print(f"{'Grupo':<30} | {'Total':<10} | {'En Tratamiento':<15} | {'% Tratamiento'}")
print("-" * 70)
for grupo, stats in matriz.items():
    pct = round((stats["tratamiento"] / stats["total"]) * 100, 2)
    print(f"{grupo:<30} | {stats['total']:<10} | {stats['tratamiento']:<15} | {pct}%")