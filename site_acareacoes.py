import streamlit as st
import os

st.set_page_config(layout="wide")
st.title("🕵️‍♀️ Página de Depuração de Ambiente")

st.header("1. Onde os arquivos estão?")
try:
    # O diretório raiz do seu repositório no servidor do Streamlit
    root_dir = "/mount/src/"
    
    st.write(f"Listando arquivos em `{root_dir}`:")
    
    # Lista os arquivos e diretórios na raiz
    files_in_root = os.listdir(root_dir)
    st.code('\n'.join(files_in_root))
    
except Exception as e:
    st.error(f"Erro ao tentar listar arquivos: {e}")

st.header("2. O 'requirements.txt' está sendo lido corretamente?")
try:
    # O caminho completo esperado para o arquivo
    req_path = "/mount/src/requirements.txt"
    
    st.write(f"Tentando ler o arquivo em `{req_path}`...")
    
    if os.path.exists(req_path):
        with open(req_path, 'r') as f:
            content = f.read()
        st.success("✅ Arquivo 'requirements.txt' encontrado! Conteúdo:")
        st.code(content)
    else:
        st.error("❌ ERRO CRÍTICO: O arquivo 'requirements.txt' NÃO foi encontrado no diretório raiz do repositório.")
        st.info("Verifique se o arquivo 'requirements.txt' está na pasta principal do seu projeto no GitHub, e não dentro de uma subpasta.")

except Exception as e:
    st.error(f"Erro ao tentar ler o requirements.txt: {e}")

st.header("3. Exploração Detalhada do Filesystem")
st.info("Esta seção tenta listar todos os arquivos para entendermos a estrutura do seu repositório no servidor.")
try:
    # Tenta listar um diretório acima para ter mais contexto
    mount_dir = "/mount/"
    st.write(f"Listando conteúdo de `{mount_dir}`:")
    mount_content = os.listdir(mount_dir)
    st.code('\n'.join(mount_content))

    # Explora o diretório principal de forma recursiva
    st.write(f"Explorando `{root_dir}` recursivamente:")
    file_list = []
    for root, dirs, files in os.walk(root_dir):
        # Transforma o caminho root para ser relativo a root_dir para clareza
        relative_root = os.path.relpath(root, root_dir)
        if relative_root == ".":
            relative_root = "" # Não mostra './' no início
        
        for name in dirs:
            file_list.append(os.path.join(relative_root, name) + '/')
        for name in files:
            file_list.append(os.path.join(relative_root, name))
    
    if file_list:
        st.code('\n'.join(sorted(file_list)))
    else:
        st.warning(f"Nenhum arquivo ou diretório encontrado em `{root_dir}` durante a exploração recursiva.")

except Exception as e:
    st.error(f"Erro durante a exploração detalhada do filesystem: {e}")

