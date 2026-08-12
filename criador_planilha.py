import os
import time
import json
import pandas as pd
from google import genai
from google.genai import types

# --- CONFIGURAÇÃO DE PASTAS ---
PASTA_ENTRADA = "entrada_dados"
PASTA_SAIDA = "saida_planilhas"
PASTA_PROCESSADOS = "historico_processados"

for pasta in [PASTA_ENTRADA, PASTA_SAIDA, PASTA_PROCESSADOS]:
    os.makedirs(pasta, exist_ok=True)

# --- CHAVE DE API GEMINI ---
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("❌ ERRO: Variável de ambiente GEMINI_API_KEY não encontrada!")
    print("Defina a chave no terminal: export GEMINI_API_KEY='sua_chave'")
    exit(1)

client = genai.Client(api_key=api_key)

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
Não inclua nenhuma explicação, apenas o código JSON.
"""

def processar_texto_com_gemini(texto_raw):
    """Envia o texto cru do WhatsApp para a IA estruturar nas colunas do ERP."""
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=f"Extraia os dados operacionais deste texto:\n\n{texto_raw}",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.1
        )
    )
    
    # Limpa possíveis marcações de código markdown do retorno
    raw_response = response.text.strip()
    if raw_response.startswith("```json"):
        raw_response = raw_response[7:-3].strip()
    elif raw_response.startswith("```"):
        raw_response = raw_response[3:-3].strip()
        
    return json.loads(raw_response)

def executar_robo():
    print("🤖 Robô ERP/MWS Iniciado!")
    print(f"📂 Vigia ativado na pasta: ./{PASTA_ENTRADA}")
    print("Aguardando novos arquivos para converter...\n")

    while True:
        arquivos = [f for f in os.listdir(PASTA_ENTRADA) if not f.startswith('.')]
        
        for nome_arquivo in arquivos:
            caminho_arquivo = os.path.join(PASTA_ENTRADA, nome_arquivo)
            print(f"⚡ Novo arquivo detectado: {nome_arquivo}")
            
            try:
                # 1. Leitura do arquivo colado na pasta
                with open(caminho_arquivo, "r", encoding="utf-8") as f:
                    conteudo = f.read()

                print("🧠 Convertendo texto informal na linguagem do ERP via Gemini...")
                dados_json = processar_texto_com_gemini(conteudo)

                # 2. Converte JSON para DataFrame do Pandas
                df = pd.DataFrame(dados_json)

                # 3. Gera a planilha Excel pronta para o ERP
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                nome_excel = f"Planilha_ERP_MWS_{timestamp}.xlsx"
                caminho_excel = os.path.join(PASTA_SAIDA, nome_excel)

                df.to_excel(caminho_excel, index=False, engine='openpyxl')
                print(f"✅ PLANILHA GERADA COM SUCESSO: {caminho_excel}")

                # 4. Move o arquivo original para histórico
                caminho_historico = os.path.join(PASTA_PROCESSADOS, f"{timestamp}_{nome_arquivo}")
                os.rename(caminho_arquivo, caminho_historico)
                print(f"📦 Arquivo fonte movido para historico.\n")

            except Exception as e:
                print(f"❌ Erro ao processar arquivo {nome_arquivo}: {e}\n")

        # Aguarda 3 segundos antes de checar a pasta novamente
        time.sleep(3)

if __name__ == "__main__":
    executar_robo()