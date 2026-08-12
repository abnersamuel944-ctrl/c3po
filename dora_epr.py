import os
import json
import pandas as pd
import streamlit as st
from google import genai
from google.genai import types

# --- CONFIGURAÇÃO DA PÁGINA STREAMLIT ---
st.set_page_config(
    page_title="Automação ERP/WMS com Clippy",
    page_icon="📎",
    layout="wide"
)

# --- PROMPT DO SISTEMA GEMINI ---
SYSTEM_PROMPT = """
Você é um motor de extração de dados para sistemas ERP e WMS (Manthan MWS, SAP, Protheus).
Sua tarefa é ler mensagens de texto informais (como conversas de WhatsApp, e-mails ou anotações) e extrair os dados em formato de tabela JSON limpa.

Mapeamento obrigatório de colunas para o ERP:
- SKU (ou Codigo_Produto)
- Item (Descrição do produto)
- Quantidade (Apenas o número)
- Endereco (Posição/Rua no armazém)
- Lote (Número de lote/batch)
- Ordem (Número da OP, Pedido ou Carga)
- Data (Data limite/prazo)

Retorne EXATAMENTE um JSON puro no formato de lista de objetos.
Exemplo de retorno:
[
  {"SKU": "ML-04", "Item": "Molas de Aço", "Quantidade": 500, "Endereco": "RUA-A-01-2", "Lote": "L2026-A", "Ordem": "99402", "Data": "15/08/2026"}
]
Não inclua nenhuma explicação ou formatação markdown adicional, apenas o código JSON.
"""

# --- INICIALIZAÇÃO DA SESSÃO ---
if "api_key" not in st.session_state:
    st.session_state.api_key = os.environ.get("GEMINI_API_KEY", "")

if "mensagens_clippy" not in st.session_state:
    st.session_state.mensagens_clippy = "Olá! Eu sou o Clippy! 📎\nEstou aqui para ajudar a transformar suas mensagens brutas em dados prontos para ERP/WMS."

# --- FUNÇÃO DE PROCESSAMENTO COM GEMINI ---
def processar_texto_com_gemini(texto_raw, api_key):
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=f"Extraia os dados operacionais deste texto:\n\n{texto_raw}",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.1,
            response_mime_type="application/json"
        )
    )
    
    raw_response = response.text.strip()
    if raw_response.startswith("```json"):
        raw_response = raw_response[7:-3].strip()
    elif raw_response.startswith("```"):
        raw_response = raw_response[3:-3].strip()
        
    return json.loads(raw_response)

# --- CSS PERSONALIZADO (BALÃO DE FALA E PERSONAGEM CLIPPY) ---
st.markdown("""
    <style>
    .clippy-container {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 9999;
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        max-width: 320px;
    }
    .clippy-speech {
        background-color: #FFFFCC;
        border: 2px solid #000;
        border-radius: 10px;
        padding: 12px;
        font-family: 'Comic Sans MS', 'Arial', sans-serif;
        font-size: 13px;
        color: #000;
        box-shadow: 3px 3px 10px rgba(0,0,0,0.2);
        margin-bottom: 8px;
        position: relative;
    }
    .clippy-speech::after {
        content: '';
        position: absolute;
        bottom: -10px;
        right: 35px;
        border-width: 10px 10px 0;
        border-style: solid;
        border-color: #FFFFCC transparent;
        display: block;
        width: 0;
    }
    .clippy-avatar {
        font-size: 65px;
        cursor: pointer;
        filter: drop-shadow(2px 2px 4px rgba(0,0,0,0.3));
        transition: transform 0.2s;
    }
    .clippy-avatar:hover {
        transform: scale(1.1) rotate(-5deg);
    }
    </style>
""", unsafe_allow_html=True)

# --- COMPONENTE DO CLIPPY FIXO NA TELA ---
st.markdown(f"""
    <div class="clippy-container">
        <div class="clippy-speech">
            {st.session_state.mensagens_clippy}
        </div>
        <div class="clippy-avatar">📎</div>
    </div>
""", unsafe_allow_html=True)

