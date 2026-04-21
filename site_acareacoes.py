import streamlit as st
import pandas as pd
import urllib.parse
import re
import os

# Configuração da página do site
st.set_page_config(page_title="Portal de Acareações", layout="centered", page_icon="📦")

# ==============================================================
# FUNÇÃO PARA LIMPAR E PADRONIZAR NOMES
# ==============================================================
def padronizar_motorista(nome_bruto):
    """Limpa siglas da iMile e pega apenas o Primeiro Nome e o Primeiro Sobrenome."""
    if pd.isna(nome_bruto) or str(nome_bruto).strip() == '' or str(nome_bruto).strip() == '(vazio)':
        return '(vazio)'
        
    nome = str(nome_bruto).upper() # Deixa tudo maiúsculo para evitar erros
    
    # 1. Remove qualquer coisa entre parênteses (Ex: "(STB LOC)", "(JML INT)")
    nome = re.sub(r'\(.*?\)', '', nome)
    
    # 2. Remove o traço e tudo que vem depois (Ex: "- PRATA", "- DIONISIO")
    nome = nome.split('-')[0]
    
    # 3. Limpa espaços extras no começo e no fim
    nome = nome.strip()
    
    # 4. Pega apenas o PRIMEIRO nome e o PRIMEIRO sobrenome (posição 0 e posição 1)
    partes = nome.split()
    if len(partes) > 1:
        return f"{partes[0]} {partes[1]}"
    elif len(partes) == 1:
        return partes[0]
        
    return '(vazio)'


# ==============================================================
# SEU NÚMERO DE WHATSAPP
# ==============================================================
NUMERO_BASE = "5531999999999" # <- ALTERE AQUI PARA O SEU NÚMERO

try:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("logo.png", use_container_width=True)
except:
    pass 

st.title("📦 Portal de Acareações")
st.markdown("Selecione seu nome abaixo para contatar os clientes e enviar as tratativas para a base.")

# ==============================================================
# CARREGAMENTO DOS DADOS (IMILE + SHOPEE)
# ==============================================================
df_imile = pd.DataFrame()
df_shopee = pd.DataFrame()

if os.path.exists("dados_acareacoes.xlsx"):
    try:
        df_imile = pd.read_excel("dados_acareacoes.xlsx")
        df_imile['Plataforma'] = 'iMile'
    except: pass

if os.path.exists("dados_acareacoes_shopee.xlsx"):
    try:
        df_shopee = pd.read_excel("dados_acareacoes_shopee.xlsx")
        df_shopee['Plataforma'] = 'Shopee'
    except: pass

# Une as duas planilhas
if not df_imile.empty or not df_shopee.empty:
    df_completo = pd.concat([df_imile, df_shopee], ignore_index=True)
    
    # ==============================================================
    # A MÁGICA ACONTECE AQUI: Aplica a padronização em todos os nomes
    # ==============================================================
    df_completo['Motorista'] = df_completo['Motorista'].apply(padronizar_motorista)
    
    # Prepara a lista de motoristas
    motoristas = sorted(df_completo['Motorista'].dropna().unique().tolist())
    
    # Remove o (vazio) das opções
    if '(vazio)' in motoristas: motoristas.remove('(vazio)')

    mot_selecionado = st.selectbox("👤 Selecione seu nome:", ["-- Escolha --"] + motoristas)

