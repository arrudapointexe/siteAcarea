import os
import streamlit as st
import pandas as pd
import urllib.parse
import re
import gspread
import json
from google.oauth2.service_account import Credentials
import base64
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Portal de Acareações", layout="centered", page_icon="📦")

# ==============================================================
# VARIÁVEIS DE AMBIENTE (SECRETS)
# ==============================================================
# No Streamlit Cloud, adicione essas variáveis em Settings > Secrets
try:
    NUMERO_BASE = st.secrets.get("NUMERO_BASE", "5531971463005")
    NOME_PLANILHA = st.secrets.get("NOME_PLANILHA", "acareaBase")
    URL_WEBHOOK_DRIVE = st.secrets.get("URL_WEBHOOK_DRIVE", "")
except:
    NUMERO_BASE = os.getenv("NUMERO_BASE", "5531971463005")
    NOME_PLANILHA = os.getenv("NOME_PLANILHA", "acareaBase")
    URL_WEBHOOK_DRIVE = os.getenv("URL_WEBHOOK_DRIVE", "")

try:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("logo.png", use_container_width=True)
except: pass 

st.title("📦 Portal de Acareações")

def obter_credenciais():
    try:
        with open('credenciais.json') as f:
            info = json.load(f)
    except FileNotFoundError:
        info = json.loads(st.secrets["chave_google"].strip())
    
    escopo = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    return Credentials.from_service_account_info(info, scopes=escopo)

def formatar_prazo(prazo_planilha):
    prazo_texto = str(prazo_planilha).strip()
    if not prazo_texto or prazo_texto.lower() in ['nan', 'none', 'n/a']:
        amanha = datetime.now() + timedelta(days=1)
        return amanha.strftime("%d/%m/%Y") + " 14:00"
        
    try:
        try: prazo_dt = datetime.strptime(prazo_texto, "%Y-%m-%d %H:%M:%S")
        except: prazo_dt = datetime.strptime(prazo_texto[:16], "%Y-%m-%d %H:%M")

        prazo_ajustado = prazo_dt - timedelta(hours=2)
        hora = prazo_ajustado.hour
        
        if hora >= 16 or hora < 6:
            return prazo_ajustado.strftime("%d/%m/%Y") + " 14:00"
        else:
            return prazo_ajustado.strftime("%d/%m/%Y %H:%M")
    except:
        return datetime.now().strftime("%d/%m/%Y") + " 14:00"

def upload_para_drive(arquivo_foto, nome_arquivo):
    if not URL_WEBHOOK_DRIVE:
        st.error("URL do Webhook do Google Apps Script não configurada.")
        return None
    try:
        bytes_imagem = arquivo_foto.getvalue()
        base64_img = base64.b64encode(bytes_imagem).decode('utf-8')
        
        payload = {
            "filename": nome_arquivo,
            "mimetype": arquivo_foto.type,
            "base64": base64_img
        }
        
        resposta = requests.post(URL_WEBHOOK_DRIVE, json=payload)
        resultado = resposta.json()
        
        if resultado.get("status") == "success":
            return resultado.get("id")
        else:
            st.error(f"Erro no Drive: {resultado.get('message')}")
            return None
    except Exception as e:
        st.error(f"Erro de conexão com o Drive Webhook: {e}")
        return None

def carregar_dados_base(nome_aba):
    try:
        creds = obter_credenciais()
        cliente = gspread.authorize(creds)
        
        # O JEITO CERTO: usa .worksheet() com o nome que veio da seleção
        planilha = cliente.open('acareaBase').worksheet(nome_aba)
        
        dados = planilha.get_all_values()
        if not dados or len(dados) < 2: 
            return pd.DataFrame()

        df = pd.DataFrame(dados[1:], columns=dados[0])
        return df
    except Exception as e:
        st.error(f"Erro ao ler aba {nome_aba}: {e}")
        return pd.DataFrame() planilha: {e}")
        return pd.DataFrame()

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
                prazo_texto = formatar_prazo(row.get('Prazo do Processo', ''))
                st.info(f"⏰ PRAZO DE FECHAMENTO: {prazo_texto}")
                st.info(f"💰 VALOR DO PACOTE: R\\$ {row.get('Valor', '0.00')} + R\\$ 100,00 MULTA")

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

                st.markdown("---")
                tel_bruto = str(row.get('Telefone', ''))
                tel_cliente = re.sub(r'\D', '', tel_bruto).lstrip('0')
                if len(tel_cliente) >= 10: tel_cliente = '55' + tel_cliente
                else: tel_cliente = ''

                msg_cliente = (
                    f"Olá, somos uma transportadora parceira (SHEIN/TIKTOK)\n\n"
                    f"{row['Nome']}, poderia confirmar o recebimento da mercadoria com os dados abaixo:\n"
                    f"Código do pacote: {row['AWB']}\n"
                    f"Endereço: {row.get('Endereco', 'N/A')}\n\n"
                    f"Produto: {row.get('Produto', 'N/A')}\n\n"
                    f"Confirma o Recebimento do produto? SIM OU NÃO"
                )
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
