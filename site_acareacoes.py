import streamlit as st
import pandas as pd
import urllib.parse
import re

# 1. Configuração da página (O 'page_icon' é a imagenzinha na aba do navegador)
# Você pode usar um emoji ou o caminho para a sua logo ex: page_icon="logo.png"
st.set_page_config(page_title="Portal de Acareações", layout="centered", page_icon="📦")

# ==============================================================
# SEU NÚMERO DE WHATSAPP (Apenas números, inclua 55 e DDD)
# ==============================================================
NUMERO_BASE = "5531971463005" # <- ALTERE AQUI PARA O SEU NÚMERO

# ==============================================================
# CABEÇALHO COM A LOGO DA EMPRESA
# ==============================================================
# Usamos colunas para centralizar a logo no meio da tela
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    # Insira o nome exato do arquivo da sua logo aqui
    st.image("logo.png", use_container_width=True)

st.title("Portal de Acareações")
st.markdown("Selecione seu nome abaixo para contatar os clientes e enviar as tratativas.")

try:
    # Lê a planilha que o robô acabou de criar
    df = pd.read_excel("dados_acareacoes.xlsx")
    
    # Prepara a lista de motoristas em ordem alfabética
    motoristas = sorted(df['Motorista'].dropna().unique().tolist())
    mot_selecionado = st.selectbox("👤 Selecione seu nome:", ["-- Escolha --"] + motoristas)

    if mot_selecionado != "-- Escolha --":
        # Filtra apenas as acareações do motorista selecionado
        df_mot = df[df['Motorista'] == mot_selecionado]
        
        st.info(f"Você tem {len(df_mot)} acareação(ões) pendente(s) hoje.")
        
        for idx, row in df_mot.iterrows():
            with st.expander(f"📦 Pacote: {row['AWB']} - {row['Nome']}", expanded=False):
                
                # Formata o telefone do cliente (Remove '+', '-', ' ' e garante o 55 no início)
                tel_cliente = re.sub(r'\D', '', str(row['Telefone']))
                if not tel_cliente.startswith('55') and len(tel_cliente) >= 10:
                    tel_cliente = '55' + tel_cliente
                
                # Monta a mensagem idêntica ao arquivo txt antigo
                msg_cliente = (
                    f"Olá, somos uma transportadora da iMile (SHEIN/TIKTOK)\n\n"
                    f"{row['Nome']}, poderia confirmar o recebimento da mercadoria com os dados abaixo:\n"
                    f"Código do pacote: {row['AWB']}\n"
                    f"Endereço: {row['Endereco']}\n\n"
                    f"Produto: {row['Produto']}\n\n"
                    f"Confirma o Recebimento do produto? SIM OU NÃO"
                )
                
                st.markdown("**Mensagem Padrão:**")
                st.code(msg_cliente, language="text") # Mostra a mensagem com botão de copiar fácil
                
                # Links do WhatsApp
                link_cliente = f"https://wa.me/{tel_cliente}?text={urllib.parse.quote(msg_cliente)}"
                
                msg_base = f"Olá Base! Segue o print da acareação do pacote {row['AWB']}."
                link_base = f"https://wa.me/{NUMERO_BASE}?text={urllib.parse.quote(msg_base)}"
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Botões lado a lado
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f'<a href="{link_cliente}" target="_blank" style="display: block; text-align: center; background-color:#25D366; color:white; padding:12px; border-radius:8px; text-decoration:none; font-weight:bold;">1️⃣ Enviar MSG Cliente</a>', unsafe_allow_html=True)
                with col2:
                    st.markdown(f'<a href="{link_base}" target="_blank" style="display: block; text-align: center; background-color:#1E4976; color:white; padding:12px; border-radius:8px; text-decoration:none; font-weight:bold;">2️⃣ Enviar Print p/ Base</a>', unsafe_allow_html=True)

except FileNotFoundError:
    st.warning("⚠️ O arquivo de acareações ainda não foi gerado hoje. Rode o robô primeiro.")
except Exception as e:
    st.error(f"Erro ao carregar os dados: {e}")