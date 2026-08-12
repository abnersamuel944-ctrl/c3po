import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from google import genai
from google.genai import types
import os
import re

# --- 1. CONFIGURAÇÃO E ESTILO ---
st.set_page_config(
    page_title="Workana Enterprise BI | Interactive Studio",
    page_icon="💎",
    layout="wide"
)

# Estilização CSS Dark Executive
st.markdown("""
<style>
    .main { background-color: #0b0f19; }
    .stMetric { background-color: #151c2c; padding: 18px; border-radius: 10px; border: 1px solid #1e293b; }
    .report-card { background-color: #151c2c; padding: 25px; border-radius: 12px; border-left: 5px solid #38bdf8; margin-top: 15px; }
</style>
""", unsafe_allow_html=True)

# Autenticação segura da API
api_key = os.environ.get("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("🔑 Chave de API não configurada! Defina a variável GEMINI_API_KEY.")
    st.stop()

client = genai.Client(api_key=api_key)

# --- 2. PIPELINE DE LIMPEZA E ETL AUTOMÁTICO ---
def pipeline_etl(df_raw):
    """
    Higieniza a planilha automaticamente:
    - Trata nomes de colunas
    - Converte moedas (R$, $) e números formatados em texto para Float
    - Remove linhas totalmente vazias
    - Tenta identificar datas automaticamente
    """
    df = df_raw.copy()
    
    # 1. Limpeza de cabeçalhos
    df.columns = [str(col).strip().replace(" ", "_").lower() for col in df.columns]
    
    # 2. Remoção de linhas nulas completas
    df.dropna(how='all', inplace=True)
    
    # 3. Tratamento de colunas de texto com valores numéricos ou moeda
    for col in df.columns:
        if df[col].dtype == 'object':
            amostra = df[col].dropna().astype(str)
            
            # Limpeza de moeda (ex: R$ 1.250,50 ou $1,250.50)
            if amostra.str.contains(r'R\$|\$', regex=True).any():
                df[col] = (df[col].astype(str)
                           .str.replace(r'[R\$\s]', '', regex=True)
                           .str.replace('.', '', regex=False)
                           .str.replace(',', '.', regex=False))
                df[col] = pd.to_numeric(df[col], errors='coerce')
            else:
                # Tenta converter para data se for padrão de data
                try:
                    df[col] = pd.to_datetime(df[col], errors='ignore')
                except Exception:
                    pass

    return df

# --- 3. CONSTRUTOR DE GRÁFICOS INTERATIVOS (PLOTLY) ---
def criar_dashboard_plotly(df):
    cols_num = df.select_dtypes(include=[np.number]).columns.tolist()
    cols_cat = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    col_chart1, col_chart2 = st.columns(2)
    
    # Gráfico 1: Linha de Tendência Interativa
    with col_chart1:
        if cols_num:
            val_col = cols_num[0]
            fig1 = px.line(
                df, y=val_col, title=f"📈 Evolução Temporal / Sequencial ({val_col.upper()})",
                template="plotly_dark", color_discrete_sequence=["#38bdf8"]
            )
            fig1.update_layout(paper_bgcolor="#151c2c", plot_bgcolor="#151c2c", hovermode="x unified")
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("Sem colunas numéricas suficientes para o gráfico de tendência.")

    # Gráfico 2: Distribuição por Categoria
    with col_chart2:
        if cols_cat and cols_num:
            cat_col = cols_cat[0]
            val_col = cols_num[0]
            df_grouped = df.groupby(cat_col)[val_col].sum().reset_index().head(8)
            
            fig2 = px.bar(
                df_grouped, x=cat_col, y=val_col, title=f"📊 Volume por Categoria ({cat_col.upper()})",
                template="plotly_dark", color_discrete_sequence=["#4ade80"]
            )
            fig2.update_layout(paper_bgcolor="#151c2c", plot_bgcolor="#151c2c")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Sem colunas categóricas suficientes para agrupamento.")

    col_chart3, col_chart4 = st.columns(2)

    # Gráfico 3: Rosca (SLA / Proporção)
    with col_chart3:
        if len(cols_cat) > 0:
            cat_col = cols_cat[0]
            top_counts = df[cat_col].value_counts().head(5)
            fig3 = px.pie(
                values=top_counts.values, names=top_counts.index,
                title=f"🍩 Proporção das Principais Categorias",
                hole=0.5, template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig3.update_layout(paper_bgcolor="#151c2c", plot_bgcolor="#151c2c")
            st.plotly_chart(fig3, use_container_width=True)

    # Gráfico 4: Matriz Correlacionada ou Barra Horizontal
    with col_chart4:
        if len(cols_num) > 1:
            val_col2 = cols_num[1]
            fig4 = px.histogram(
                df, x=val_col2, title=f"📊 Distribuição de Frequência ({val_col2.upper()})",
                template="plotly_dark", color_discrete_sequence=["#c084fc"]
            )
            fig4.update_layout(paper_bgcolor="#151c2c", plot_bgcolor="#151c2c")
            st.plotly_chart(fig4, use_container_width=True)

# --- 4. INTERFACE PRINCIPAL ---
st.title("💎 Workana Enterprise BI Studio")
st.caption("Solução Completa: Tratamento de Dados (ETL) + Visualização Interativa Plotly + Parecer de IA")

st.markdown("---")

arquivo = st.file_uploader("📥 Carregue a planilha da sua empresa (Excel ou CSV):", type=["xlsx", "csv"])

if arquivo is not None:
    try:
        # Carregamento bruto
        df_raw = pd.read_csv(arquivo) if arquivo.name.endswith('.csv') else pd.read_excel(arquivo)
        
        # Executa ETL
        df_clean = pipeline_etl(df_raw)
        
        st.success("✅ Planilha higienizada com sucesso! Erros de formatação e valores monetários foram ajustados.")
        
        # Exibição de Métricas Corporativas
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Linhas Processadas", f"{len(df_clean):,}")
        m2.metric("Colunas Sanitizadas", f"{len(df_clean.columns)}")
        m3.metric("Valores Nulos Tratados", f"{df_raw.isnull().sum().sum()}")
        m4.metric("Status do Pipeline", "Pronto / Higienizado")

        st.markdown("---")

        # Dashboard Plotly
        st.subheader("📊 Painel Interativo de Business Intelligence")
        criar_dashboard_plotly(df_clean)

        # Relatório de Inteligência Artificial
        st.markdown("---")
        st.subheader("📋 Relatório Analítico de Engenharia (IA Generativa)")

        if 'relatorio_executivo' not in st.session_state:
            with st.spinner("🧠 Gerando parecer analítico detalhado para a diretoria..."):
                prompt_sys = """
                Você é um Engenheiro de Dados Principal e Consultor de BI Sênior.
                Analise o resumo dos dados fornecidos e entregue um relatório profissional com:
                1. Visão Geral dos Resultados
                2. Principais Gargalos e Anomalias Identificadas
                3. Recomendação Estratégica
                Apresente os dados de forma elegante, direta e com foco no ROI do negócio.
                """
                
                resumo_dados = f"Colunas: {list(df_clean.columns)}\nEstatísticas:\n{df_clean.describe(include='all').to_string()}"
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=f"Analise este conjunto de dados:\n{resumo_dados}",
                    config=types.GenerateContentConfig(
                        system_instruction=prompt_sys,
                        temperature=0.2
                    )
                )
                st.session_state.relatorio_executivo = response.text

        st.markdown(f'<div class="report-card">{st.session_state.relatorio_executivo}</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Erro ao processar arquivo: {e}")