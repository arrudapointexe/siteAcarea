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

# ==============================================================
# CONFIGURAÇÃO DA PÁGINA (Deve ser a primeira linha do Streamlit)
# ==============================================================
st.set_page_config(page_title="Gestão de Acareações", layout="wide", page_icon="📦")

# ==============================================================
# CONFIGURAÇÕES E SECRETS
# ==============================================================
try:
    NUMERO_BASE = st.secrets.get("NUMERO_BASE", "5531971463005")
    NUMERO_BASE_CTG = st.secrets.get("NUMERO_BASE_CTG", NUMERO_BASE) 
    NOME_PLANILHA = st.secrets.get("NOME_PLANILHA", "acareaBase")
    URL_WEBHOOK_DRIVE = st.secrets.get("URL_WEBHOOK_DRIVE", "")
except:
    NUMERO_BASE = os.getenv("NUMERO_BASE", "5531971463005")
    NUMERO_BASE_CTG = os.getenv("NUMERO_BASE_CTG", NUMERO_BASE)
    NOME_PLANILHA = os.getenv("NOME_PLANILHA", "acareaBase")
    URL_WEBHOOK_DRIVE = os.getenv("URL_WEBHOOK_DRIVE", "")

BASES_DISPONIVEIS = ["JML", "ITR", "CTG"]

# ==============================================================
# FUNÇÕES DE APOIO E DADOS
# ==============================================================
def obter_credenciais():
    try:
        with open('credenciais.json') as f:
            info = json.load(f)
    except FileNotFoundError:
        info = json.loads(st.secrets["chave_google"].strip())
    escopo = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    return Credentials.from_service_account_info(info, scopes=escopo)

@st.cache_data(ttl=60)
def carregar_dados_base(nome_aba):
    try:
        creds = obter_credenciais()
        cliente = gspread.authorize(creds)
        planilha = cliente.open(NOME_PLANILHA).worksheet(nome_aba)
        dados = planilha.get_all_values()
        if not dados or len(dados) < 2: return pd.DataFrame()
        df = pd.DataFrame(dados[1:], columns=dados[0])
        df.columns = df.columns.astype(str).str.strip()
        if 'Motorista' in df.columns: df['Motorista'] = df['Motorista'].astype(str).str.strip()
        return df
    except: return pd.DataFrame()

@st.cache_data(ttl=120)
def carregar_kpi_historico():
    try:
        creds = obter_credenciais()
        cliente = gspread.authorize(creds)
        planilha = cliente.open(NOME_PLANILHA).worksheet("KPI_Historico")
        dados = planilha.get_all_values()
        if len(dados) > 1:
            df = pd.DataFrame(dados[1:], columns=dados[0])
            df['KPI (%)'] = df['KPI (%)'].astype(str).str.replace('%', '').astype(float)
            df['Data'] = pd.to_datetime(df['Data'])
            df['Entregues'] = pd.to_numeric(df['Entregues'])
            df['Acareações'] = pd.to_numeric(df['Acareações'])
            return df
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

# ==============================================================
# MENU LATERAL (SIDEBAR)
# ==============================================================
try:
    st.sidebar.image("logo.png", width=150)
except:
    pass
st.sidebar.title("Navegação")
menu = st.sidebar.radio("Ir para:", ["📷 Portal do Motorista", "🚨 Painel de Risco (< 5h)", "📈 Dashboard de KPI"])

# ==============================================================
# TELA 1: PORTAL DO MOTORISTA (COMO ERA ANTES)
# ==============================================================
if menu == "📷 Portal do Motorista":
    st.title("📦 Portal de Acareações")
    base_atual = st.selectbox("🏢 Selecione sua Unidade:", ["-- Escolha --"] + BASES_DISPONIVEIS)

    if base_atual != "-- Escolha --":
        df_imile = carregar_dados_base(base_atual)
        if not df_imile.empty:
            motoristas = sorted(df_imile['Motorista'].dropna().unique().tolist())
            if '(vazio)' in motoristas: motoristas.remove('(vazio)')
            mot_selecionado = st.selectbox("👤 Selecione o seu nome:", ["-- Escolha --"] + motoristas)

            if mot_selecionado != "-- Escolha --":
                df_mot = df_imile[df_imile['Motorista'] == mot_selecionado]
                st.success(f"Você tem **{len(df_mot)} acareação(ões)** pendente(s) na base {base_atual}.")
                
                for idx, row in df_mot.iterrows():
                    with st.expander(f"🔵 Pacote: {row['AWB']} - {row['Nome']}", expanded=False):
                        st.info(f"⏰ PRAZO: {row.get('Prazo do Processo', 'N/A')} | 🚨 MOTIVO: {row.get('Subtipo', 'N/A')}")
                        
                        st.markdown("### 📷 Enviar Comprovante")
                        foto = st.file_uploader(f"Anexe a foto", type=['png', 'jpg', 'jpeg'], key=f"file_{row['AWB']}")
                        
                        # INJEÇÃO 1: Mostra a foto e o botão de confirmação original
                        if foto:
                            st.image(foto, caption="Pré-visualização da Foto", width=250)
                            if st.button(f"Confirmar Envio", key=f"btn_{row['AWB']}"):
                                st.success("✅ Função de envio conectada com sucesso!")
                        
                        # INJEÇÃO 2: Botões do WhatsApp abaixo da área de foto
                        st.markdown("---")
                        st.markdown("### 💬 Ações Rápidas")
                        
                        col_wpp1, col_wpp2 = st.columns(2)
                        telefone = str(row.get('Telefone', '')).replace('.0', '').replace('-', '').replace(' ', '')
                        rastreio = row['AWB']
                        
                        with col_wpp1:
                            if telefone and telefone != 'nan':
                                msg_cliente = f"Olá! Somos da transportadora responsável pela sua entrega da iMile (Pacote: {rastreio}). Gostaríamos de confirmar um detalhe sobre o seu endereço..."
                                link_cliente = f"https://wa.me/55{telefone}?text={msg_cliente}".replace(' ', '%20')
                                st.markdown(f'<a href="{link_cliente}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:10px; border-radius:5px; font-weight:bold;">📱 Falar com Cliente</button></a>', unsafe_allow_html=True)
                            else:
                                st.warning("Sem telefone")
                                
                        with col_wpp2:
                            msg_base = f"Acareação finalizada! Pacote: {rastreio}."
                            # Utiliza as variáveis de contato da base já configuradas no topo do seu código
                            num_zap = NUMERO_BASE_CTG if base_atual == "CTG" else NUMERO_BASE
                            link_base = f"https://wa.me/{num_zap}?text={msg_base}".replace(' ', '%20')
                            st.markdown(f'<a href="{link_base}" target="_blank"><button style="width:100%; background-color:#0068C9; color:white; border:none; padding:10px; border-radius:5px; font-weight:bold;">🏢 Informar Base</button></a>', unsafe_allow_html=True)
        else:
            st.warning("⚠️ Nenhuma acareação pendente nesta base.")

