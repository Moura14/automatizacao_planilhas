import streamlit as st

from analytics.analise import preparar_dados_grafico, selecionar_graficos
from dados.excel_reader import ARQUIVO, carregar_dados, ler_planilha_excel
from export.png_export import exportar_graficos_png
from visualization.graficos import criar_grafico_editavel
from gerar_pdf import gerar_relatorio_pdf


CORES = ["#1769AA", "#13A66B", "#7048C8", "#087E9B", "#F08A24"]


def _limpar_estado_graficos():
    prefixos = (
        "titulo_",
        "tipo_",
        "cor_",
        "dados_",
        "grafico_",
        "excluir_",
    )
    for chave in list(st.session_state.keys()):
        if chave.startswith(prefixos):
            del st.session_state[chave]

    st.session_state["graficos_excluidos"] = set()
    st.session_state.pop("chave_exportacao_graficos_png", None)
    st.session_state.pop("arquivo_exportacao_graficos_png", None)
    st.session_state.pop("download_resumo_pdf", None)


def exibir_painel():

    graficos_pdf = []
    if "graficos_excluidos" not in st.session_state:
        st.session_state["graficos_excluidos"] = set()
    if "upload_selecionado_antes" not in st.session_state:
        st.session_state["upload_selecionado_antes"] = False
    if "planilha_upload_removida" not in st.session_state:
        st.session_state["planilha_upload_removida"] = True

    st.markdown(
        """
        <div style="
            background: linear-gradient(100deg, #062b75, #0756b8);
            padding: 12px 22px;
            border-radius: 12px;
            color: white;
            margin-bottom: 14px;
        ">
            <div style="font-size: 13px;">
                Resumo e gráficos gerados com base nos dados disponíveis
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    arquivo_enviado = st.file_uploader(
        "Anexar planilha",
        type=["xlsx"],
        help="Selecione um arquivo Excel (.xlsx) para atualizar os dados.",
        key="planilha_upload",
    )

    if arquivo_enviado is None:
        if st.session_state["upload_selecionado_antes"]:
            _limpar_estado_graficos()
            st.session_state["planilha_upload_removida"] = True
        st.session_state["upload_selecionado_antes"] = False
    else:
        if not st.session_state["upload_selecionado_antes"]:
            _limpar_estado_graficos()
            st.session_state["planilha_upload_removida"] = False
        st.session_state["upload_selecionado_antes"] = True

    if "nome_planilha" not in st.session_state:
        st.session_state["nome_planilha"] = ARQUIVO.stem

    if arquivo_enviado is not None:
        st.session_state["nome_planilha"] = arquivo_enviado.name.rsplit(".", 1)[0]


    nome_planilha = None

    if arquivo_enviado is not None:
        conteudo = arquivo_enviado.getvalue()
        nome_planilha = arquivo_enviado.name.rsplit(".", 1)[0]

        try:
            _, linha_cabecalho = ler_planilha_excel(
                arquivo_enviado
            )
            st.caption(
                f"Linha de títulos identificada: {linha_cabecalho}."
            )
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

    df, data_modificacao = carregar_dados()

    if df.empty:
        st.error(
            "Não encontrei dados. Verifique o arquivo "
            "dados/forca_trabalho.xlsx."
        )
        st.stop()

    graficos = (
        []
        if st.session_state["planilha_upload_removida"]
        else selecionar_graficos(df)
    )
    graficos = [
    (campo, tipo)
    for campo, tipo in graficos
    if f"{campo}_{tipo}" not in st.session_state["graficos_excluidos"]
]

    if graficos:
        chave_exportacao = (data_modificacao, tuple(graficos))
        if (
            st.session_state.get("chave_exportacao_graficos_png")
            != chave_exportacao
        ):
            st.session_state["chave_exportacao_graficos_png"] = (
                chave_exportacao
            )
            st.session_state["arquivo_exportacao_graficos_png"] = None


        if st.session_state.get("arquivo_exportacao_graficos_png") is not None:
            st.download_button(
                "📥 Baixar gráficos (PNG)",
                data=st.session_state["arquivo_exportacao_graficos_png"],
                file_name="graficos_planilha.zip",
                mime="application/zip",
                help=(
                    "Baixa todos os gráficos do painel em arquivos PNG "
                    "dentro de um ZIP."
                ),
            )

        for inicio in range(0, len(graficos), 3):
            linha = st.columns(3, gap="medium")

            for posicao, (campo, tipo) in enumerate(
                graficos[inicio:inicio + 3]
            ):
                indice = inicio + posicao
                chave = f"{indice}_{campo}"

                with linha[posicao]:
                    with st.container(border=True):
                        

                        with st.expander("✏️ Editar gráfico"):
                            titulo = st.text_input(
                                "Título",
                                value=campo,
                                key=f"titulo_{chave}",
                            )
                            tipo_grafico = st.selectbox(
                                "Tipo de gráfico",
                                ["Barras", "Pizza"],
                                key=f"tipo_{chave}",
                            )
                            cor = st.color_picker(
                                "Cor do gráfico",
                                value=CORES[indice % len(CORES)],
                                key=f"cor_{chave}",
                            )

                            dados_originais = preparar_dados_grafico(
                                df, campo, tipo
                            )
                            st.caption(
                                "Edite os nomes e valores abaixo. "
                                "Essas mudanças afetam apenas o gráfico."
                            )
                            dados_editados = st.data_editor(
                                dados_originais,
                                num_rows="dynamic",
                                hide_index=True,
                                use_container_width=True,
                                key=f"dados_{chave}",
                                column_config={
                                    "Categoria": st.column_config.TextColumn(
                                        "Categoria",
                                        required=False,
                                    ),
                                    "Quantidade": (
                                        st.column_config.NumberColumn(
                                            "Quantidade",
                                            min_value=0,
                                            step=1,
                                            required=False,
                                        )
                                    ),
                                },
                            )

                            dados_para_grafico = dados_editados.dropna(
                            subset=["Categoria", "Quantidade"]
                        ).copy()

                        dados_para_grafico = dados_para_grafico[
                            dados_para_grafico["Categoria"].astype(str).str.strip().ne("")
]

                        if st.button(
                            "🗑️ Excluir gráfico",
                            key=f"excluir_{chave}",
                            use_container_width=True,
                        ):
                            st.session_state["graficos_excluidos"].add(
                                f"{campo}_{tipo}"
                            )
                            st.rerun()

                        criar_grafico_editavel(
                            dados_para_grafico,
                            titulo,
                            tipo_grafico,
                            cor,
                            chave,
                        )

                        graficos_pdf.append({
                            "titulo": titulo,
                            "tipo": tipo_grafico,
                            "cor": cor,
                            "dados": dados_para_grafico.copy(),
                        })

    elif st.session_state["planilha_upload_removida"]:
        st.info("Planilha removida. Anexe outra planilha para gerar gráficos.")
    else:
        st.info(
            "Não há colunas adequadas para gerar gráficos. "
            "Verifique se a planilha contém dados variados."
        )

        
    if graficos_pdf:
        st.divider()
        st.subheader("📄 Resumo visual em PDF")

        if st.button("Gerar relatório em PDF"):
            try:
                

                pdf = gerar_relatorio_pdf(
                    df=df,
                    graficos=graficos_pdf,
                    titulo=f"Relatório - {st.session_state['nome_planilha']}",
                )

                st.download_button(
                    label="⬇️ Baixar resumo em PDF",
                    data=pdf,
                    file_name="resumo_forca_trabalho.pdf",
                    mime="application/pdf",
                    key="download_resumo_pdf",
                )

            except Exception as erro:
                st.error(f"Erro ao gerar o PDF: {erro}")


    st.markdown(
        """
        <div style="
            text-align: center;
            color: #47709e;
            font-size: 12px;
            padding: 8px 0;
        ">
            Painel gerado automaticamente a partir da planilha enviada.
        </div>
        """,
        unsafe_allow_html=True,
    )
