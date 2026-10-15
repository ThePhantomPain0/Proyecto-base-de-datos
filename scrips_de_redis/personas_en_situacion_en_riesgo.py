import redis

r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

casos_criticos = []
limite = 25  

keys = list(r.scan_iter("encuesta:*"))
pipe = r.pipeline()

print("--- MUESTRA DE CASOS CRÍTICOS (Aislamiento > 2 Meses + Estrés + Coping Struggles) ---")
for i in range(0, len(keys), 10000):
    bloque = keys[i : i + 10000]
    for k in bloque:
        pipe.hmget(k, ["Country", "Occupation", "Days_Indoors", "Growing_Stress", "Coping_Struggles"])
    
    resultados = pipe.execute()
    for p, ocu, dias, estres, coping in resultados:
        if dias in ["More than 2 months", "31-60 days"] and estres == "Yes" and coping == "Yes":
            casos_criticos.append({
                "Pais": p,
                "Ocupacion": ocu,
                "Aislamiento": dias
            })
            if len(casos_criticos) >= limite:
                break
    if len(casos_criticos) >= limite:
        break

for idx, caso in enumerate(casos_criticos, start=1):
    print(f"Caso #{idx}: País: {caso['Pais']} | Ocupación: {caso['Ocupacion']} | Aislamiento: {caso['Aislamiento']}")