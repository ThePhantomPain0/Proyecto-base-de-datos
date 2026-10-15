import sys
from typing import Dict, List, Optional
from pymongo import MongoClient
import redis


class AnalyticsManager:

    def __init__(
        self,
        mongo_uri: str = "mongodb://localhost:27017/",
        mongo_db: str = "añosdeinvestigacion",
        redis_host: str = "localhost",
        redis_port: int = 6379,
    ):
        """Inicializa las conexiones a Redis y MongoDB."""
        try:
            # Conexión a MongoDB
            self.mongo_client = MongoClient(mongo_uri)
            self.db = self.mongo_client[mongo_db]

            # Conexión a Redis
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=0,
                decode_responses=True,
            )
            self.redis_client.ping()
            print(" Conexión exitosa a Redis y MongoDB.")

        except Exception as e:
            print(f" Error de conexión: {e}")
            sys.exit(1)

    # -------------------------------------------------------------------------
    # CONSULTAS EN REDIS
    # -------------------------------------------------------------------------

    def obtener_encuesta_por_id(self, encuesta_id: int) -> Optional[Dict]:
        """Consulta un Hash específico de Redis por ID de encuesta."""
        clave = f"encuesta:{encuesta_id}"
        datos = self.redis_client.hgetall(clave)
        return datos if datos else None

    def obtener_resumen_salud_mental_por_pais(self, pais: str) -> Dict:
        """Agrega y calcula estadísticas de salud mental en Redis para un país específico."""
        total = 0
        tratamiento_si = 0
        estres_alto = 0

        for clave in self.redis_client.scan_iter("encuesta:*"):
            p, t, s = self.redis_client.hmget(
                clave, ["Country", "treatment", "Growing_Stress"]
            )
            if p == pais:
                total += 1
                if t == "Yes":
                    tratamiento_si += 1
                if s == "Yes":
                    estres_alto += 1

        if total == 0:
            return {"total": 0, "pct_tratamiento": 0.0, "pct_estres": 0.0}

        return {
            "total": total,
            "pct_tratamiento": round((tratamiento_si / total) * 100, 2),
            "pct_estres": round((estres_alto / total) * 100, 2),
        }

    # -------------------------------------------------------------------------
    # CONSULTAS EN MONGODB
    # -------------------------------------------------------------------------

    def obtener_top_paises_felicidad(
        self, año: str = "2019", limite: int = 5
    ) -> List[Dict]:
        """Obtiene el Top N de países más felices desde MongoDB para un año dado."""
        campo_pais = (
            "Country" if año in ["2015", "2016", "2017"] else "Country or region"
        )
        campo_rank = (
            "Happiness Rank"
            if año in ["2015", "2016"]
            else ("Happiness.Rank" if año == "2017" else "Overall rank")
        )
        campo_score = (
            "Happiness Score"
            if año in ["2015", "2016"]
            else ("Happiness.Score" if año == "2017" else "Score")
        )

        cursor = (
            self.db[año]
            .find({}, {"_id": 0, campo_pais: 1, campo_rank: 1, campo_score: 1})
            .sort(campo_rank, 1)
            .limit(limite)
        )

        resultados = []
        for doc in cursor:
            resultados.append(
                {
                    "pais": doc.get(campo_pais),
                    "posicion": doc.get(campo_rank),
                    "puntaje": doc.get(campo_score),
                }
            )
        return resultados

    # -------------------------------------------------------------------------
    # CONSULTA CRUZADA / ANÁLISIS COMBINADO
    # -------------------------------------------------------------------------

    def analizar_felicidad_vs_salud_mental(
        self, año: str = "2019", limite: int = 5
    ):
        """Cruza la información del Top N de MongoDB con las métricas en tiempo real de Redis."""
        print(
            f"\n=== ANÁLISIS CRUZADO: TOP {limite} FELICIDAD ({año}) VS SALUD MENTAL ==="
        )

        top_paises = self.obtener_top_paises_felicidad(año=año, limite=limite)

        for item in top_paises:
            pais = item["pais"]
            posicion = item["posicion"]
            puntaje = item["puntaje"]

            # Obtener datos de Redis
            stats_redis = self.obtener_resumen_salud_mental_por_pais(pais)

            print(f"\n Posición #{posicion}: {pais} (Score Mongo: {puntaje})")
            if stats_redis["total"] > 0:
                print(
                    f"   ├─ Muestra en Redis: {stats_redis['total']} encuestados"
                )
                print(
                    f"   ├─ % en Tratamiento: {stats_redis['pct_tratamiento']}%"
                )
                print(f"   └─ % Estrés Creciente: {stats_redis['pct_estres']}%")
            else:
                print("   └─ Sin registros de encuestas en Redis")


# =========================================================================
# EJECUCIÓN PRINCIPAL
# =========================================================================
if __name__ == "__main__":
    # Instanciar el administrador
    analytics = AnalyticsManager()

    # 1. Consulta simple a Redis
    print("\n--- 1. CONSULTA A REDIS POR ID ---")
    encuesta_5 = analytics.obtener_encuesta_por_id(5)
    print("Datos encuesta ID 5:", encuesta_5)

    # 2. Análisis cruzado MongoDB + Redis
    analytics.analizar_felicidad_vs_salud_mental(año="2019", limite=5)