import streamlit as st
import pandas as pd
import os

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA & ESTILOS DE HQ
# ==============================================================================
st.set_page_config(
    page_title="Robô Especialista SAP - HQ Dinâmica",
    page_icon="🤖",
    layout="wide"
)

st.markdown("""
    <style>
    /* Estilização Geral do Painel */
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        border-left: 8px solid #0284c7;
        margin-bottom: 25px;
    }
    
    /* Moldura de Quadrinho (Tirinha) */
    .comic-panel {
        border: 4px solid #0f172a;
        border-radius: 8px;
        padding: 15px;
        background-color: #f8fafc;
        box-shadow: 5px 5px 0px #0f172a;
        margin-bottom: 20px;
        min-height: 280px;
    }
    .comic-tag {
        background-color: #0284c7;
        color: white;
        font-weight: bold;
        padding: 4px 8px;
        font-size: 12px;
        border-radius: 4px;
        margin-bottom: 8px;
        display: inline-block;
        border: 1px solid #0f172a;
    }
    .speech-bubble {
        background-color: #ffffff;
        border: 2px solid #0f172a;
        border-radius: 12px;
        padding: 10px;
        font-weight: 600;
        color: #0f172a;
        margin: 10px 0;
        box-shadow: 2px 2px 0px rgba(0,0,0,0.15);
    }
    .footnote-note {
        font-size: 11px;
        color: #64748b;
        font-style: italic;
        border-top: 1px dashed #cbd5e1;
        padding-top: 6px;
        margin-top: 8px;
    }

    /* Cards de Analistas */
    .junior-card { background-color: #f0fdf4; border-left: 5px solid #22c55e; padding: 15px; border-radius: 6px; margin-bottom: 10px; }
    .pleno-card { background-color: #fefce8; border-left: 5px solid #eab308; padding: 15px; border-radius: 6px; margin-bottom: 10px; }
    .senior-card { background-color: #fef2f2; border-left: 5px solid #ef4444; padding: 15px; border-radius: 6px; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="main-header">
        <h2 style="margin:0;">🤖 Robô Especialista SAP S/4HANA & Engenharia de Produção</h2>
        <p style="margin:5px 0 0 0; color: #94a3b8;">Gerador Dinâmico de Histórias em Quadrinhos e Diagnóstico Operacional</p>
    </div>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. ENGENHARIA DE PRODUÇÃO: CÁLCULO DA CURVA ABC
# ==============================================================================
def calcular_curva_abc(df):
    data = df.copy()
    if "valor_total" not in data.columns:
        data["valor_total"] = data["quantidade"] * data["valor_unitario"]
    data = data.sort_values(by="valor_total", ascending=False).reset_index(drop=True)
    faturamento_total = data["valor_total"].sum()
    if faturamento_total == 0:
        faturamento_total = 1  # Evita divisão por zero
    data["acumulado"] = data["valor_total"].cumsum()
    data["pct_acumulado"] = (data["acumulado"] / faturamento_total) * 100

    def classificar(pct):
        if pct <= 80: return 'A'
        elif pct <= 95: return 'B'
        else: return 'C'

    data["classe_abc"] = data["pct_acumulado"].apply(classificar)
    return data

# ==============================================================================
# 3. BARRA LATERAL (ENTRADA DE DADOS E TRATAMENTO SEGURO DE ERROS)
# ==============================================================================
st.sidebar.header("⚙️ Central de Parâmetros")

# Inicialização padrão da variável df_dados para EVITAR o NameError
df_dados = pd.DataFrame({
    "item": ["Chassi Principal", "Painel Eletrônico", "Suporte Lateral", "Cabo de Força", "Parafuso M6"],
    "quantidade": [50, 50, 100, 50, 1000],
    "valor_unitario": [1200.0, 800.0, 45.0, 30.0, 0.50]
})

arquivo_carregado = st.sidebar.file_uploader("📥 Envie a planilha (CSV/Excel/TXT):", type=["csv", "xlsx", "xls", "txt"])

if arquivo_carregado is not None:
    try:
        nome = arquivo_carregado.name.lower()
        if nome.endswith('.xlsx'):
            df_lido = pd.read_excel(arquivo_carregado, engine='openpyxl')
        elif nome.endswith('.xls'):
            df_lido = pd.read_excel(arquivo_carregado, engine='xlrd')
        else:
            try:
                df_lido = pd.read_csv(arquivo_carregado)
                if len(df_lido.columns) == 1:
                    arquivo_carregado.seek(0)
                    df_lido = pd.read_csv(arquivo_carregado, sep=';')
            except Exception:
                arquivo_carregado.seek(0)
                df_lido = pd.read_csv(arquivo_carregado, sep=None, engine='python')

        # --- PADRONIZAÇÃO DE COLUNAS (Evita KeyError) ---
        df_lido.columns = df_lido.columns.astype(str).str.strip().str.lower()
        
        mapeamento = {
            'qtd': 'quantidade',
            'qtd.': 'quantidade',
            'quant': 'quantidade',
            'quantidade_estoque': 'quantidade',
            'valor unitario': 'valor_unitario',
            'valor_unitário': 'valor_unitario',
            'valor unitário': 'valor_unitario',
            'preco_unitario': 'valor_unitario',
            'preço unitário': 'valor_unitario',
            'preco': 'valor_unitario',
            'preço': 'valor_unitario',
            'vl_unitario': 'valor_unitario'
        }
        df_lido = df_lido.rename(columns=mapeamento)

        if 'item' not in df_lido.columns:
            for col in ['produto', 'descricao', 'descrição', 'material', 'nome']:
                if col in df_lido.columns:
                    df_lido = df_lido.rename(columns={col: 'item'})
                    break
            if 'item' not in df_lido.columns:
                df_lido['item'] = "Item Sem Nome"

        if 'quantidade' in df_lido.columns and 'valor_unitario' in df_lido.columns:
            df_lido['quantidade'] = pd.to_numeric(df_lido['quantidade'], errors='coerce').fillna(0)
            df_lido['valor_unitario'] = pd.to_numeric(df_lido['valor_unitario'], errors='coerce').fillna(0.0)
            df_dados = df_lido
            st.sidebar.success("Arquivo processado e validado!")
        else:
            st.sidebar.warning("⚠️ Colunas 'quantidade' e 'valor_unitario' não encontradas. Usando dados padrão.")

    except Exception as e:
        st.sidebar.error(f"Erro ao ler o arquivo: {e}")

cenario_modulo = st.sidebar.selectbox(
    "Selecione o Módulo/Fluxo do Problema:",
    [
        "Gargalo de Produção (MD04, CO02, CO11N)",
        "Falta de Insumo / Compras (ME21N, MIGO)",
        "Atraso na Expedição / Vendas (VA01, VL01N)"
    ]
)

gargalo_texto = st.sidebar.text_input("Gargalo Específico Identificado:", "Falta de matéria-prima no Posto de Solda")

# Executa Cálculo ABC
df_abc = calcular_curva_abc(df_dados)
itens_A = df_abc[df_abc["classe_abc"] == 'A']["item"].tolist()
str_itens_A = ", ".join(itens_A) if itens_A else "Nenhum item A"

# ==============================================================================
# 4. MONTAGEM DINÂMICA DA HQ CONFORME O PROBLEMA
# ==============================================================================
banco_hq = {
    "Gargalo de Produção (MD04, CO02, CO11N)": {
        "q1_t": "QUADRO 1: Abertura SAP", "q1_f": "Preciso abrir o SAP Logon para verificar os atrasos da fábrica.", "q1_n": "Inicializando o SAP GUI no Windows.",
        "q2_t": "QUADRO 2: Login S/4HANA", "q2_f": "Conectando ao servidor de produção para checar as ordens.", "q2_n": "Autenticando no ambiente de produção.",
        "q3_t": "QUADRO 3: Tela Fiori", "q3_f": "Acessando a busca rápida para abrir a transação MD04.", "q3_n": "Navegação por comando rápido.",
        "q4_t": "QUADRO 4: Transação MD04", "q4_f": f"Na MD04 vejo o gargalo '{gargalo_texto}' afetando o item {str_itens_A}!", "q4_n": f"Prioridade Classe A: {str_itens_A}.",
        "q5_t": "QUADRO 5: CO02 & CO11N", "q5_f": "Reprogramando na CO02 e confirmando os apontamentos na CO11N!", "q5_n": "Reajuste de capacidade e baixa de insumos.",
        "q6_t": "QUADRO 6: Expedição", "q6_f": "Produção liberada e ordem finalizada para envio ao cliente!", "q6_n": "Projeto entregue no prazo."
    },
    "Falta de Insumo / Compras (ME21N, MIGO)": {
        "q1_t": "QUADRO 1: Ruptura de Estoque", "q1_f": "Identificamos parada de linha por falta de matérias-primas!", "q1_n": "Alerta de falta de insumos na fábrica.",
        "q2_t": "QUADRO 2: Login S/4HANA", "q2_f": "Acessando o módulo de Gestão de Materiais (MM).", "q2_n": "Conexão ao módulo de suprimentos.",
        "q3_t": "QUADRO 3: Tela Fiori", "q3_f": "Abrindo o aplicativo de Pedidos de Compra Emergenciais.", "q3_n": "Interface de compras.",
        "q4_t": "QUADRO 4: Transação ME21N", "q4_f": f"Gerando Pedido de Compra crítico para conter: '{gargalo_texto}'!", "q4_n": f"Comprando emergencialmente os itens {str_itens_A}.",
        "q5_t": "QUADRO 5: Entrada MIGO", "q5_f": "Registrando a entrada física dos materiais no depósito via MIGO.", "q5_n": "Recebimento físico e fiscal.",
        "q6_t": "QUADRO 6: Abastecimento", "q6_f": "Estoque abastecido e linha de produção liberada com sucesso!", "q6_n": "Fábrica abastecida."
    },
    "Atraso na Expedição / Vendas (VA01, VL01N)": {
        "q1_t": "QUADRO 1: Pedido do Cliente", "q1_f": "Cliente cobrando a entrega urgente do lote contratado!", "q1_n": "Pressão comercial por expedição.",
        "q2_t": "QUADRO 2: Login S/4HANA", "q2_f": "Acessando o módulo de Vendas e Distribuição (SD).", "q2_n": "Conexão ao módulo SD.",
        "q3_t": "QUADRO 3: Tela Fiori", "q3_f": "Digitando a transação de criação de Ordem de Venda.", "q3_n": "Abertura de transações comerciais.",
        "q4_t": "QUADRO 4: Transação VA01", "q4_f": f"Criando Ordem de Venda e superando a restrição de '{gargalo_texto}'!", "q4_n": f"Alocando estoque para {str_itens_A}.",
        "q5_t": "QUADRO 5: Remessa VL01N", "q5_f": "Gerando documento de saída e liberação de picking no armazém.", "q5_n": "Separação física de mercadorias.",
        "q6_t": "QUADRO 6: Nota & Envio", "q6_f": "Nota fiscal emitida e caminhão liberado para entrega ao cliente!", "q6_n": "Faturamento concluído."
    }
}

hq_atual = banco_hq[cenario_modulo]

# ==============================================================================
# 5. ABAS DA APLICAÇÃO
# ==============================================================================
tab_hq, tab_dados, tab_analistas = st.tabs(["🖼️ História em Quadrinhos Dinâmica", "📊 Curva ABC & Dados", "🎓 Orientações por Nível de Analista"])

# ------------------------------------------------------------------------------
# TAB 1: HISTÓRIA EM QUADRINHOS (ILUSTRADA + DINÂMICA)
# ------------------------------------------------------------------------------
with tab_hq:
    st.subheader("📰 Tira de Quadrinhos Gerada Dinamicamente")
    
    if os.path.exists("15487.png"):
        st.image("15487.png", caption="Tira Ilustrativa das Telas do SAP S/4HANA", use_container_width=True)
    
    st.markdown("---")
    st.subheader("🎨 Painel de Quadrinhos Interativo")

    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown(f'''
            <div class="comic-panel">
                <span class="comic-tag">{hq_atual["q1_t"]}</span>
                <div class="speech-bubble">💭 "{hq_atual["q1_f"]}"</div>
                <div class="footnote-note">* {hq_atual["q1_n"]}</div>
            </div>
            <div class="comic-panel">
                <span class="comic-tag">{hq_atual["q4_t"]}</span>
                <div class="speech-bubble">💭 "{hq_atual["q4_f"]}"</div>
                <div class="footnote-note">* {hq_atual["q4_n"]}</div>
            </div>
        ''', unsafe_allow_html=True)

    with c2:
        st.markdown(f'''
            <div class="comic-panel">
                <span class="comic-tag">{hq_atual["q2_t"]}</span>
                <div class="speech-bubble">💭 "{hq_atual["q2_f"]}"</div>
                <div class="footnote-note">* {hq_atual["q2_n"]}</div>
            </div>
            <div class="comic-panel">
                <span class="comic-tag">{hq_atual["q5_t"]}</span>
                <div class="speech-bubble">💭 "{hq_atual["q5_f"]}"</div>
                <div class="footnote-note">* {hq_atual["q5_n"]}</div>
            </div>
        ''', unsafe_allow_html=True)

    with c3:
        st.markdown(f'''
            <div class="comic-panel">
                <span class="comic-tag">{hq_atual["q3_t"]}</span>
                <div class="speech-bubble">💭 "{hq_atual["q3_f"]}"</div>
                <div class="footnote-note">* {hq_atual["q3_n"]}</div>
            </div>
            <div class="comic-panel">
                <span class="comic-tag">{hq_atual["q6_t"]}</span>
                <div class="speech-bubble">💭 "{hq_atual["q6_f"]}"</div>
                <div class="footnote-note">* {hq_atual["q6_n"]}</div>
            </div>
        ''', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# TAB 2: CURVA ABC & RESULTADOS DOS DADOS
# ------------------------------------------------------------------------------
with tab_dados:
    st.subheader("📊 Classificação da Curva ABC")
    st.dataframe(df_abc, use_container_width=True)
    st.info(f"💡 **Diagnóstico de Engenharia:** Os itens críticos de Classe A que exigem prioridade total são: **{str_itens_A}**.")

# ------------------------------------------------------------------------------
# TAB 3: DIRETRIZES PARA ANALISTAS (JÚNIOR, PLENO E SÊNIOR)
# ------------------------------------------------------------------------------
with tab_analistas:
    st.subheader("🎯 Plano de Ação por Nível de Experiência")
    
    st.markdown(f"""
        <div class="junior-card">
            <h4>🟢 Analista Júnior (Operacional)</h4>
            <ul>
                <li><b>Execução:</b> Realizar as consultas nas transações do fluxo selecionado (ex: MD04/ME21N/VA01).</li>
                <li><b>Acompanhamento:</b> Atualizar as datas das ordens e repassar os status de progresso para a liderança.</li>
            </ul>
        </div>
        
        <div class="pleno-card">
            <h4>🟡 Analista Pleno (Tático)</h4>
            <ul>
                <li><b>Gargalo Atual:</b> Resolver o impacto do problema <i>'{gargalo_texto}'</i> focado nos itens Classe A (<b>{str_itens_A}</b>).</li>
                <li><b>Parâmetros:</b> Ajustar o estoque de segurança, lotes de compras e tempos de reposição na MM02.</li>
            </ul>
        </div>

        <div class="senior-card">
            <h4>🔴 Analista Sênior / Especialista (Estratégico)</h4>
            <ul>
                <li><b>Gargalos de Capacidade:</b> Executar o nivelamento de carga nos Centros de Trabalho via transação CM25.</li>
                <li><b>Automação:</b> Ativar o planejamento de necessidades automatizado (MD01N) e reequilibrar o plano mestre de produção.</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)