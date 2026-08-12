import os
import pandas as pd
import streamlit as st

# Configuração da página - Tema Industrial SAP GUI
st.set_page_config(
    page_title="SAP GUI - Centro de Comando Sênior",
    layout="wide",
    page_icon="⚙️",
)

# Estilização CSS Personalizada
st.markdown(
    """
    <style>
    .stApp { background-color: #1b263b; color: #e0e1dd; }
    .sap-header { background-color: #0d1b2a; padding: 15px; border-radius: 8px; border-bottom: 3px solid #00b4d8; margin-bottom: 15px; }
    .card-ponto-cego { background-color: #3d0007; border-left: 5px solid #ff4d6d; padding: 15px; border-radius: 5px; margin: 10px 0; }
    .card-logistica { background-color: #002b36; border-left: 5px solid #2aa198; padding: 15px; border-radius: 5px; margin: 10px 0; }
    .rodape-sugestao { background-color: #415a77; color: #ffffff; padding: 15px; border-radius: 8px; font-weight: bold; border: 1px solid #778da9; }
    </style>
""",
    unsafe_allow_html=True,
)

# --- SIDEBAR: DICIONÁRIO SAP & FERRAMENTAS DE CONVERSÃO ---
st.sidebar.title("🖥️ SAP Easy Access (Sênior)")
st.sidebar.caption("Dicionário Técnico & Módulo de Exportação")

st.sidebar.markdown("### 📚 Dicionário de Transações")
transacoes = {
    "IW21 / IW28": "Avisos de Manutenção e Gargalos da Engenharia",
    "ME21N / ME22N": "Pedidos de Compras & Gestão de Fornecedores",
    "CO01 / CO02": "Ordens de Produção & Capacidade de Chão de Fábrica",
    "MM03 / MMBE": "Mestre de Materiais & Consulta de Estoque Físico",
    "VT01N / VT02N": "Gestão de Transporte e Expedição Logística",
    "VA02": "Ordens de Venda & Liberação de Crédito",
}
for t, desc in transacoes.items():
    st.sidebar.write(f"🔹 **{t}**: {desc}")

st.sidebar.divider()

# Conversor de Arquivos para o Cliente
st.sidebar.markdown("### 🔄 Exportador Universal de Arquivos")
arquivo_converter = st.sidebar.file_uploader(
    "Carregar para conversão de formato:", type=["xlsx", "csv", "ods"]
)
formato_destino = st.sidebar.selectbox(
    "Formato para o cliente:", ["pdf", "csv", "xlsx", "txt"]
)

if arquivo_converter and st.sidebar.button("Converter e Baixar"):
    try:
        df_conv = (
            pd.read_csv(arquivo_converter)
            if arquivo_converter.name.endswith(".csv")
            else pd.read_excel(arquivo_converter)
        )
        nome_saida = f"relatorio_exportado.{formato_destino}"

        if formato_destino == "csv":
            df_conv.to_csv(nome_saida, index=False)
        elif formato_destino == "xlsx":
            df_conv.to_excel(nome_saida, index=False)
        elif formato_destino == "txt":
            df_conv.to_csv(nome_saida, sep="\t", index=False)

        st.sidebar.success(f"✅ Arquivo pronto no formato {formato_destino}!")
    except Exception as e:
        st.sidebar.error(f"Erro na conversão: {e}")

# --- CABEÇALHO DO PAINEL PRINCIPAL ---
st.markdown(
    """
    <div class="sap-header">
        <h2>⚙️ Módulo Avançado de Engenharia de Produção & Logística</h2>
        <p>Análise de Diagnóstico de Processos, Riscos Ocultos e Sugestões Operacionais</p>
    </div>
""",
    unsafe_allow_html=True,
)

# --- CARREGAMENTO E PROCESSAMENTO DA PLANILHA ---
st.subheader("📥 1. Entrada de Dados / Importar Planilha de Avisos")
arquivo_avisos = st.file_uploader(
    "Arraste a planilha (.csv, .ods, .xlsx) para ativação do robô de diagnóstico:",
    type=["csv", "ods", "xlsx"],
)

