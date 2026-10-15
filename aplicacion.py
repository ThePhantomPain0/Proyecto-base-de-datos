import os
from collections import Counter
from pymongo import MongoClient
import plotly.express as px
import plotly.graph_objects as go
import redis
import streamlit as st

# =========================================================================
# CONFIGURACIÓN DE LA PÁGINA
# =========================================================================
st.set_page_config(
    page_title="Taller BD: MongoDB & Redis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================================
# FUNCIONES DE CONEXIÓN SEGURO Y CACHÉ
# =========================================================================
@st.cache_resource
def conectar_mongo():
    """Conexión persistente a MongoDB."""
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
    client.admin.command("ping")  # Probar si MongoDB responde
    return client["añosdeinvestigacion"]


@st.cache_resource
def conectar_redis():
    """Conexión persistente a Redis."""
    r = redis.Redis(
        host="localhost",
        port=6379,
        db=0,
        decode_responses=True,
        socket_timeout=2,
    )
    r.ping()  # Probar si Redis responde
    return r


# Verificación de Estado de las Bases de Datos
db_mongo, r_redis = None, None
status_mongo, status_redis = "🔴 Desconectado", "🔴 Desconectado"

try:
    db_mongo = conectar_mongo()
    status_mongo = "🟢 Conectado"
except Exception as e:
    status_mongo = f"🔴 Error ({e})"

try:
    r_redis = conectar_redis()
    status_redis = "🟢 Conectado"
except Exception as e:
    status_redis = f"🔴 Error ({e})"


@st.cache_data(ttl=600)
def cargar_registros_redis():
    """Extrae encuestas desde Redis usando Pipelines de forma ultra rápida."""
    if not r_redis:
        return []
    try:
        keys = list(r_redis.scan_iter("encuesta:*"))
        pipe = r_redis.pipeline()
        for i in range(0, len(keys), 10000):
            for k in keys[i : i + 10000]:
                pipe.hmget(
                    k,
                    [
                        "Occupation",
                        "treatment",
                        "Days_Indoors",
                        "Growing_Stress",
                        "Gender",
                        "family_history",
                        "Country",
                        "Coping_Struggles",
                    ],
                )
        return pipe.execute()
    except Exception:
        return []


# Helper para campos dinámicos de MongoDB según el año
def campos_mongo(año):
    pais = "Country" if año in ["2015", "2016", "2017"] else "Country or region"
    rank = (
        "Happiness Rank"
        if año in ["2015", "2016"]
        else ("Happiness.Rank" if año == "2017" else "Overall rank")
    )
    score = (
        "Happiness Score"
        if año in ["2015", "2016"]
        else ("Happiness.Score" if año == "2017" else "Score")
    )
    pib = (
        "Economy (GDP per Capita)"
        if año in ["2015", "2016"]
        else ("Economy..GDP.per.Capita." if año == "2017" else "GDP per capita")
    )
    return pais, rank, score, pib


# =========================================================================
# BARRA LATERAL (NAVEGACIÓN Y REINICIO DE CONEXIÓN)
# =========================================================================
st.sidebar.title("📌 Navegación del Taller")
seccion = st.sidebar.radio(
    "Selecciona una sección:",
    [
        "1. Presentación del Proyecto",
        "2. Consultas en MongoDB",
        "3. Consultas en Redis",
        "4. Análisis Cruzado (Mongo + Redis)",
        "5. Código Fuente para Evaluación",
    ],
)

año_mongo = st.sidebar.selectbox(
    "Año de Filtro para MongoDB:", ["2015", "2016", "2017", "2018", "2019"], index=4
)

st.sidebar.markdown("---")
st.sidebar.subheader("🔌 Estado de Conexiones NoSQL")
st.sidebar.text(f"MongoDB: {status_mongo}")
st.sidebar.text(f"Redis:   {status_redis}")

st.sidebar.markdown("### 🔄 Gestión de Conexiones")
col_btn1, col_btn2 = st.sidebar.columns(2)

with col_btn1:
    if st.button("🔄 Reconectar", help="Limpia conexiones e intenta reconectar"):
        st.cache_resource.clear()
        st.cache_data.clear()
        st.toast("Reconectando a las bases de datos...", icon="⚡")
        st.rerun()

with col_btn2:
    if st.button("🧹 Limpiar Cache", help="Elimina los datos guardados en memoria"):
        st.cache_data.clear()
        st.toast("Memoria caché limpiada.", icon="🧼")
        st.rerun()


# =========================================================================
# SECCIÓN 1: PORTADA / PRESENTACIÓN
# =========================================================================
if seccion == "1. Presentación del Proyecto":
    st.title("🎓 Taller de Base de Datos: Integración NoSQL")
    st.subheader(
        "Análisis Multidimensional de Felicidad Mundial (MongoDB) y Salud Mental (Redis)"
    )

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.info("### 🍃 Base de Datos 1: MongoDB")
        st.markdown("""
        * **Base de datos:** `añosdeinvestigacion`
        * **Colecciones:** `2015`, `2016`, `2017`, `2018`, `2019`
        * **Métrica Principal:** Escala de Cantril (0 a 10) para el índice de felicidad mundial, PIB per cápita y apoyo social.
        """)

    with col2:
        st.success("### ⚡ Base de Datos 2: Redis")
        st.markdown("""
        * **Estructura de Datos:** Hashes (`encuesta:1`, `encuesta:2`, ...)
        * **Manejo de Datos:** Optimizado para lecturas masivas.
        * **Técnica de Consulta:** *Pipelines* para transferencias masivas en lotes de 10,000 llaves.
        """)

    st.markdown("---")
    registros = cargar_registros_redis()
    st.metric(
        label="Total de Encuestas Procesadas en Tiempo Real desde Redis",
        value=f"{len(registros):,}" if registros else "Sin datos / Desconectado",
    )


# =========================================================================
# SECCIÓN 2: CONSULTAS MONGODB
# =========================================================================
elif seccion == "2. Consultas en MongoDB":
    st.title("🍃 Consultas de Análisis en MongoDB")

    if not db_mongo:
        st.error("No hay conexión con MongoDB. Haz clic en 'Reconectar' en la barra lateral.")
    else:
        c_pais, c_rank, c_score, c_pib = campos_mongo(año_mongo)

        tab1, tab2, tab3, tab4 = st.tabs(
            [
                "1. Promedio Global",
                "2. Países Élite (> 7.5)",
                "3. Top PIB per Cápita",
                "4. Evolución de Chile",
            ]
        )

        # 1. Promedio
        with tab1:
            st.subheader("Promedio del Puntaje de Felicidad Global (2015 - 2019)")
            promedios = []
            años = ["2015", "2016", "2017", "2018", "2019"]
            for a in años:
                _, _, s, _ = campos_mongo(a)
                pipe = [{"$group": {"_id": None, "prom": {"$avg": f"${s}"}}}]
                res = list(db_mongo[a].aggregate(pipe))
                if res and res[0]["prom"] is not None:
                    promedios.append({"Año": a, "Promedio": round(res[0]["prom"], 2)})

            if promedios:
                fig = px.bar(
                    promedios,
                    x="Año",
                    y="Promedio",
                    text="Promedio",
                    range_y=[0, 10],
                    color="Promedio",
                    color_continuous_scale="Blues",
                )
                st.plotly_chart(fig, use_container_width="stretch")
            else:
                st.warning("No se encontraron datos para calcular el promedio.")

        # 2. Países Élite
        with tab2:
            st.subheader(f"Países con Puntaje de Felicidad > 7.5 ({año_mongo})")
            top_75 = list(
                db_mongo[año_mongo]
                .find(
                    {c_score: {"$gt": 7.5}},
                    {"_id": 0, c_pais: 1, c_score: 1, c_rank: 1},
                )
                .sort(c_score, -1)
            )

            df_75 = [
                {
                    "País": d[c_pais],
                    "Puntaje": round(d[c_score], 2),
                    "Ranking": d[c_rank],
                }
                for d in top_75
                if d.get(c_pais) and d.get(c_score) is not None
            ]

            if df_75:
                fig = px.bar(
                    df_75,
                    x="Puntaje",
                    y="País",
                    orientation="h",
                    text="Puntaje",
                    color="Puntaje",
                    color_continuous_scale="Greens",
                )
                fig.update_layout(yaxis={"autorange": "reversed"})
                st.plotly_chart(fig, use_container_width="stretch")
            else:
                st.warning("No se encontraron países con puntaje superior a 7.5 en este año.")

        # 3. Top PIB
        with tab3:
            st.subheader(f"Top 10 Países con Mayor PIB per Cápita ({año_mongo})")
            top_pib = list(
                db_mongo[año_mongo]
                .find({}, {"_id": 0, c_pais: 1, c_pib: 1})
                .sort(c_pib, -1)
                .limit(10)
            )

            df_pib = [
                {"País": d[c_pais], "PIB": round(d[c_pib], 3)}
                for d in top_pib
                if d.get(c_pais) and d.get(c_pib) is not None
            ]

            if df_pib:
                fig = px.bar(
                    df_pib,
                    x="PIB",
                    y="País",
                    orientation="h",
                    text="PIB",
                    color="PIB",
                    color_continuous_scale="Purples",
                )
                fig.update_layout(yaxis={"autorange": "reversed"})
                st.plotly_chart(fig, use_container_width="stretch")
            else:
                st.warning("No hay datos de PIB disponibles.")

        # 4. Evolución Chile
        with tab4:
            st.subheader("Trayectoria Histórica de Chile en el Ranking Mundial (2015 - 2019)")
            años_presentes, pos, scores = [], [], []
            años = ["2015", "2016", "2017", "2018", "2019"]
            for a in años:
                p, r, s, _ = campos_mongo(a)
                doc = db_mongo[a].find_one({p: "Chile"})
                if doc and doc.get(r) is not None:
                    años_presentes.append(a)
                    pos.append(doc[r])
                    scores.append(round(doc[s], 2))

            if pos:
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=años_presentes,
                        y=pos,
                        mode="lines+markers+text",
                        text=[f"#{p} ({sc} pts)" for p, sc in zip(pos, scores)],
                        textposition="top center",
                        line=dict(color="#C44E52", width=3),
                        marker=dict(size=10),
                    )
                )
                fig.update_layout(
                    yaxis=dict(autorange="reversed", title="Posición en el Ranking")
                )
                st.plotly_chart(fig, use_container_width="stretch")
            else:
                st.warning("No se encontraron registros históricos para Chile.")


