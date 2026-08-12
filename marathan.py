import streamlit as st
import pandas as pd
from google import genai
from google.genai import types
import os

st.set_page_config(page_title="Assistente Manthan MWS - Logística", layout="wide")

# --- 1. GERENCIAMENTO SEGURO DA CHAVE DE API ---
api_key = os.environ.get("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("🔑 Chave da API do Gemini não encontrada! Configure a variável GEMINI_API_KEY.")
    st.stop()

client = genai.Client(api_key=api_key)

# Reset de estado ao trocar de módulo
def resetar_jornada():
    if 'passos_guia' in st.session_state:
        del st.session_state.passos_guia
        del st.session_state.passo_atual

st.title("📦 Assistente Especialista em Manthan MWS (Logística)")

col_left, col_right = st.columns([1, 2])

with col_left:
    modulo_mws = st.selectbox(
        "Qual módulo do Manthan MWS você quer operar hoje?",
        [
            "Manthan MWS - Inbound (Recebimento & Guarda/Putaway)",
            "Manthan MWS - Outbound (Onda de Picking & Expedição)",
            "Manthan MWS - Gestão de Estoque & Inventário Cíclico",
            "Manthan MWS - Gestão de Pátio & Agendamento de Docas"
        ],
        on_change=resetar_jornada
    )
    
    arquivo_uploaded = st.file_uploader("Envie a planilha de operações (Excel ou CSV):", type=["xlsx", "csv"])

# --- 2. DICIONÁRIO DE LOGÍSTICA E WMS ---
DICIONARIO_WMS = {
    "sku": ["SKU", "Codigo_Produto", "Item", "Material", "Cod_Item"],
    "quantidade": ["Qtd", "Quantidade", "Volume", "Caixas", "Unidades", "Qtd_Esperada"],
    "endereco": ["Endereco", "Posicao", "Rua", "Loc", "Localizacao", "Bin"],
    "lote": ["Lote", "Batch", "Validade", "Serial"],
    "ordem_picking": ["Onda", "Wave", "Pedido", "Ordem_Separacao", "Carga"]
}

def padronizar_planilha(df):
    renomear = {}
    for col in df.columns:
        for chave, sinonimos in DICIONARIO_WMS.items():
            if str(col).strip() in sinonimos:
                renomear[col] = chave
    return df.rename(columns=renomear)

# --- 3. PROCESSAMENTO COM O GEMINI (ESPECIALISTA MANTHAN MWS) ---
if arquivo_uploaded is not None:
    try:
        if arquivo_uploaded.name.endswith('.csv'):
            df = pd.read_csv(arquivo_uploaded)
        else:
            df = pd.read_excel(arquivo_uploaded)
        
        df_padronizado = padronizar_planilha(df)
        st.success("Planilha de logística carregada e mapeada para a estrutura do Manthan MWS!")
        
        resumo_dados = f"Total de itens/registros: {len(df_padronizado)}\n"
        resumo_dados += f"Colunas identificadas: {list(df_padronizado.columns)}\n"
        resumo_dados += f"Amostra dos dados operacionais:\n{df_padronizado.head(5).to_string()}"

        system_instruction = f"""
        Você é um Especialista Sênior no sistema de WMS 'Manthan MWS' focado em Logística e Operações de Armazém.
        Sua personalidade é extremamente prática, didática, amigável e focada na rotina de armazém/centro de distribuição (CD).
        
        Módulo Atual Selecionado: {modulo_mws}
        
        Sua missão:
        1. Analisar os dados fornecidos na planilha (SKUs, quantidades, endereços, lotes, ordens de picking/recebimento).
        2. Orientar o operador/analista passo a passo de como executar essa demanda no Manthan MWS.
        3. Indicar menus específicos do MWS, uso de coletores RF (Rádio Frequência) quando aplicável, telas de liberação de ondas ou impressão de etiquetas de palete (LPN).
        4. Citar os dados reais da planilha para o usuário preencher em cada etapa.
        
        Retorne a resposta dividida EXATAMENTE em passos numerados no seguinte formato de marcação:
        ---PASSO---
        [Título do Passo | Tela/Menu do Manthan MWS]
        [Sua instrução explicando o procedimento técnico de forma clara e os dados específicos a utilizar]
        """
        
        if 'passos_guia' not in st.session_state:
            with st.spinner("O Especialista Manthan MWS está analisando sua operação..."):
                prompt = f"Aqui está o resumo da operação logística recebida:\n{resumo_dados}\n\nCrie o roteiro passo a passo para processar esta carga no Manthan MWS."
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.3
                    )
                )
                
                raw_text = response.text
                passos = [p.strip() for p in raw_text.split("---PASSO---") if p.strip()]
                
                if passos:
                    st.session_state.passos_guia = passos
                    st.session_state.passo_atual = 0
                else:
                    st.warning("O modelo não retornou os passos no formato esperado. Tente reenviar o arquivo.")

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo de logística: {e}")

    # --- 4. PAINEL DE NAVEGAÇÃO INTERATIVO ---
    if 'passos_guia' in st.session_state and st.session_state.passos_guia:
        passos = st.session_state.passos_guia
        total_passos = len(passos)
        atual = st.session_state.passo_atual
        
        st.markdown("---")
        
        col_tit, col_btn = st.columns([3, 1])
        with col_tit:
            st.subheader(f"🏗️ Roteiro Operacional - Manthan MWS ({atual + 1} de {total_passos})")
        with col_btn:
            if st.button("🔄 Reiniciar Roteiro"):
                resetar_jornada()
                st.rerun()

        conteudo_passo = passos[atual]
        st.info(f"👷 **Especialista Manthan MWS orienta:**\n\n{conteudo_passo}")
        
        col_voltar, col_espaco, col_proximo = st.columns([1, 4, 1])
        
        with col_voltar:
            if st.button("⬅️ Passo Anterior", disabled=(atual == 0)):
                st.session_state.passo_atual -= 1
                st.rerun()
                
        with col_proximo:
            if st.button("Próximo Passo ➡️", disabled=(atual == total_passos - 1)):
                st.session_state.passo_atual += 1
                st.rerun()