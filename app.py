from io import BytesIO
from pathlib import Path
from datetime import datetime
import re
import unicodedata
import zipfile
import pandas as pd
import plotly.express as px
import streamlit as st



BASE_DIR = Path(__file__).resolve().parent
ARQUIVO = BASE_DIR / "dados" / "forca_trabalho.xlsx"

st.set_page_config(
    page_title="Painel de Planilha",
    page_icon="📊",
    layout="wide"
)




CORES = ["#1769AA", "#13A66B", "#7048C8", "#087E9B", "#F08A24"]
TERMOS_PROTEGIDOS = (
    "nome", "cpf", "matricula", "email", "telefone", "celular",
    "endereco", "nascimento", "identidade", "passaporte",
)



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



def carregar_dados():
    """Lê a planilha Excel."""
    if not ARQUIVO.exists():
        return pd.DataFrame(), None

    try:
        dados = pd.read_excel(ARQUIVO, engine="openpyxl")
        dados.columns = [str(c).strip() for c in dados.columns]

        modificacao = datetime.fromtimestamp(
            ARQUIVO.stat().st_mtime
        )

        return dados, modificacao

    except Exception as erro:
        st.error(f"Erro ao ler a planilha: {erro}")
        return pd.DataFrame(), None


def contar_categorias(df, coluna):
    """Conta os registros de cada categoria."""
    if coluna not in df.columns:
        return pd.Series(dtype="int64")

    valores = (
        df[coluna]
        .fillna("Não informado")
        .astype(str)
        .str.strip()
    )

    valores = valores.replace(
        {"": "Não informado", "nan": "Não informado"}
    )

    return valores.value_counts().sort_values()


def normalizar_texto(valor):
    """Remove acentos para comparar nomes de colunas."""
    return "".join(
        caractere
        for caractere in unicodedata.normalize("NFKD", str(valor).lower())
        if not unicodedata.combining(caractere)
    )


def coluna_protegida(coluna):
    nome = normalizar_texto(coluna)
    return any(termo in nome for termo in TERMOS_PROTEGIDOS)


def coluna_identificadora(coluna):
    nome = normalizar_texto(coluna)
    termos = {"id", "codigo", "identificador", "protocolo"}
    tokens = set(re.findall(r"[a-z0-9]+", nome))
    return coluna_protegida(coluna) or bool(tokens & termos)


def criar_grafico(df, coluna, cor, tipo, limite=10):
    """Cria um gráfico adequado ao tipo de dado da coluna."""
    if tipo == "numérico":
        fig = px.histogram(
            df,
            x=coluna,
            nbins=12,
            color_discrete_sequence=[cor],
        )
        fig.update_xaxes(title=coluna)
        fig.update_yaxes(title="Registros")
    elif tipo == "data":
        fig = px.histogram(
            df,
            x=coluna,
            nbins=12,
            color_discrete_sequence=[cor],
        )
        fig.update_xaxes(title=coluna)
        fig.update_yaxes(title="Registros")
    else:
        contagem = contar_categorias(df, coluna).sort_values(ascending=False)
        contagem = contagem.head(limite).sort_values()
        grafico_df = (
            contagem.rename_axis("Categoria")
            .reset_index(name="Quantidade")
        )
        fig = px.bar(
            grafico_df,
            x="Quantidade",
            y="Categoria",
            orientation="h",
            text="Quantidade",
            color_discrete_sequence=[cor],
        )
        fig.update_traces(textposition="outside")
        fig.update_yaxes(title=None, automargin=True)
        fig.update_xaxes(title=None)

    fig.update_layout(
        height=280,
        margin=dict(l=8, r=16, t=12, b=8),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#12306B", size=11),
    )
    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False},
    )