# =========================================================================
# SECCIÓN 3: CONSULTAS REDIS
# =========================================================================
elif seccion == "3. Consultas en Redis":
    st.title("⚡ Consultas de Análisis en Redis")

    registros = cargar_registros_redis()

    if not registros:
        st.error("No se pudieron cargar datos desde Redis. Revisa la conexión.")
    else:
        tab1, tab2, tab3, tab4 = st.tabs(
            [
                "1. Ocupación vs Tratamiento",
                "2. Estrés vs Encierro",
                "3. Top Países en Redis",
                "4. Casos Críticos",
            ]
        )

        # 1. Ocupación
        with tab1:
            st.subheader("% de Personas en Tratamiento según Ocupación")
            data = {}
            for ocu, treat, *_ in registros:
                if ocu:
                    if ocu not in data:
                        data[ocu] = {"total": 0, "si": 0}
                    data[ocu]["total"] += 1
                    if treat == "Yes":
                        data[ocu]["si"] += 1

            df = [
                {
                    "Ocupación": k,
                    "% Tratamiento": round((v["si"] / v["total"]) * 100, 1),
                }
                for k, v in data.items()
                if v["total"] > 0
            ]

            if df:
                fig = px.bar(
                    df,
                    x="% Tratamiento",
                    y="Ocupación",
                    orientation="h",
                    text="% Tratamiento",
                    color="% Tratamiento",
                    color_continuous_scale="Blues",
                )
                st.plotly_chart(fig, use_container_width="stretch")
            else:
                st.warning("No se encontraron datos por ocupación en Redis.")

        # 2. Aislamiento
        with tab2:
            st.subheader("Impacto del Tiempo en Encierro en el Estrés Creciente")
            data = {}
            orden = [
                "Go out Every day",
                "1-14 days",
                "15-30 days",
                "31-60 days",
                "More than 2 months",
            ]
            for _, _, dias, estres, *_ in registros:
                if dias:
                    if dias not in data:
                        data[dias] = {"total": 0, "si": 0}
                    data[dias]["total"] += 1
                    if estres == "Yes":
                        data[dias]["si"] += 1

            df = [
                {
                    "Tiempo Encierro": d,
                    "% Estrés": round((data[d]["si"] / data[d]["total"]) * 100, 1),
                }
                for d in orden
                if d in data and data[d]["total"] > 0
            ]

            if df:
                fig = px.bar(
                    df,
                    x="Tiempo Encierro",
                    y="% Estrés",
                    text="% Estrés",
                    color="% Estrés",
                    color_continuous_scale="Oranges",
                )
                st.plotly_chart(fig, use_container_width="stretch")
            else:
                st.warning("No se encontraron datos de aislamiento en Redis.")

        # 3. Top Países
        with tab3:
            st.subheader("Top 5 Países con Mayor Muestra Encuestada en Redis")
            conteo = Counter([r[6] for r in registros if r[6]])
            top5 = conteo.most_common(5)
            df = [{"País": p[0], "Registros": p[1]} for p in top5]

            if df:
                fig = px.bar(
                    df,
                    x="País",
                    y="Registros",
                    text="Registros",
                    color="Registros",
                    color_continuous_scale="Reds",
                )
                st.plotly_chart(fig, use_container_width="stretch")
            else:
                st.warning("No hay datos de países en Redis.")

        # 4. Casos Críticos
        with tab4:
            st.subheader("Casos Críticos por Ocupación (>2 Meses Encierro + Estrés)")
            conteo = Counter()
            for ocu, _, dias, estres, _, _, _, coping in registros:
                if (
                    dias in ["More than 2 months", "31-60 days"]
                    and estres == "Yes"
                    and coping == "Yes"
                ):
                    if ocu:
                        conteo[ocu] += 1

            df = [{"Ocupación": k, "Casos Críticos": v} for k, v in conteo.items()]

            if df:
                fig = px.bar(
                    df,
                    x="Ocupación",
                    y="Casos Críticos",
                    text="Casos Críticos",
                    color="Casos Críticos",
                    color_continuous_scale="Purples",
                )
                st.plotly_chart(fig, use_container_width="stretch")
            else:
                st.warning("No se encontraron casos críticos con los filtros seleccionados.")


