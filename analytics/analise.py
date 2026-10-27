
import re
import unicodedata

import pandas as pd


TERMOS_PROTEGIDOS = (
    "nome", "cpf", "matricula", "email", "telefone", "celular",
    "endereco", "nascimento", "identidade", "passaporte",
)


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


def contar_categorias(df, coluna):
    """Conta os registros de cada categoria."""
    if coluna not in df.columns:
        return pd.Series(dtype="int64")

    valores = (
        df[coluna]
        .astype(object)
        .fillna("Não informado")
        .astype(str)
        .str.strip()
    )
    valores = valores.replace(
        {"": "Não informado", "nan": "Não informado"}
    )

    return valores.value_counts().sort_values()


def preparar_dados_grafico(df, coluna, tipo, limite=10):
    """Prepara os dados editáveis sem alterar o DataFrame original."""

    if tipo == "categoria":
        contagem = contar_categorias(df, coluna)
        contagem = contagem.sort_values(
            ascending=False
        ).head(limite)

        dados = contagem.rename_axis(
            "Categoria"
        ).reset_index(name="Quantidade")

    else:
        valores = df[coluna].dropna()

        if tipo == "data":
            valores = pd.to_datetime(valores, errors="coerce").dropna()
        else:
            valores = pd.to_numeric(valores, errors="coerce").dropna()

        if valores.empty:
            return pd.DataFrame(
                columns=["Categoria", "Quantidade"]
            )

        quantidade_faixas = min(10, max(1, valores.nunique()))

        if valores.nunique() == 1:
            dados = pd.DataFrame({
                "Categoria": [str(valores.iloc[0])],
                "Quantidade": [len(valores)]
            })
        else:
            faixas = pd.cut(
                valores,
                bins=quantidade_faixas,
                duplicates="drop"
            )

            contagem = faixas.value_counts(sort=False)

            dados = pd.DataFrame({
                "Categoria": contagem.index.astype(str),
                "Quantidade": contagem.values
            })

    return dados.reset_index(drop=True)


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