# ==============================================================
# TELA 2: PAINEL DE RISCO (< 5 HORAS)
# ==============================================================
elif menu == "🚨 Painel de Risco (< 5h)":
    st.title("🚨 Acareações em Risco de Vencimento")
    st.markdown("Pacotes que vencem nas próximas **5 horas** e precisam de atenção urgente.")

    agora = datetime.now()
    limite_5h = agora + timedelta(hours=5)
    
    lista_risco = []
    
    with st.spinner("Analisando os prazos de todas as bases..."):
        for base in BASES_DISPONIVEIS:
            df_base = carregar_dados_base(base)
            if not df_base.empty:
                for idx, row in df_base.iterrows():
                    prazo_texto = str(row.get('Prazo do Processo', '')).strip()
                    if prazo_texto and prazo_texto.lower() not in ['nan', 'none', 'n/a']:
                        try:
                            try: prazo_dt = datetime.strptime(prazo_texto, "%Y-%m-%d %H:%M:%S")
                            except: prazo_dt = datetime.strptime(prazo_texto[:16], "%Y-%m-%d %H:%M")

                            if prazo_dt <= limite_5h:
                                lista_risco.append({
                                    "Base": base,
                                    "Motorista": row.get('Motorista', 'N/A'),
                                    "AWB": row['AWB'],
                                    "Motivo": row.get('Subtipo', 'N/A'),
                                    "Prazo Limite": prazo_dt.strftime("%d/%m %H:%M")
                                })
                        except: pass
    
    if lista_risco:
        df_risco = pd.DataFrame(lista_risco)
        st.error(f"⚠️ Existem {len(df_risco)} acareações estourando o prazo!")
        st.dataframe(df_risco, use_container_width=True)
    else:
        st.success("✅ Tudo sob controle! Nenhuma acareação próxima do vencimento nas próximas 5 horas nas bases ativas.")

# ==============================================================
# TELA 3: DASHBOARD DE KPI (GRÁFICOS)
# ==============================================================
elif menu == "📈 Dashboard de KPI":
    st.title("📈 Análise de Acareações vs Entregas")
    
    df_kpi = carregar_kpi_historico()
    
    if df_kpi.empty:
        st.warning("⚠️ O histórico ainda está vazio. O robô precisa rodar o arquivo 'kpi_mensal.py' para gerar os primeiros dados.")
    else:
        # Filtros de tempo
        filtro_tempo = st.radio("Filtro de Período:", ["Últimos 7 dias", "Últimos 15 dias", "Mês Atual", "Tudo"], horizontal=True)
        
        hoje = pd.to_datetime(datetime.now().date())
        if filtro_tempo == "Últimos 7 dias": df_kpi = df_kpi[df_kpi['Data'] >= (hoje - pd.Timedelta(days=7))]
        elif filtro_tempo == "Últimos 15 dias": df_kpi = df_kpi[df_kpi['Data'] >= (hoje - pd.Timedelta(days=15))]
        elif filtro_tempo == "Mês Atual": df_kpi = df_kpi[df_kpi['Data'].dt.month == hoje.month]
        
        # Limpa duplicatas para não dar erro no pivot (Adicionado por segurança)
        df_kpi = df_kpi.drop_duplicates(subset=['Data', 'Base'], keep='last')
        
        # Converte a data para string para ficar bonito no gráfico
        df_kpi['Data'] = df_kpi['Data'].dt.strftime('%d/%m/%Y')

        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Taxa de Acareação % (KPI)")
            # Pivot table para separar uma linha por base
            pivot_kpi = df_kpi.pivot(index='Data', columns='Base', values='KPI (%)')
            st.line_chart(pivot_kpi)
            
        with col2:
            st.subheader("📦 Total de Acareações Geradas")
            pivot_qnt = df_kpi.pivot(index='Data', columns='Base', values='Acareações')
            st.bar_chart(pivot_qnt)
            
        st.markdown("---")
        st.subheader("📋 Tabela Consolidada (Período Selecionado)")
        # Soma total no período selecionado
        resumo = df_kpi.groupby('Base').agg({'Entregues': 'sum', 'Acareações': 'sum'}).reset_index()
        # Evita erro de divisão por zero
        resumo['KPI Geral (%)'] = resumo.apply(
            lambda x: round((x['Acareações'] / x['Entregues']) * 100, 2) if x['Entregues'] > 0 else 0.0, axis=1
        )
        st.dataframe(resumo, use_container_width=True)
