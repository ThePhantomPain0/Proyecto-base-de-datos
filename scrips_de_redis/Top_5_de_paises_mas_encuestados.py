import redis
from collections import Counter

r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

conteo_paises = Counter()

keys = list(r.scan_iter("encuesta:*"))
pipe = r.pipeline()

print("--- TOP 5 PAÍSES CON MÁS REGISTROS EN REDIS ---")
for i in range(0, len(keys), 10000):
    bloque = keys[i : i + 10000]
    for k in bloque:
        pipe.hget(k, "Country")
    
    resultados = pipe.execute()
    conteo_paises.update([p for p in resultados if p])

for posicion, (pais, total) in enumerate(conteo_paises.most_common(5), start=1):
    print(f"#{posicion}: {pais} -> {total:,} registros")