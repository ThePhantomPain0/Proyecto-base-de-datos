import csv
import os
import redis

# 1. Conexión a Redis en Docker con protocol=2
r = redis.Redis(
    host="localhost", 
    port=6379, 
    db=0, 
    decode_responses=True, 
    protocol=2
)

# 2. Construir la ruta exacta hacia el CSV ubicado en la misma carpeta que el script
carpeta_del_script = os.path.dirname(__file__)
csv_path = os.path.join(carpeta_del_script, "Mental Health Dataset.csv")

print(f"Buscando archivo en: {csv_path}")

# 3. Limpiar encuestas previas
for key in r.scan_iter("encuesta:*"):
    r.delete(key)

pipe = r.pipeline()
contador = 0

# 4. Leer e insertar datos en Redis
with open(csv_path, mode="r", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    for row in reader:
        contador += 1
        key = f"encuesta:{contador}"

        # Reemplazar campos vacíos por 'N/A'
        data = {k: (v if v.strip() != "" else "N/A") for k, v in row.items()}
        pipe.hset(key, mapping=data)

        if contador % 10000 == 0:
            pipe.execute()
            print(f"Procesados {contador} registros...")

pipe.execute()
print(f"¡Carga completa! Se insertaron {contador} encuestas completas en Redis.")