# =========================================================================
# SECCIÓN 4: ANÁLISIS CRUZADO
# =========================================================================
elif seccion == "4. Análisis Cruzado (Mongo + Redis)":
    st.title("🔀 Análisis Cruzado: Felicidad (Mongo) vs Estrés (Redis)")

    registros = cargar_registros_redis()

    if not db_mongo or not registros:
        st.error("Se requieren ambas bases de datos conectadas para realizar este análisis.")
    else:
        c_pais, _, c_score, _ = campos_mongo(año_mongo)

        docs_mongo = list(
            db_mongo[año_mongo].find({}, {"_id": 0, c_pais: 1, c_score: 1})
        )

        stats_redis = {}
        for p, _, _, estres, *_ in registros:
            if p:
                if p not in stats_redis:
                    stats_redis[p] = {"total": 0, "estres": 0}
                stats_redis[p]["total"] += 1
                if estres == "Yes":
                    stats_redis[p]["estres"] += 1

        cruzado = []
        for d in docs_mongo:
            pais = d.get(c_pais)
            score = d.get(c_score)
            if pais and score and pais in stats_redis and stats_redis[pais]["total"] >= 100:
                tot = stats_redis[pais]["total"]
                pct_est = round((stats_redis[pais]["estres"] / tot) * 100, 1)
                cruzado.append(
                    {
                        "País": pais,
                        "Puntaje Felicidad": round(score, 2),
                        "% Estrés Creciente": pct_est,
                        "Muestra Redis": tot,
                    }
                )

        if cruzado:
            fig = px.scatter(
                cruzado,
                x="Puntaje Felicidad",
                y="% Estrés Creciente",
                text="País",
                size="Muestra Redis",
                color="% Estrés Creciente",
                title="Matriz de Dispersión: Score de Felicidad vs Estrés Creciente",
                color_continuous_scale="Reds",
            )
            fig.update_traces(textposition="top center")
            st.plotly_chart(fig, use_container_width="stretch")
        else:
            st.warning("No se encontraron coincidencias suficientes entre los países de MongoDB y Redis para este año (mínimo 100 encuestas requeridas por país).")


