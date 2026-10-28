
from io import BytesIO
from datetime import datetime
from html import escape

import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


AZUL = "#0756B8"
AZUL_ESCURO = "#062B75"

PALETA = [
    ("#E5EFFB", "#1769AA"),
    ("#DFF3E6", "#16804A"),
    ("#FCEBD9", "#B96513"),
    ("#EEE6F8", "#7048C8"),
    ("#E3F1F5", "#087E9B"),
    ("#F8E7E5", "#B84040"),
]


def texto_seguro(valor):
    return escape(str(valor))


def numero(valor):
    return f"{valor:,.0f}".replace(",", ".")


def criar_cartao(titulo, valor, descricao, fundo, destaque, largura, estilos):
    elementos = [
        Paragraph(texto_seguro(titulo), estilos["cartao_titulo"]),
        Paragraph(
            texto_seguro(valor),
            ParagraphStyle(
                "ValorDestaque",
                parent=estilos["cartao_valor"],
                textColor=colors.HexColor(destaque),
            ),
        ),
        Paragraph(texto_seguro(descricao), estilos["cartao_descricao"]),
    ]

    tabela = Table([[elementos]], colWidths=[largura])

    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(fundo)),
        ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor(fundo)),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))

    return tabela


def criar_cartao_grafico(grafico, indice, largura, estilos):
    fundo, destaque = PALETA[indice % len(PALETA)]

    dados = grafico["dados"].copy()

    dados["Quantidade"] = pd.to_numeric(
        dados["Quantidade"], errors="coerce"
    )

    dados = dados.dropna(subset=["Categoria", "Quantidade"])
    dados = dados[dados["Categoria"].notna()]

    elementos = [
        Paragraph(
            texto_seguro(grafico["titulo"]),
            ParagraphStyle(
                f"TituloGrafico{indice}",
                parent=estilos["cartao_titulo"],
                fontSize=10,
                leading=12,
                textColor=colors.HexColor(destaque),
            ),
        ),
        Spacer(1, 4),
    ]

    if dados.empty:
        elementos.append(
            Paragraph("Nenhum dado disponível.", estilos["cartao_descricao"])
        )
    else:
        total = dados["Quantidade"].sum()

        elementos.extend([
            Paragraph(
                numero(total),
                ParagraphStyle(
                    f"TotalGrafico{indice}",
                    parent=estilos["cartao_valor"],
                    fontSize=19,
                    leading=22,
                    textColor=colors.HexColor(destaque),
                ),
            ),
            Paragraph("Total exibido", estilos["cartao_descricao"]),
            Spacer(1, 5),
        ])

        principais = dados.nlargest(4, "Quantidade")

        for _, linha in principais.iterrows():
            categoria = texto_seguro(linha["Categoria"])
            quantidade = linha["Quantidade"]

            percentual = (
                quantidade / total * 100 if total > 0 else 0
            )

            linha_tabela = Table(
                [[
                    Paragraph(
                        categoria,
                        estilos["categoria"],
                    ),
                    Paragraph(
                        f"<b>{numero(quantidade)}</b>",
                        estilos["quantidade"],
                    ),
                ]],
                colWidths=[largura * 0.69, largura * 0.25],
            )

            linha_tabela.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))

            elementos.append(linha_tabela)

            elementos.append(
                Paragraph(
                    f"{percentual:.1f}% do total exibido",
                    estilos["percentual"],
                )
            )

    cartao = Table([[elementos]], colWidths=[largura])

    cartao.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(fundo)),
        ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#D9E2EC")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))

    return cartao


