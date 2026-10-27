from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent.parent
ARQUIVO = BASE_DIR / "dados" / "forca_trabalho.xlsx"



@st.cache_data(show_spinner="Carregando planilha...", ttl=60)
def ler_planilha(caminho, modificado_em):
    """Lê a planilha Excel e retorna um DataFrame."""
    try:

        bruto = pd.read_excel(caminho, header=None, engine="openpyxl")

        termos_cabecalho = [
            "nome", "cpf", "matricula", "email", "telefone", "celular",
            "endereco", "nascimento", "identidade", "passaporte",
        ]


        dados = pd.read_excel(caminho, engine="openpyxl")
        dados.columns = [str(c).strip() for c in dados.columns]
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