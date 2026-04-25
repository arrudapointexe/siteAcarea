import streamlit as st
import pandas as pd
import urllib.parse
import re
import os

# Configuração da página do site
st.set_page_config(page_title="Portal de Acareações", layout="centered", page_icon="📦")

# ==============================================================
# SEU NÚMERO DE WHATSAPP (Já configurado!)
# ==============================================================
NUMERO_BASE = "5531971463005" 

try:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("logo.png", use_container_width=True)
except:
    pass 

st.title("📦 Portal de Acareações")
st.markdown("Selecione seu nome abaixo para contatar os clientes e enviar as tratativas para a base.")

# ==============================================================
# CARREGAMENTO DOS DADOS (APENAS IMILE)
# ==============================================================
df_imile = pd.DataFrame()

if os.path.exists("dados_acareacoes.xlsx"):
    try:
        df_imile = pd.read_excel("dados_acareacoes.xlsx")
    except Exception as e:
        st.error(f"Erro ao carregar a planilha: {e}")

if not df_imile.empty:
    
    # Prepara a lista de motoristas mantendo os nomes originais (com tags)
    motoristas = sorted(df_imile['Motorista'].dropna().unique().tolist())
    
    if '(vazio)' in motoristas: motoristas.remove('(vazio)')

    mot_selecionado = st.selectbox("👤 Selecione seu nome:", ["-- Escolha --"] + motoristas)

    if mot_selecionado != "-- Escolha --":
        df_mot = df_imile[df_imile['Motorista'] == mot_selecionado]
        
        st.info(f"Você tem **{len(df_mot)} acareação(ões)** pendente(s) hoje.")
        
        for idx, row in df_mot.iterrows():
            with st.expander(f"🔵 iMile | Pacote: {row['AWB']} - {row['Nome']}", expanded=False):
                
                # --- EXIBIÇÃO DO VALOR (APENAS PARA O MOTORISTA) ---
                valor_pnr = row.get('Valor', '0.00')
                st.markdown(f"""
                <div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; border-left: 5px solid #1E4976; margin-bottom: 15px;">
                    <span style="color: #1E4976; font-weight: bold;">💰 VALOR DO PACOTE:</span> 
                    <span style="font-size: 18px; font-weight: bold;">R$ {valor_pnr}</span>
                </div>
                """, unsafe_allow_html=True)
                
                # =========================================================
                # LIMPEZA BLINDADA DE TELEFONE
                # =========================================================
                tel_bruto = str(row.get('Telefone', ''))
                
                if tel_bruto.endswith('.0'):
                    tel_bruto = tel_bruto[:-2]
                    
                tel_cliente = re.sub(r'\D', '', tel_bruto)
                
                if tel_cliente.startswith('55') and len(tel_cliente) > 11:
                    tel_cliente = tel_cliente[2:]
                    
                tel_cliente = tel_cliente.lstrip('0')
                
                if len(tel_cliente) >= 10:
                    tel_cliente = '55' + tel_cliente
                else:
                    tel_cliente = '' 
                # =========================================================

                # --- MENSAGEM PADRÃO ---
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
                
                # --- BOTÃO CLIENTE ---
                if tel_cliente:
                    link_cliente = f"https://wa.me/{tel_cliente}?text={urllib.parse.quote(msg_cliente)}"
                    btn_cliente_html = f'<a href="{link_cliente}" target="_blank" style="display: block; text-align: center; background-color:#25D366; color:white; padding:12px; border-radius:8px; text-decoration:none; font-weight:bold;">1️⃣ Enviar MSG Cliente</a>'
                else:
                    btn_cliente_html = f'<div style="text-align: center; background-color:#f8d7da; color:#721c24; padding:12px; border-radius:8px; border: 1px solid #f5c6cb;">Telefone Indisponível</div>'

                # --- BOTÃO PARA A BASE ---
                msg_base = f"Olá Base! Segue o print da acareação do pacote {row['AWB']} (iMile) - Valor: R$ {valor_pnr}."
                link_base = f"https://wa.me/{NUMERO_BASE}?text={urllib.parse.quote(msg_base)}"
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(btn_cliente_html, unsafe_allow_html=True)
                with col2:
                    st.markdown(f'<a href="{link_base}" target="_blank" style="display: block; text-align: center; background-color:#1E4976; color:white; padding:12px; border-radius:8px; text-decoration:none; font-weight:bold;">2️⃣ Enviar Print p/ Base</a>', unsafe_allow_html=True)

else:
    st.warning("⚠️ Nenhum arquivo de acareação da iMile foi encontrado hoje. Rode o robô primeiro.")
