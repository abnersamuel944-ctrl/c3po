     
import streamlit as st
import pandas as pd
from google import genai
from google.genai import types
import os

st.set_page_config(page_title="ERP Interativo - Estilo Dora", layout="wide")

# 1. Gerenciamento Seguro da Chave de API
api_key = os.environ.get("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("🔑 Chave da API do Gemini não encontrada! Configure a variável GEMINI_API_KEY.")
    st.stop()

client = genai.Client(api_key=api_key)

# 2. Reset de Estado caso o usuário mude o ERP
def resetar_jornada():
    if 'passos_guia' in st.session_state:
        del st.session_state.passos_guia
        del st.session_state.passo_atual

st.title("🎓 Assistente Interativo de ERP")

col_left, col_right = st.columns([1, 2])

with col_left:
    erp_selecionado = st.selectbox(
        "Qual ERP você deseja utilizar hoje?",
        ["SAP S/4HANA", "TOTVS Protheus", "Oracle ERP Cloud", "Microsoft Dynamics"],
        on_change=resetar_jornada
    )
    
    arquivo_uploaded = st.file_uploader("Envie a planilha de dados (Excel ou CSV):", type=["xlsx", "csv"])

DICIONARIO_ERP = {
    "material": ["Material", "Item", "Codigo_Produto", "SKU", "Cod_Mat"],
    "quantidade": ["Qtd", "Quantidade", "Necessidade", "Estoque_Req", "Volume"],
    "data": ["Data_Entrega", "Data", "Prazo", "Plann_Date"],
    "ordem": ["Ordem_Producao", "OP", "Production_Order", "Pedido"]
}

def padronizar_planilha(df):
    renomear = {}
    for col in df.columns:
        for chave, sinonimos in DICIONARIO_ERP.items():
            if str(col).strip() in sinonimos:
                renomear[col] = chave
    return df.rename(columns=renomear)

# 3. Processamento com Tratamento de Erros
if arquivo_uploaded is not None:
    try:
        if arquivo_uploaded.name.endswith('.csv'):
            df = pd.read_csv(arquivo_uploaded)
        else:
            df = pd.read_excel(arquivo_uploaded)
        
        df_padronizado = padronizar_planilha(df)
        st.success("Planilha carregada e processada com sucesso!")
        
        # Resumo estatístico para ajudar o Gemini sem estourar tokens
        resumo_dados = f"Total de linhas: {len(df_padronizado)}\n"
        resumo_dados += f"Colunas encontradas: {list(df_padronizado.columns)}\n"
        resumo_dados += f"Amostra dos dados:\n{df_padronizado.head(5).to_string()}"

        system_instruction = f"""
        Você é o próprio sistema ERP {erp_selecionado}. Sua personalidade é super didática, amigável e interativa, 
        exatamente no estilo da 'Dora a Aventureira'. Você fala em 1ª pessoa ('Eu vejo...', 'Vem em mim na transação X').
        
        Sua missão:
        1. Analisar os dados fornecidos da planilha.
        2. Guiar o usuário passo a passo no processo de resolução.
        3. Indicar exatamente qual tela ou transação ele deve abrir no {erp_selecionado}.
        4. Citar dados específicos da planilha para ele preencher em cada passo.
        
        Retorne a resposta dividida EXATAMENTE em passos numerados no seguinte formato de marcação:
        ---PASSO---
        [Título do Passo | Transação]
        [Fala da Dora/ERP explicando o que fazer e quais dados usar]
        """
        
        if 'passos_guia' not in st.session_state:
            with st.spinner("O ERP está analisando seus dados..."):
                prompt = f"Aqui está o resumo do arquivo recebido:\n{resumo_dados}\n\nCrie a jornada passo a passo para eu processar estes dados."
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.3 # Menor temperatura garante respostas mais precisas/técnicas
                    )
                )
                
                raw_text = response.text
                passos = [p.strip() for p in raw_text.split("---PASSO---") if p.strip()]
                
                if passos:
                    st.session_state.passos_guia = passos
                    st.session_state.passo_atual = 0
                else:
                    st.warning("O modelo não retornou os passos no formato esperado. Tente reenviar.")

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo: {e}")

    # 4. Exibição
    if 'passos_guia' in st.session_state and st.session_state.passos_guia:
        passos = st.session_state.passos_guia
        total_passos = len(passos)
        atual = st.session_state.passo_atual
        
        st.markdown("---")
        
        col_tit, col_btn = st.columns([3, 1])
        with col_tit:
            st.subheader(f"📍 Jornada de Processamento ({atual + 1} de {total_passos})")
        with col_btn:
            if st.button("🔄 Recomeçar Análise"):
                resetar_jornada()
                st.rerun()

        conteudo_passo = passos[atual]
        st.info(f"🤖 **{erp_selecionado} diz:**\n\n{conteudo_passo}")
        
        col_voltar, col_espaco, col_proximo = st.columns([1, 4, 1])
        
        with col_voltar:
            if st.button("⬅️ Voltar", disabled=(atual == 0)):
                st.session_state.passo_atual -= 1
                st.rerun()
                
        with col_proximo:
            if st.button("Próximo ➡️", disabled=(atual == total_passos - 1)):
                st.session_state.passo_atual += 1
                st.rerun()