# =========================================================================
# SECCIÓN 5: CÓDIGO FUENTE (EVALUACIÓN)
# =========================================================================
elif seccion == "5. Código Fuente para Evaluación":
    st.title("💻 Código de Consultas Implementado")
    st.markdown("A continuación se presenta el código fuente utilizado para las consultas NoSQL:")

    with st.expander("Ver Código de Pipeline de Lectura en Redis"):
        st.code(
            """
import redis

r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
keys = list(r.scan_iter("encuesta:*"))

# Ejecución por bloques de 10,000 para optimizar el rendimiento
pipe = r.pipeline()
for i in range(0, len(keys), 10000):
    for k in keys[i : i + 10000]:
        pipe.hmget(k, ["Occupation", "treatment", "Days_Indoors", "Growing_Stress"])

registros = pipe.execute()
        """,
            language="python",
        )

    with st.expander("Ver Código de Agregación e Histórico en MongoDB"):
        st.code(
            """
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["añosdeinvestigacion"]

# 1. Agregación del promedio de felicidad mundial
pipeline = [{"$group": {"_id": None, "prom": {"$avg": "$Score"}}}]
resultado_promedio = list(db["2019"].aggregate(pipeline))

# 2. Consulta filtrada de países de élite (> 7.5)
paises_top = db["2019"].find({"Score": {"$gt": 7.5}}).sort("Score", -1)
        """,
            language="python",
        )