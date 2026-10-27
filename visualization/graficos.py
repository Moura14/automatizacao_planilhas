import pandas as pd
import plotly.express as px
import streamlit as st



def criar_grafico_editavel(
    dados,
    titulo,
    tipo_grafico,
    cor,
    chave
):
    """Exibe o gráfico usando os dados editáveis do painel."""

    if dados.empty:
        st.warning("Não existem dados para exibir neste gráfico.")
        return

    dados = dados.copy()
    dados["Categoria"] = dados["Categoria"].astype(str)
    dados["Quantidade"] = pd.to_numeric(
        dados["Quantidade"], errors="coerce"
    ).fillna(0)

    if tipo_grafico == "Pizza":
        fig = px.pie(
            dados,
            names="Categoria",
            values="Quantidade",
            title=titulo,
            color_discrete_sequence=[cor],
        )
    else:
        fig = px.bar(
            dados,
            x="Quantidade",
            y="Categoria",
            orientation="h",
            text="Quantidade",
            title=titulo,
            color_discrete_sequence=[cor],
        )
        fig.update_traces(textposition="outside")
        fig.update_yaxes(title=None, automargin=True)
        fig.update_xaxes(title="Quantidade")

    fig.update_layout(
        height=350,
        template="plotly_white",
        yaxis=dict(autorange="reversed"),
        margin=dict(l=8, r=20, t=55, b=15),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key=f"grafico_{chave}",
        config={"displayModeBar": True},
    )