# ... (O restante do código, os botões e os links do WhatsApp continuam EXATAMENTE IGUAIS a partir daqui) ...

    if mot_selecionado != "-- Escolha --":
        df_mot = df_completo[df_completo['Motorista'] == mot_selecionado]
        
        # Conta pacotes por plataforma
        qtd_imile = len(df_mot[df_mot['Plataforma'] == 'iMile'])
        qtd_shopee = len(df_mot[df_mot['Plataforma'] == 'Shopee'])
        
        st.info(f"Você tem **{len(df_mot)} acareação(ões)** pendente(s) hoje. (iMile: {qtd_imile} | Shopee: {qtd_shopee})")
        
        for idx, row in df_mot.iterrows():
            plataforma = row.get('Plataforma', 'iMile')
            icone = "🟠" if plataforma == 'Shopee' else "🔵"
            
            with st.expander(f"{icone} {plataforma} | Pacote: {row['AWB']} - {row['Nome']}", expanded=False):
                
                # --- LÓGICA PARA IMILE ---
                if plataforma == 'iMile':
                    tel_cliente = re.sub(r'\D', '', str(row.get('Telefone', '')))
                    if not tel_cliente.startswith('55') and len(tel_cliente) >= 10:
                        tel_cliente = '55' + tel_cliente
                        
                    msg_cliente = (
                        f"Olá, somos uma transportadora parceira (SHEIN/TIKTOK)\n\n"
                        f"{row['Nome']}, poderia confirmar o recebimento da mercadoria com os dados abaixo:\n"
                        f"Código do pacote: {row['AWB']}\n"
                        f"Endereço: {row.get('Endereco', 'N/A')}\n\n"
                        f"Produto: {row.get('Produto', 'N/A')}\n\n"
                        f"Confirma o Recebimento do produto? SIM OU NÃO"
                    )
                    st.markdown("**Mensagem Padrão (iMile):**")
                    st.code(msg_cliente, language="text") 
                    
                    if len(tel_cliente) >= 10:
                        link_cliente = f"https://wa.me/{tel_cliente}?text={urllib.parse.quote(msg_cliente)}"
                        btn_cliente_html = f'<a href="{link_cliente}" target="_blank" style="display: block; text-align: center; background-color:#25D366; color:white; padding:12px; border-radius:8px; text-decoration:none; font-weight:bold;">1️⃣ Enviar MSG Cliente (iMile)</a>'
                    else:
                        btn_cliente_html = f'<div style="text-align: center; background-color:#f8d7da; color:#721c24; padding:12px; border-radius:8px; border: 1px solid #f5c6cb;">Telefone Indisponível</div>'

                # --- LÓGICA PARA SHOPEE ---
                else:
                    # Shopee não fornece telefone na extração PNR facilmente.
                    # O motorista terá que copiar a mensagem e mandar pro número se ele tiver,
                    # ou apenas copiar para fins de registro.
                    msg_cliente = (
                        f"Olá, somos a transportadora parceira da SHOPEE.\n\n"
                        f"Sr(a). {row['Nome']}, consta em nosso sistema uma contestação de entrega para o pacote:\n"
                        f"Código: {row['AWB']}\n\n"
                        f"Você confirma que RECEBEU ou NÃO RECEBEU este pacote?"
                    )
                    st.markdown("**Mensagem Padrão (Shopee):**")
                    st.code(msg_cliente, language="text")
                    
                    # Como não temos o telefone direto da Shopee na planilha, o botão redireciona para o WhatsApp limpo, 
                    # ou podemos omitir o botão 1 se for inútil sem o número.
                    link_cliente = f"https://wa.me/?text={urllib.parse.quote(msg_cliente)}"
                    btn_cliente_html = f'<a href="{link_cliente}" target="_blank" style="display: block; text-align: center; background-color:#25D366; color:white; padding:12px; border-radius:8px; text-decoration:none; font-weight:bold;">1️⃣ Copiar e Abrir Wpp (Escolher Contato)</a>'


                # --- BOTÃO PARA A BASE (Comum aos dois) ---
                msg_base = f"Olá Base! Segue o print da acareação do pacote {row['AWB']} ({plataforma})."
                link_base = f"https://wa.me/{NUMERO_BASE}?text={urllib.parse.quote(msg_base)}"
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(btn_cliente_html, unsafe_allow_html=True)
                with col2:
                    st.markdown(f'<a href="{link_base}" target="_blank" style="display: block; text-align: center; background-color:#1E4976; color:white; padding:12px; border-radius:8px; text-decoration:none; font-weight:bold;">2️⃣ Enviar Print p/ Base</a>', unsafe_allow_html=True)

else:
    st.warning("⚠️ Nenhum arquivo de acareação (iMile ou Shopee) foi encontrado hoje. Rode os robôs extratores primeiro.")
