from collections import Counter
import matplotlib.pyplot as plt
import redis
import seaborn as sns


class AnalizadorRedis:

    def __init__(self, host="localhost", port=6379):
        """Inicializa la conexión y extrae los datos de Redis una sola vez."""
        self.r = redis.Redis(
            host=host, port=port, db=0, decode_responses=True
        )

        # Configuración estética global
        sns.set_theme(style="whitegrid", palette="muted")
        plt.rcParams.update(
            {
                "font.size": 11,
                "font.family": "sans-serif",
                "axes.titlesize": 13,
                "axes.labelsize": 11,
                "figure.autolayout": True,
            }
        )

        print(" Cargando datos desde Redis...")
        keys = list(self.r.scan_iter("encuesta:*"))

        # Extraemos todo en un solo pipeline optimizado
        pipe = self.r.pipeline()
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
        self.registros = pipe.execute()
        print(f" Carga lista: {len(self.registros):,} registros almacenados.")

    # -------------------------------------------------------------------------
    # FUNCIONES DE ANÁLISIS Y GRÁFICOS MEJORADOS
    # -------------------------------------------------------------------------

    def grafico_ocupacion(self):
        """1. Tratamiento según ocupación con porcentaje en barras horizontales."""
        data = {}
        for ocu, treat, *_ in self.registros:
            if ocu:
                if ocu not in data:
                    data[ocu] = {"total": 0, "si": 0}
                data[ocu]["total"] += 1
                if treat == "Yes":
                    data[ocu]["si"] += 1

        # Ordenar de mayor a menor porcentaje
        items = sorted(
            data.items(),
            key=lambda item: (item[1]["si"] / item[1]["total"]),
            reverse=True,
        )
        x = [item[0] for item in items]
        y = [round((item[1]["si"] / item[1]["total"]) * 100, 1) for item in items]

        fig, ax = plt.subplots(figsize=(9, 4.5))
        bars = ax.barh(x, y, color="#4C72B0", edgecolor="#2B4B7C", height=0.6)

        ax.set_title(
            "1. Porcentaje de Personas en Tratamiento según Ocupación",
            fontweight="bold",
            pad=15,
        )
        ax.set_xlabel("% en Tratamiento de Salud Mental", fontweight="bold")
        ax.set_xlim(0, 100)
        ax.invert_yaxis()  # El mayor porcentaje arriba

        # Etiquetas con el valor dentro/fuera de cada barra
        for bar in bars:
            w = bar.get_width()
            ax.text(
                w + 1.5,
                bar.get_y() + bar.get_height() / 2,
                f"{w:.1f}%",
                va="center",
                fontweight="bold",
                color="#333333",
            )

        sns.despine(top=True, right=True)
        plt.savefig("grafico_1_ocupacion.png", dpi=300)
        plt.close()
        print(" Gráfico 1 generado: grafico_1_ocupacion.png")

    def grafico_aislamiento(self):
        """2. Estrés según tiempo de aislamiento con orden cronológico."""
        data = {}
        orden = [
            "Go out Every day",
            "1-14 days",
            "15-30 days",
            "31-60 days",
            "More than 2 months",
        ]
        etiquetas_limpias = [
            "Sale Todos\nlos Días",
            "1-14 Días",
            "15-30 Días",
            "31-60 Días",
            "> 2 Meses",
        ]

        for _, _, dias, estres, *_ in self.registros:
            if dias:
                if dias not in data:
                    data[dias] = {"total": 0, "si": 0}
                data[dias]["total"] += 1
                if estres == "Yes":
                    data[dias]["si"] += 1

        x = [
            etiquetas_limpias[i]
            for i, d in enumerate(orden)
            if d in data
        ]
        y = [
            round((data[d]["si"] / data[d]["total"]) * 100, 1)
            for d in orden
            if d in data
        ]

        fig, ax = plt.subplots(figsize=(8.5, 4.5))
        bars = ax.bar(x, y, color="#DD8452", edgecolor="#A8572A", width=0.55)

        ax.set_title(
            "2. Impacto del Tiempo en Encierro sobre el Estrés Creciente",
            fontweight="bold",
            pad=15,
        )
        ax.set_ylabel("% con Estrés Creciente", fontweight="bold")
        ax.set_ylim(0, max(y) + 12)

        for bar in bars:
            h = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                h + 1.2,
                f"{h:.1f}%",
                ha="center",
                fontweight="bold",
                color="#333333",
            )

        sns.despine(top=True, right=True)
        plt.savefig("grafico_2_aislamiento.png", dpi=300)
        plt.close()
        print(" Gráfico 2 generado: grafico_2_aislamiento.png")

    def grafico_genero_historial(self):
        """3. Tratamiento por género e historial familiar."""
        data = {}
        for _, treat, _, _, gen, hist, *_ in self.registros:
            if gen and hist:
                grupo = f"{gen}\nHistorial: {hist}"
                if grupo not in data:
                    data[grupo] = {"total": 0, "si": 0}
                data[grupo]["total"] += 1
                if treat == "Yes":
                    data[grupo]["si"] += 1

        x = list(data.keys())
        y = [round((data[g]["si"] / data[g]["total"]) * 100, 1) for g in x]

        fig, ax = plt.subplots(figsize=(9, 4.5))
        bars = ax.bar(x, y, color="#55A868", edgecolor="#2E6B3E", width=0.55)

        ax.set_title(
            "3. Búsqueda de Tratamiento por Género e Historial Familiar",
            fontweight="bold",
            pad=15,
        )
        ax.set_ylabel("% en Tratamiento", fontweight="bold")
        ax.set_ylim(0, 100)

        for bar in bars:
            h = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                h + 2,
                f"{h:.1f}%",
                ha="center",
                fontweight="bold",
                color="#333333",
            )

        sns.despine(top=True, right=True)
        plt.savefig("grafico_3_genero_historial.png", dpi=300)
        plt.close()
        print(" Gráfico 3 generado: grafico_3_genero_historial.png")

    def grafico_top_paises(self):
        """4. Top 5 países con más volumen en Redis."""
        conteo = Counter([r[6] for r in self.registros if r[6]])
        top5 = conteo.most_common(5)

        x = [p[0] for p in top5]
        y = [p[1] for p in top5]

        fig, ax = plt.subplots(figsize=(8.5, 4.5))
        bars = ax.bar(x, y, color="#C44E52", edgecolor="#8A2B2E", width=0.5)

        ax.set_title(
            "4. Top 5 Países con Mayor Muestra Encuestada en Redis",
            fontweight="bold",
            pad=15,
        )
        ax.set_ylabel("Cantidad de Registros", fontweight="bold")
        ax.set_ylim(0, max(y) * 1.15)

        for bar in bars:
            h = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                h + (max(y) * 0.02),
                f"{h:,}",
                ha="center",
                fontweight="bold",
                color="#333333",
            )

        sns.despine(top=True, right=True)
        plt.savefig("grafico_4_top_paises.png", dpi=300)
        plt.close()
        print(" Gráfico 4 generado: grafico_4_top_paises.png")

    def grafico_casos_criticos(self):
        """5. Casos críticos por ocupación."""
        conteo = Counter()
        for ocu, _, dias, estres, _, _, _, coping in self.registros:
            if (
                dias in ["More than 2 months", "31-60 days"]
                and estres == "Yes"
                and coping == "Yes"
            ):
                if ocu:
                    conteo[ocu] += 1

        items = sorted(conteo.items(), key=lambda x: x[1], reverse=True)
        x = [i[0] for i in items]
        y = [i[1] for i in items]

        fig, ax = plt.subplots(figsize=(8.5, 4.5))
        bars = ax.bar(x, y, color="#8172B0", edgecolor="#524380", width=0.5)

        ax.set_title(
            "5. Casos Críticos por Ocupación (Aislamiento > 30 días + Estrés)",
            fontweight="bold",
            pad=15,
        )
        ax.set_ylabel("Total de Casos Detectados", fontweight="bold")
        ax.set_ylim(0, max(y) * 1.15)

        for bar in bars:
            h = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                h + (max(y) * 0.02),
                f"{h:,}",
                ha="center",
                fontweight="bold",
                color="#333333",
            )

        sns.despine(top=True, right=True)
        plt.savefig("grafico_5_casos_criticos.png", dpi=300)
        plt.close()
        print(" Gráfico 5 generado: grafico_5_casos_criticos.png")

    def ejecutar_todo(self):
        """Ejecuta todas las funciones de análisis de una sola vez."""
        self.grafico_ocupacion()
        self.grafico_aislamiento()
        self.grafico_genero_historial()
        self.grafico_top_paises()
        self.grafico_casos_criticos()


# =========================================================================
# MODO DE USO
# =========================================================================
if __name__ == "__main__":
    app = AnalizadorRedis()

    # Ejecutar todos los gráficos mejorados
    app.ejecutar_todo()