def gerar_relatorio_pdf(
    df,
    graficos,
    titulo="Força de Trabalho MESP",
):
    buffer = BytesIO()

    documento = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=0.8 * cm,
        leftMargin=0.8 * cm,
        topMargin=0.7 * cm,
        bottomMargin=0.8 * cm,
        title=titulo,
    )

    estilos_base = getSampleStyleSheet()

    estilos = {
        "cabecalho": ParagraphStyle(
            "Cabecalho",
            parent=estilos_base["Title"],
            fontSize=19,
            leading=22,
            textColor=colors.white,
            alignment=0,
            spaceAfter=3,
        ),
        "subtitulo": ParagraphStyle(
            "Subtitulo",
            parent=estilos_base["Normal"],
            fontSize=8,
            leading=11,
            textColor=colors.white,
        ),
        "secao": ParagraphStyle(
            "Secao",
            parent=estilos_base["Heading2"],
            fontSize=11,
            leading=13,
            textColor=colors.HexColor(AZUL_ESCURO),
            spaceBefore=5,
            spaceAfter=5,
        ),
        "cartao_titulo": ParagraphStyle(
            "CartaoTitulo",
            parent=estilos_base["Normal"],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#334155"),
            spaceAfter=3,
        ),
        "cartao_valor": ParagraphStyle(
            "CartaoValor",
            parent=estilos_base["Title"],
            fontSize=21,
            leading=24,
            alignment=0,
            spaceAfter=1,
        ),
        "cartao_descricao": ParagraphStyle(
            "CartaoDescricao",
            parent=estilos_base["Normal"],
            fontSize=7,
            leading=9,
            textColor=colors.HexColor("#475569"),
        ),
        "categoria": ParagraphStyle(
            "Categoria",
            parent=estilos_base["Normal"],
            fontSize=7,
            leading=9,
            textColor=colors.HexColor("#263445"),
            wordWrap="CJK",
        ),
        "quantidade": ParagraphStyle(
            "Quantidade",
            parent=estilos_base["Normal"],
            fontSize=7,
            leading=9,
            alignment=2,
        ),
        "percentual": ParagraphStyle(
            "Percentual",
            parent=estilos_base["Normal"],
            fontSize=6,
            leading=7,
            textColor=colors.HexColor("#64748B"),
            spaceAfter=2,
        ),
    }

    largura_util = landscape(A4)[0] - 1.6 * cm
    conteudo = []

    # Cabeçalho azul
    data_geracao = datetime.now().strftime("%d/%m/%Y às %H:%M")

    cabecalho = Table(
        [[
            [
                Paragraph(texto_seguro(titulo), estilos["cabecalho"]),
                Paragraph(
                    "Resumo visual gerado automaticamente",
                    estilos["subtitulo"],
                ),
            ],
            Paragraph(
                f"Atualizado em<br/>{data_geracao}",
                estilos["subtitulo"],
            ),
        ]],
        colWidths=[largura_util * 0.76, largura_util * 0.24],
    )

    cabecalho.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(AZUL)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))

    conteudo.extend([cabecalho, Spacer(1, 6)])


    # Cartões dos gráficos
    conteudo.append(
        Paragraph("DISTRIBUIÇÃO DOS INDICADORES", estilos["secao"])
    )

    if graficos:
        espacamento_cartao = 0.15 * cm
        largura_cartao = (largura_util - 2 * espacamento_cartao) / 3

        cartoes = [
            criar_cartao_grafico(
                grafico,
                indice,
                largura_cartao,
                estilos,
            )
            for indice, grafico in enumerate(graficos)
        ]

        for inicio in range(0, len(cartoes), 3):
            grupo = cartoes[inicio:inicio + 3]

            larguras = [largura_cartao] * len(grupo)

            linha = Table(
                [grupo],
                colWidths=larguras,
            )

            linha.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))

            conteudo.extend([linha, Spacer(1, 4)])

    else:
        conteudo.append(
            Paragraph(
                "Não foram encontrados indicadores para apresentar.",
                estilos["cartao_descricao"],
            )
        )

    def rodape(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#47709E"))

        canvas.drawString(
            0.9 * cm,
            0.4 * cm,
            "Painel gerado automaticamente a partir dos dados disponíveis.",
        )

        canvas.drawRightString(
            landscape(A4)[0] - 0.9 * cm,
            0.4 * cm,
            f"Página {doc.page}",
        )

        canvas.restoreState()

    documento.build(
        conteudo,
        onFirstPage=rodape,
        onLaterPages=rodape,
    )

    buffer.seek(0)
    return buffer.getvalue()
