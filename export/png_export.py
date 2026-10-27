from io import BytesIO
import re
import zipfile

import plotly.express as px
import streamlit as st

from analytics.analise import (
    normalizar_texto,
    contar_categorias,
)

CORES = ["#1769AA", "#13A66B", "#7048C8", "#087E9B", "#F08A24"]


@st.cache_data(show_spinner="Gerando imagens PNG...")
def exportar_graficos_png(df, graficos):
    """Gera um ZIP com os gráficos selecionados."""
    arquivo_zip = BytesIO()

    with zipfile.ZipFile(
        arquivo_zip, "w", zipfile.ZIP_DEFLATED
    ) as zip_saida:

        for indice, (coluna, tipo) in enumerate(graficos, start=1):
            nome_seguro = re.sub(
                r"[^a-zA-Z0-9_-]+",
                "_",
                normalizar_texto(coluna),
            ).strip("_") or f"grafico_{indice}"

            contagem = contar_categorias(df, coluna)

            if tipo == "categoria":
                contagem = contagem.sort_values(
                    ascending=False
                ).head(10).sort_values()

                dados_grafico = (
                    contagem.rename_axis("Categoria")
                    .reset_index(name="Quantidade")
                )

                fig = px.bar(
                    dados_grafico,
                    x="Quantidade",
                    y="Categoria",
                    orientation="h",
                    text="Quantidade",
                    title=coluna,
                    color_discrete_sequence=[
                        CORES[(indice - 1) % len(CORES)]
                    ],
                )

            elif tipo == "data":
                fig = px.histogram(
                    df,
                    x=coluna,
                    nbins=12,
                    title=coluna,
                    color_discrete_sequence=[
                        CORES[(indice - 1) % len(CORES)]
                    ],
                )

            else:
                fig = px.histogram(
                    df,
                    x=coluna,
                    nbins=12,
                    title=coluna,
                    color_discrete_sequence=[
                        CORES[(indice - 1) % len(CORES)]
                    ],
                )

            fig.update_layout(
                template="plotly_white",
                height=450,
            )

            imagem = fig.to_image(
                format="png",
                width=1200,
                height=700,
                scale=2,
            )

            zip_saida.writestr(
                f"{indice:02d}_{nome_seguro}.png",
                imagem,
            )

    arquivo_zip.seek(0)
    return arquivo_zip.getvalue()