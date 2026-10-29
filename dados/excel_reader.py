from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent.parent
ARQUIVO = BASE_DIR / "dados" / "forca_trabalho.xlsx"
MAX_LINHAS_CABECALHO = 40


def detectar_linha_cabecalho(bruto):
    """Estima a linha de títulos pela estrutura, sem nomes de colunas fixos."""
    candidatos = []

    for indice, linha in bruto.iterrows():
        valores = [
            valor
            for valor in linha
            if not pd.isna(valor) and str(valor).strip()
        ]
        if len(valores) < 2:
            continue

        valores_textuais = sum(isinstance(valor, str) for valor in valores)
        colunas_preenchidas = len(valores)
        valores_distintos = len({str(valor).strip().casefold() for valor in valores})
        candidatos.append(
            (
                colunas_preenchidas,
                valores_distintos,
                valores_textuais,
                -indice,
                indice,
            )
        )

    if not candidatos:
        raise ValueError(
            "Não foi possível identificar uma linha de títulos com "
            "pelo menos duas células preenchidas."
        )

    return max(candidatos)[-1]


def ler_planilha_excel(arquivo):
    """Lê uma planilha e detecta automaticamente a linha de cabeçalho."""
    bruto = pd.read_excel(
        arquivo,
        header=None,
        nrows=MAX_LINHAS_CABECALHO,
        engine="openpyxl",
    )
    linha_cabecalho = detectar_linha_cabecalho(bruto)

    if hasattr(arquivo, "seek"):
        arquivo.seek(0)

    dados = pd.read_excel(
        arquivo,
        header=linha_cabecalho,
        engine="openpyxl",
    )
    dados.columns = [str(coluna).strip() for coluna in dados.columns]
    return dados, linha_cabecalho + 1


@st.cache_data(show_spinner="Carregando planilha...", ttl=60)
def ler_planilha(caminho, modificado_em):
    """Lê a planilha Excel e retorna um DataFrame."""
    try:
        dados, _ = ler_planilha_excel(caminho)
        return dados
    except Exception as erro:
        st.error(f"Erro ao ler a planilha: {erro}")
        return pd.DataFrame()


def carregar_dados():
    """Lê a planilha Excel."""
    if not ARQUIVO.exists():
        return pd.DataFrame(), None

    try:
        modificacao_ts = ARQUIVO.stat().st_mtime
        dados = ler_planilha(ARQUIVO, modificacao_ts)
        return dados, datetime.fromtimestamp(modificacao_ts)

    except Exception as erro:
        st.error(f"Erro ao ler a planilha: {erro}")
        return pd.DataFrame(), None