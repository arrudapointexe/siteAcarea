import streamlit as st
import pandas as pd
import urllib.parse
import re
import gspread
import json
import requests
import base64
from google.oauth2.service_account import Credentials

# Configuração da página
st.set_page_config(page_title="Portal de Acareações", layout="centered", page_icon="📦")

# ==============================================================
# CONFIGURAÇÕES BÁSICAS
# ==============================================================
NUMERO_BASE = "5531971463005"
IMGBB_API_KEY = "9127eccb78656e481be2eb59ad2657ff" # Sua chave do ImgBB

# Carregamento da Logotipo
try:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("logo.png", use_container_width=True)
except:
    pass 

st.title("📦 Portal de Acareações")

# ==============================================================
# FUNÇÃO PARA LER DADOS DA PLANILHA (GOOGLE)
# ==============================================================
def obter_credenciais():
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
# FUNÇÃO PARA UPLOAD DE FOTO (IMGBB)
# ==============================================================
def upload_para_imgbb(arquivo_foto):
    try:
        url = "https://api.imgbb.com/1/upload"
        # Converte a imagem para o formato que a internet entende (Base64)
        imagem_base64 = base64.b64encode(arquivo_foto.getvalue()).decode('utf-8')
        
        payload = {
            "key": IMGBB_API_KEY,
            "image": imagem_base64
        }
        
        resposta = requests.post(url, data=payload)
        
        if resposta.status_code == 200:
            dados_resposta = resposta.json()
            return dados_resposta['data']['url'] # Retorna o link direto da foto
        else:
            st.error(f"Erro no servidor de imagens: {resposta.text}")
            return None
    except Exception as e:
        st.error(f"Erro ao processar a foto: {e}")
        return None

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
            awb = row['AWB']
            chave_link = f"link_foto_{awb}" # Gaveta de memória para salvar o link da foto
            
            with st.expander(f"🔵 iMile | Pacote: {awb} - {row['Nome']}", expanded=False):
                
                st.info(f"💰 VALOR DO PACOTE: R$ {row.get('Valor', '0.00')}")
                
                # --- ÁREA DE UPLOAD ---
                st.markdown("### 📷 Enviar Comprovante")
                foto = st.file_uploader(f"Anexe o print/foto (AWB {awb})", type=['png', 'jpg', 'jpeg'], key=f"file_{awb}")
                
                # Se o motorista colocar uma foto e apertar o botão
                if foto:
                    if st.button(f"Confirmar Envio da Foto {awb}", key=f"btn_{awb}"):
                        with st.spinner("Gerando link seguro da imagem..."):
                            link_gerado = upload_para_imgbb(foto)
                            if link_gerado:
                                # Guarda o link na memória do site
                                st.session_state[chave_link] = link_gerado
                                st.success("✅ Foto processada com sucesso!")
                                st.markdown(f"**Link gerado:** [Ver Comprovante]({link_gerado})")
                                st.balloons()

                # --- BOTÕES DE WHATSAPP ---
                st.markdown("---")
                
                # Tratamento do telefone
                tel_bruto = str(row.get('Telefone', ''))
                tel_cliente = re.sub(r'\D', '', tel_bruto).lstrip('0')
                if len(tel_cliente) >= 10: tel_cliente = '55' + tel_cliente
                else: tel_cliente = ''

                # MENSAGEM DO CLIENTE
                msg_cliente = (
                    f"Olá, somos uma transportadora parceira (SHEIN/TIKTOK)\n\n"
                    f"{row['Nome']}, poderia confirmar o recebimento da mercadoria com os dados abaixo:\n"
                    f"Código do pacote: {awb}\n"
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
                    # MENSAGEM DA BASE (Agora inclui o link da foto se ela foi enviada!)
                    msg_base = f"Base, segue tratativa do pacote {awb} (iMile) - Valor: R$ {row.get('Valor', '0.00')}."
                    
                    # Se houver um link de foto salvo na memória, adiciona na mensagem do zap
                    if chave_link in st.session_state:
                        msg_base += f"\n\n📷 Print/Comprovante: {st.session_state[chave_link]}"
                    else:
                        msg_base += f"\n\n⚠️ (Nenhum comprovante anexado no site)"

                    st.link_button("2️⃣ Avisar Base", f"https://wa.me/{NUMERO_BASE}?text={urllib.parse.quote(msg_base)}")

else:
    st.warning("⚠️ Nenhuma acareação pendente.")