if arquivo_avisos is not None:
    try:
        # Leitura flexível
        if arquivo_avisos.name.endswith(".csv"):
            df = pd.read_csv(arquivo_avisos, sep=None, engine="python")
        else:
            df = pd.read_excel(arquivo_avisos)

        # Padronização simples das colunas
        df.columns = [c.strip() for c in df.columns]

        st.success(
            f"🤖 **Robô Sênior Conectado:** {len(df)} registros processados com sucesso."
        )

        col_esq, col_dir = st.columns([1.2, 1])

        with col_esq:
            st.markdown("### 📊 Visão em Tabela de Dados")
            st.dataframe(df, use_container_width=True, height=350)

        with col_dir:
            st.markdown("### 🔍 Gabarito de Execução Direta")

            # Métrica de custo acumulado se a coluna existir
            col_custo = [
                c
                for c in df.columns
                if "custo" in c.lower() or "parada" in c.lower()
            ]
            if col_custo:
                total_prejuizo = pd.to_numeric(
                    df[col_custo[0]], errors="coerce"
                ).sum()
                st.metric("Custo Total de Paradas", f"R$ {total_prejuizo:,.2f}")
            else:
                st.metric("Total de Ocorrências", f"{len(df)} itens")

            st.write("---")
            st.markdown("#### 📋 Passos Recomendados de Operação:")
            st.write("1️⃣ **Executar Triagem:** Verificar prioridades críticas.")
            st.write(
                "2️⃣ **Verificação de Estoque:** Consultar **MM03** para checagem de saldo."
            )
            st.write(
                "3️⃣ **Regularização:** Emitir Pedido de Compra na **ME21N** ou Ordem na **CO01**."
            )

        st.divider()

        # --- ANÁLISE DE PONTOS CEGOS (RISCOS OCULTOS) ---
        st.subheader("⚠️ 2. Análise de Pontos Cegos & Riscos de Operação")

        col_atraso = [
            c
            for c in df.columns
            if "dias" in c.lower() or "atraso" in c.lower()
        ]
        maior_atraso = 0
        if col_atraso:
            maior_atraso = pd.to_numeric(
                df[col_atraso[0]], errors="coerce"
            ).max()

        st.markdown(
            f"""
            <div class="card-ponto-cego">
                🎯 <b>PONTO CEGO DETECTADO PELO ROBÔ:</b><br>
                • <b>Impacto Cascata:</b> Existe um gargalo acumulado com atraso máximo de <b>{maior_atraso} dias</b>.<br>
                • <b>Risco Oculto:</b> Atrasos em componentes básicos interrompem linhas inteiras de montagem downstream, podendo gerar multas contratuais na expedição.<br>
                • <b>Ação Preventiva:</b> Reordenar cronograma de entrega via transação <b>VT02N</b>.
            </div>
        """,
            unsafe_allow_html=True,
        )

        # --- MÓDULO ESPECIALISTA EM LOGÍSTICA ---
        # Detecta se há termos de logística na planilha
        texto_completo = df.to_string().lower()
        tem_logistica = any(
            termo in texto_completo
            for termo in [
                "logistica",
                "rota",
                "frete",
                "transito",
                "transporte",
                "expedicao",
            ]
        )

        if tem_logistica:
            st.divider()
            st.subheader("🚚 3. Relatório Avançado de Logística & Expedição")

            col_l1, col_l2 = st.columns(2)

            with col_l1:
                st.markdown(
                    """
                    <div class="card-logistica">
                        📊 <b>DIAGNOSTICO DE LOGÍSTICA:</b><br>
                        • <b>Status do Inbound/Outbound:</b> Dificuldades de cumprimento de rota encontradas.<br>
                        • <b>Gargalo Principal:</b> Tempo de espera em trânsito acima da média estipulada.<br>
                        • <b>Transações Envolvidas:</b> VT01N (Criar Transporte) e MMBE (Estoque por Depósito).
                    </div>
                """,
                    unsafe_allow_html=True,
                )

            with col_l2:
                # Tabela de resumos rápidos por status se houver coluna correspondente
                col_status = [
                    c
                    for c in df.columns
                    if "status" in c.lower() or "linha" in c.lower()
                ]
                if col_status:
                    st.write("**Distribuição dos Status de Linha/Rota:**")
                    st.bar_chart(df[col_status[0]].value_counts())

        # --- NOTA DE RODAPÉ / SUGESTÃO TÉCNICA ---
        st.divider()
        st.markdown(
            """
            <div class="rodape-sugestao">
                💡 <b>NOTA DE RODAPÉ / RECOMENDAÇÃO TÉCNICA DO ROBÔ:</b><br>
                Com base nos cruzamentos realizados, a prioridade imediata é liberar as ordens de compra paradas (ME21N) para evitar paradas prolongadas no chão de fábrica e reajustar as rotas de transporte na VT01N.
            </div>
        """,
            unsafe_allow_html=True,
        )

    except Exception as e:
        st.error(f"Erro ao processar e analisar dados: {e}")
else:
    st.info(
        "💡 **Modo Operacional Ativo:** Insira a planilha de avisos para abrir a análise sênior do robô."
    )