# --- INTERFACE PRINCIPAL ---
st.title("🤖 Automação Operacional ERP / WMS")
st.subheader("Extração Inteligente de Mensagens para Planilhas")

# --- BARRA LATERAL (CONFIGURAÇÃO DA CHAVE DE API) ---
with st.sidebar:
    st.header("⚙️ Configurações")
    chave_input = st.text_input("Sua GEMINI_API_KEY:", value=st.session_state.api_key, type="password")
    if chave_input:
        st.session_state.api_key = chave_input
        st.success("Chave salva!")
    else:
        st.warning("Insira sua chave de API para continuar.")

# --- CORPO DA APLICAÇÃO ---
if not st.session_state.api_key:
    st.info("👈 Por favor, adicione sua chave de API do Gemini na barra lateral para ativar o sistema.")
    st.session_state.mensagens_clippy = "Ei! Preciso da sua chave de API na barra lateral para começar a trabalhar!"
else:
    aba_texto, aba_arquivo = st.tabs(["💬 Digitar / Colar Mensagem", "📁 Enviar Arquivo de Texto"])

    # ABA 1: TEXTO DIRETO
    with aba_texto:
        texto_input = st.text_area("Cole a mensagem informal aqui (ex: WhatsApp, e-mail):", height=200, 
                                   placeholder="Exemplo: Preciso enviar 500 unidades da Mola de Aço (SKU: ML-04) da RUA-A-01-2. Lote L2026-A, OP 99402 para o dia 15/08/2026.")
        
        if st.button("🚀 Processar Mensagem", type="primary"):
            if texto_input.strip():
                try:
                    with st.spinner("Clippy e Gemini estão processando..."):
                        dados = processar_texto_com_gemini(texto_input, st.session_state.api_key)
                        df = pd.DataFrame(dados)
                        
                        st.session_state.mensagens_clippy = "Prontinho! Consegui extrair os dados e organizei a tabela para você! 🎉"
                        st.experimental_rerun()
                except Exception as e:
                    st.error(f"Erro ao processar: {e}")
                    st.session_state.mensagens_clippy = "Ops... Ocorreu um erro ao processar esses dados. Verifique a chave ou o texto enviado."
            else:
                st.warning("Por favor, insira algum texto.")

    # ABA 2: UPLOAD DE ARQUIVOS
    with aba_arquivo:
        arquivo_enviado = st.file_uploader("Envie um arquivo .txt com os dados:", type=["txt"])
        
        if arquivo_enviado is not None:
            conteudo_txt = arquivo_enviado.read().decode("utf-8")
            st.text_area("Conteúdo do arquivo:", conteudo_txt, height=150, disabled=True)
            
            if st.button("🚀 Processar Arquivo"):
                try:
                    with st.spinner("Analisando o arquivo..."):
                        dados = processar_texto_com_gemini(conteudo_txt, st.session_state.api_key)
                        df = pd.DataFrame(dados)
                        
                        st.session_state.mensagens_clippy = "Arquivo lido com sucesso! Aqui estão os dados convertidos em tabela."
                        st.experimental_rerun()
                except Exception as e:
                    st.error(f"Erro ao processar o arquivo: {e}")

    # RESULTADOS E EXPORTAÇÃO
    if 'df' in locals():
        st.markdown("---")
        st.header("📊 Dados Extraídos para ERP/WMS")
        st.dataframe(df, use_container_width=True)

        # Download do Excel
        nome_arquivo_excel = "Planilha_ERP_MWS.xlsx"
        df.to_excel(nome_arquivo_excel, index=False, engine='openpyxl')
        
        with open(nome_arquivo_excel, "rb") as file:
            st.download_button(
                label="📥 Baixar Planilha Excel (.xlsx)",
                data=file,
                file_name=nome_arquivo_excel,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