def selecionar_graficos(df, limite=6):
    """
    Seleciona colunas informativas com base no nome,
    no conteúdo e na distribuição dos dados.
    """
    graficos = []
    candidatos = []
    total_linhas = len(df)

    if total_linhas < 2:
        return []

  
    prioridades = {
        "situacao": 10,
        "status": 10,
        "cargo": 9,
        "funcao": 9,
        "vinculo": 9,
        "lotacao": 9,
        "unidade": 8,
        "orgao": 8,
        "secretaria": 8,
        "escolaridade": 8,
        "tipo": 6,
        "categoria": 7,
        "grupo": 6,
        "setor": 8,
        "data": 5,
        "ano": 4,
        "mes": 4,
    }

    
    ignorar = {
        "observacao", "observacoes", "descricao",
        "complemento", "justificativa", "documento",
        "endereco", "email", "telefone", "celular",
        "nome", "cpf", "matricula", "identidade",
        "passaporte", "protocolo", "identificador",
    }

    for coluna in df.columns:
        nome = normalizar_texto(coluna)
        tokens = set(re.findall(r"[a-z0-9]+", nome))

        if coluna_identificadora(coluna):
            continue

        if any(termo in tokens for termo in ignorar):
            continue

        valores = df[coluna].dropna()

        if len(valores) < 2:
            continue

        quantidade = valores.nunique()
        if quantidade < 2:
            continue

        proporcao_unicos = quantidade / len(valores)

       
        if proporcao_unicos > 0.8:
            continue

     
        if pd.api.types.is_datetime64_any_dtype(valores):
            tipo = "data"

        elif pd.api.types.is_bool_dtype(valores):
            tipo = "categoria"

        elif pd.api.types.is_numeric_dtype(valores):
            tipo = "categoria" if quantidade <= 10 else "numérico"

        else:
            tipo = "categoria"

            
            max_categorias = max(
                30, int(total_linhas ** 0.5 * 2)
            )

            if quantidade > max_categorias:
                continue

    
        pontuacao = 0

        for termo, pontos in prioridades.items():
            if termo in tokens:
                pontuacao += pontos

    
        if tipo == "categoria":
            if 2 <= quantidade <= 10:
                pontuacao += 4
            elif quantidade <= 20:
                pontuacao += 2

       
        if proporcao_unicos > 0.5:
            pontuacao -= 3

        candidatos.append(
            (pontuacao, coluna, tipo, quantidade)
        )

    
    candidatos.sort(key=lambda item: item[0], reverse=True)

   
    termos_escolhidos = set()

    for pontuacao, coluna, tipo, quantidade in candidatos:
        if len(graficos) >= limite:
            break

        tokens = set(
            re.findall(r"[a-z0-9]+", normalizar_texto(coluna))
        )

       
        termos_relevantes = tokens & set(prioridades.keys())

        if termos_relevantes & termos_escolhidos:
            continue

        graficos.append((coluna, tipo))
        termos_escolhidos.update(termos_relevantes)

    return graficos



st.markdown("""
<div style="
    background: linear-gradient(100deg, #062b75, #0756b8);
    padding: 16px 22px;
    border-radius: 12px;
    color: white;
    margin-bottom: 14px;
">
    <div style="font-size: 27px; font-weight: 800;">
        📊 Painel da Planilha
    </div>
    <div style="font-size: 13px; margin-top: 3px;">
        Resumo e gráficos gerados com base nos dados disponíveis
    </div>
</div>
""", unsafe_allow_html=True)

arquivo_enviado = st.file_uploader(
    "Anexar planilha",
    type=["xlsx"],
    help="Selecione um arquivo Excel (.xlsx) para atualizar os dados do painel.",
    key="planilha_upload",
)

if arquivo_enviado is not None:
    conteudo = arquivo_enviado.getvalue()

    try:
        pd.read_excel(BytesIO(conteudo), engine="openpyxl")
    except Exception as erro:
        st.error(f"Não foi possível ler a planilha enviada: {erro}")
    else:
        try:
            arquivo_igual = (
                ARQUIVO.exists() and ARQUIVO.read_bytes() == conteudo
            )
            if not arquivo_igual:
                ARQUIVO.parent.mkdir(parents=True, exist_ok=True)
                ARQUIVO.write_bytes(conteudo)
        except OSError as erro:
            st.error(f"Não foi possível salvar a planilha enviada: {erro}")
        else:
            if not arquivo_igual:
                st.success("Planilha anexada e painel atualizado.")
                st.rerun()

# Carrega os dados
df, data_modificacao = carregar_dados()

if df.empty:
    st.error(
        "Não encontrei dados. Verifique o arquivo "
        "dados/forca_trabalho.xlsx."
    )
    st.stop()



graficos = selecionar_graficos(df)

if graficos:
    st.download_button(
        "Exportar gráficos (PNG)",
        data=exportar_graficos_png(df, graficos),
        file_name="graficos_planilha.zip",
        mime="application/zip",
        help="Baixa todos os gráficos do painel em arquivos PNG dentro de um ZIP.",
    )

    for inicio in range(0, len(graficos), 3):
        linha = st.columns(3, gap="medium")
        for posicao, (campo, tipo) in enumerate(graficos[inicio:inicio + 3]):
            with linha[posicao]:
                with st.container(border=True):
                    st.markdown(f"#### {campo}")
                    criar_grafico(
                        df,
                        campo,
                        CORES[(inicio + posicao) % len(CORES)],
                        tipo,
                    )
else:
    st.info(
        "Não há colunas adequadas para gerar gráficos. "
        "Verifique se a planilha contém dados variados."
    )



st.markdown("""
<div style="
    text-align: center;
    color: #47709e;
    font-size: 12px;
    padding: 8px 0;
">
    Painel gerado automaticamente a partir da planilha enviada.
</div>
""", unsafe_allow_html=True)


# Informações da fonte
with st.expander("Informações da atualização"):
    st.write(f"Arquivo: {ARQUIVO.name}")

    if data_modificacao:
        st.write(
            "Última modificação: "
            f"{data_modificacao:%d/%m/%Y às %H:%M:%S}"
        )

    st.write(
        "O painel verifica novamente a planilha a cada "
        "60 segundos."
    )

    st.caption(
        "Colunas com nomes que indicam dados pessoais ou identificadores "
        "são omitidas dos indicadores e gráficos."
    )