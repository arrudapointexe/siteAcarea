import streamlit as st
import pandas as pd
import urllib.parse
import re
import gspread
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

# Configuração da página
st.set_page_config(page_title="Portal de Acareações", layout="centered", page_icon="📦")

# ==============================================================
# CONFIGURAÇÕES BÁSICAS
# ==============================================================
NUMERO_BASE = "5531971463005"
ID_PASTA_DRIVE = "1yL7KPreMQ9HQpKRJsDptsIxoUB29czGW" # Sua pasta do Drive

# Carregamento da Logotipo
try:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("logo.png", use_container_width=True)
except:
    pass 

st.title("📦 Portal de Acareações")

# ==============================================================
# FUNÇÃO PARA CONECTAR AOS SERVIÇOS GOOGLE
# ==============================================================
def obter_credenciais():
    # Tenta ler local, se não, lê do Secrets (Online)
    try:
        with open('credenciais.json') as f:
            info = json.load(f)
    except FileNotFoundError:
        info = json.loads(st.secrets["chave_google"].strip())
    
    escopo = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    return Credentials.from_service_account_info(info, scopes=escopo)

# ==============================================================
# FUNÇÃO PARA UPLOAD DE FOTO
# ==============================================================
def upload_para_drive(arquivo_foto, nome_arquivo):
    try:
        creds = obter_credenciais()
        servico = build('drive', 'v3', credentials=creds)
        
        metadados = {
            'name': nome_arquivo,
            'parents': [ID_PASTA_DRIVE]
        }
        
        # Converte a foto do Streamlit para um formato que o Google aceita
        media = MediaIoBaseUpload(io.BytesIO(arquivo_foto.getvalue()), 
                                  mimetype=arquivo_foto.type)
        
        arquivo = servico.files().create(body=metadados, media_body=media, fields='id').execute()
        return arquivo.get('id')
    except Exception as e:
        st.error(f"Erro no upload: {e}")
        return None

# ==============================================================
# LEITURA DA PLANILHA
# ==============================================================
def carregar_dados_nuvem():
    try:
        creds = obter_credenciais()
        cliente = gspread.authorize(creds)
        planilha = cliente.open('acareaBase').sheet1
        dados = planilha.get('A1:G5000')
        
        if not dados or len(dados) < 2:
            return pd.DataFrame()

        df = pd.DataFrame(dados[1:], columns=dados[0])
        df.columns = df.columns.astype(str).str.strip()
        if 'Motorista' in df.columns:
            df['Motorista'] = df['Motorista'].astype(str).str.strip()
        return df
    except Exception as e:
        st.error(f"Erro ao ler planilha: {e}")
        return pd.DataFrame()

# ==============================================================
# INTERFACE DO SITE
# ==============================================================
df_imile = carregar_dados_nuvem()

if not df_imile.empty:
    motoristas = sorted(df_imile['Motorista'].dropna().unique().tolist())
    if '(vazio)' in motoristas: motoristas.remove('(vazio)')

    mot_selecionado = st.selectbox("👤 Selecione o seu nome:", ["-- Escolha --"] + motoristas)

    if mot_selecionado != "-- Escolha --":
        df_mot = df_imile[df_imile['Motorista'] == mot_selecionado]
        st.success(f"Você tem **{len(df_mot)} acareação(ões)** pendente(s).")
        
        for idx, row in df_mot.iterrows():
            with st.expander(f"🔵 iMile | Pacote: {row['AWB']} - {row['Nome']}", expanded=False):
                
                # Exibição do Valor
                st.info(f"💰 VALOR DO PACOTE: R$ {row.get('Valor', '0.00')}")
                
                # --- ÁREA DE UPLOAD ---
                st.markdown("### 📷 Enviar Comprovante")
                foto = st.file_uploader(f"Anexe o print/foto (AWB {row['AWB']})", type=['png', 'jpg', 'jpeg'], key=f"file_{row['AWB']}")
                
                if foto:
                    if st.button(f"Confirmar Envio da Foto {row['AWB']}", key=f"btn_{row['AWB']}"):
                        with st.spinner("Enviando para a base..."):
                            nome_img = f"{row['AWB']}_{row['Nome']}.jpg".replace(" ", "_")
                            file_id = upload_para_drive(foto, nome_img)
                            if file_id:
                                st.success("✅ Foto salva com sucesso no Google Drive!")
                                st.balloons()

                # --- BOTÕES DE WHATSAPP ---
                st.markdown("---")
                
                # Limpeza de Telefone
                tel_bruto = str(row.get('Telefone', ''))
                tel_cliente = re.sub(r'\D', '', tel_bruto).lstrip('0')
                if len(tel_cliente) >= 10: tel_cliente = '55' + tel_cliente
                else: tel_cliente = ''

                # MENSAGEM PADRÃO COMPLETA (Endereço e Produto)
                msg_cliente = (
                    f"Olá, somos uma transportadora parceira (SHEIN/TIKTOK)\n\n"
                    f"{row['Nome']}, poderia confirmar o recebimento da mercadoria com os dados abaixo:\n"
                    f"Código do pacote: {row['AWB']}\n"
                    f"Endereço: {row.get('Endereco', 'N/A')}\n\n"
                    f"Produto: {row.get('Produto', 'N/A')}\n\n"
                    f"Confirma o Recebimento do produto? SIM OU NÃO"
                )
                st.markdown("**Mensagem Padrão:**")
                st.code(msg_cliente, language="text") 
                
                col1, col2 = st.columns(2)
                with col1:
                    if tel_cliente:
                        st.link_button("1️⃣ Chamar Cliente", f"https://wa.me/{tel_cliente}?text={urllib.parse.quote(msg_cliente)}")
                    else:
                        st.error("Telefone indisponível")
                with col2:
                    msg_base = f"Base, segue comprovante do pacote {row['AWB']}."
                    st.link_button("2️⃣ Avisar Base", f"https://wa.me/{NUMERO_BASE}?text={urllib.parse.quote(msg_base)}")

else:
    st.warning("⚠️ Nenhuma acareação pendente.")
