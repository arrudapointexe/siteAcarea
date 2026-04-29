simport streamlit as st
import pandas as pd
import urllib.parse
import re
import gspread
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import base64
import requests
from datetime import datetime, timedelta

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
# FUNÇÃO PARA FORMATAÇÃO DE PRAZO
# ==============================================================

def formatar_prazo(prazo_planilha):
    """
    Regra revisada: 
    1. Subtrai 2 horas do prazo original.
    2. Se o horário resultante for entre 16:00 e 05:59, força para 14:00.
    3. Retorna Data e Hora (ex: 29/04/2026 14:00).
    """
    prazo_texto = str(prazo_planilha).strip()
    
    # Se vier vazio ou inválido
    if not prazo_texto or prazo_texto.lower() in ['nan', 'none', 'n/a']:
        amanha = datetime.now() + timedelta(days=1)
        return amanha.strftime("%d/%m/%Y") + " 14:00"
        
    try:
        # 1. Converte o formato da iMile (2026-04-29 19:08:23) para objeto datetime
        # Tentamos o formato completo, se falhar tentamos só data e hora curta
        try:
            prazo_dt = datetime.strptime(prazo_texto, "%Y-%m-%d %H:%M:%S")
        except:
            prazo_dt = datetime.strptime(prazo_texto[:16], "%Y-%m-%d %H:%M")

        # 2. Subtrai 2 horas
        prazo_ajustado = prazo_dt - timedelta(hours=2)
        
        # 3. Verifica a regra do bloqueio (>= 16h ou < 06h)
        hora = prazo_ajustado.hour
        if hora >= 16 or hora < 6:
            # Se caiu no bloqueio, mantém a data mas fixa a hora em 14:00
            prazo_final_str = prazo_ajustado.strftime("%d/%m/%Y") + " 14:00"
        else:
            # Se está no horário permitido, usa o horário calculado
            prazo_final_str = prazo_ajustado.strftime("%d/%m/%Y %H:%M")
            
        return prazo_final_str
        
    except Exception as e:
        # Em caso de erro de conversão, retorna a data de hoje com 14:00
        return datetime.now().strftime("%d/%m/%Y") + " 14:00"
    """
    Regra: Subtrai 2 horas do prazo do sistema.
    Se o horário ajustado cair de madrugada (0h às 5h) ou a partir das 16h (16h às 23h),
    o prazo final é forçado para 14:00.
    """
    prazo_texto = str(prazo_planilha).strip()
    
    # Se vier vazio da iMile
    if not prazo_texto or prazo_texto.lower() in ['nan', 'none', 'n/a']:
        return "14:00"
        
    try:
        # Isola apenas a hora (ex: de "2026-04-29 19:08:23" extrai "19:08")
        if " " in prazo_texto:
            hora_str = prazo_texto.split(" ")[1][:5]
        else:
            hora_str = prazo_texto[:5]
            
        # Converte para tempo e diminui 2 horas
        prazo_dt = datetime.strptime(hora_str, "%H:%M")
        prazo_ajustado = prazo_dt - timedelta(hours=2)
        
        # Avalia a hora final ajustada
        hora = prazo_ajustado.hour
        if hora >= 16 or hora < 6:
            return "14:00"
            
        return prazo_ajustado.strftime("%H:%M")
        
    except Exception:
        # Se a iMile mudar o formato do nada, joga para 14h por segurança
        return "14:00"

# ==============================================================
# FUNÇÃO PARA UPLOAD DE FOTO
# ==============================================================
# Cole aqui a URL que você copiou no Passo 1 (App da Web)
URL_WEBHOOK_DRIVE = "https://script.google.com/macros/s/AKfycbw5jfWjFhxEatj1JhrZlPbs_0H5grj7F7zBZJjdLAZ9K7gyM2R1M_IY1OhkxccuS0FF/exec"

def upload_para_drive(arquivo_foto, nome_arquivo):
    try:
        # Pega a foto do site e codifica para enviar pela passagem secreta
        bytes_imagem = arquivo_foto.getvalue()
        base64_img = base64.b64encode(bytes_imagem).decode('utf-8')

        payload = {
            "filename": nome_arquivo,
            "mimetype": arquivo_foto.type,
            "base64": base64_img
        }

        # Dispara a foto para o seu Google Drive
        resposta = requests.post(URL_WEBHOOK_DRIVE, json=payload)
        resultado = resposta.json()

        if resultado.get("status") == "success":
            return resultado.get("id")
        else:
            st.error(f"Erro no Drive: {resultado.get('message')}")
            return None

    except Exception as e:
        st.error(f"Erro de conexão com o Drive: {e}")
        return None

# ==============================================================
# LEITURA DA PLANILHA
# ==============================================================
def carregar_dados_nuvem():
    try:
        creds = obter_credenciais()
        cliente = gspread.authorize(creds)
        planilha = cliente.open('acareaBaseJML').sheet1
        dados = planilha.get_all_values()
        
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
                
                # Exibição do Prazo de Fechamento
                prazo_texto = formatar_prazo(row)
                st.info(f"⏰ PRAZO DE FECHAMENTO: {prazo_texto}")
                
                # Exibição do Valor
                st.info(f"💰 VALOR DO PACOTE: R\\$ {row.get('Valor', '0.00')} + R\\$100,00 MULTA")                
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
