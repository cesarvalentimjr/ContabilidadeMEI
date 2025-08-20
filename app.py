import streamlit as st
import sqlite3
from datetime import datetime
import hashlib
import os
import pandas as pd
import plotly.express as px

# ---------------------------
# Banco de dados SQLite
# ---------------------------
DB_FILE = "meu_app.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    # Usuários
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        nome TEXT NOT NULL,
        senha TEXT NOT NULL,
        admin INTEGER DEFAULT 0
    )
    """)
    # Categorias
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categorias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        tipo TEXT CHECK(tipo IN ('entrada','saida')) NOT NULL
    )
    """)
    # Transações
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        descricao TEXT,
        valor REAL NOT NULL,
        tipo TEXT CHECK(tipo IN ('entrada','saida')) NOT NULL,
        categoria_id INTEGER,
        data TEXT NOT NULL,
        FOREIGN KEY(usuario_id) REFERENCES usuarios(id),
        FOREIGN KEY(categoria_id) REFERENCES categorias(id)
    )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------------------
# Hash de senha
# ---------------------------
def hash_senha(senha):
    salt = os.urandom(16)
    hash_bytes = hashlib.pbkdf2_hmac('sha256', senha.encode(), salt, 100000)
    return salt.hex() + hash_bytes.hex()

def verificar_senha(senha_digitada, hash_armazenado):
    salt = bytes.fromhex(hash_armazenado[:32])
    hash_armazenado_bytes = bytes.fromhex(hash_armazenado[32:])
    hash_digitado = hashlib.pbkdf2_hmac('sha256', senha_digitada.encode(), salt, 100000)
    return hash_digitado == hash_armazenado_bytes

# ---------------------------
# Funções de usuários
# ---------------------------
def cadastrar_usuario(email, nome, senha, admin=0):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        senha_hash = hash_senha(senha)
        cursor.execute(
            "INSERT INTO usuarios (email, nome, senha, admin) VALUES (?, ?, ?, ?)",
            (email, nome, senha_hash, admin)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def login_usuario(email, senha):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM usuarios WHERE email = ?",
        (email,)
    )
    user = cursor.fetchone()
    conn.close()
    if user and verificar_senha(senha, user["senha"]):
        return user
    return None

# ---------------------------
# Funções de categorias
# ---------------------------
def listar_categorias(tipo=None):
    conn = get_connection()
    cursor = conn.cursor()
    if tipo:
        cursor.execute("SELECT * FROM categorias WHERE tipo = ?", (tipo,))
    else:
        cursor.execute("SELECT * FROM categorias")
    rows = cursor.fetchall()
    conn.close()
    return rows

def adicionar_categoria(nome, tipo):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO categorias (nome, tipo) VALUES (?, ?)", (nome, tipo))
    conn.commit()
    conn.close()

# ---------------------------
# Funções de transações
# ---------------------------
def registrar_transacao(usuario_id, descricao, valor, tipo, categoria_id, data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO transacoes (usuario_id, descricao, valor, tipo, categoria_id, data) VALUES (?, ?, ?, ?, ?, ?)",
        (usuario_id, descricao, valor, tipo, categoria_id, data)
    )
    conn.commit()
    conn.close()

def listar_transacoes(usuario_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT t.id, t.descricao, t.valor, t.tipo, t.data, c.nome AS categoria
           FROM transacoes t
           LEFT JOIN categorias c ON t.categoria_id = c.id
           WHERE t.usuario_id = ?
           ORDER BY t.data DESC""",
        (usuario_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows

# ---------------------------
# Dashboard com layout visual
# ---------------------------
def dashboard_financeiro(usuario_id):
    transacoes = listar_transacoes(usuario_id)
    if not transacoes:
        st.info("Nenhuma transação registrada.")
        return

    df = pd.DataFrame(transacoes)
    df['data'] = pd.to_datetime(df['data'])

    # Filtros
    st.subheader("Filtros")
    min_data = df['data'].min()
    max_data = df['data'].max()
    col1, col2, col3 = st.columns(3)
    with col1:
        start_date = st.date_input("Data Inicial", min_data)
    with col2:
        end_date = st.date_input("Data Final", max_data)
    with col3:
        tipo_filter = st.selectbox("Tipo", ["todos","entrada","saida"])
    
    categorias = list(df['categoria'].dropna().unique())
    categoria_filter = st.multiselect("Categorias", categorias, default=categorias)

    df_filtered = df[
        (df['data'] >= pd.to_datetime(start_date)) &
        (df['data'] <= pd.to_datetime(end_date))
    ]
    if tipo_filter != "todos":
        df_filtered = df_filtered[df_filtered['tipo'] == tipo_filter]
    if categoria_filter:
        df_filtered = df_filtered[df_filtered['categoria'].isin(categoria_filter)]

    # Cards de resumo com cores e emojis
    total_entrada = df_filtered[df_filtered['tipo']=='entrada']['valor'].sum()
    total_saida = df_filtered[df_filtered['tipo']=='saida']['valor'].sum()
    saldo = total_entrada - total_saida

    st.subheader("Resumo Financeiro")
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Entradas", f"R$ {total_entrada:.2f}", delta=None)
    col2.metric("📉 Saídas", f"R$ {total_saida:.2f}", delta=None)
    col3.metric("📈 Saldo", f"R$ {saldo:.2f}", delta=None)

    # Gráficos em colunas
    st.subheader("Gráficos")
    col1, col2 = st.columns(2)
    # Entradas e saídas por mês
    df_mes = df_filtered.groupby([df_filtered['data'].dt.to_period('M'), 'tipo'])['valor'].sum().reset_index()
    df_mes['data'] = df_mes['data'].dt.to_timestamp()
    fig = px.bar(df_mes, x='data', y='valor', color='tipo', barmode='group', title="Entradas e Saídas por Mês")
    col1.plotly_chart(fig, use_container_width=True)

    # Distribuição por categoria
    df_cat = df_filtered.groupby(['categoria','tipo'])['valor'].sum().reset_index()
    fig2 = px.pie(df_cat, names='categoria', values='valor', title="Distribuição por Categoria")
    col2.plotly_chart(fig2, use_container_width=True)

    # Tabela detalhada
    st.subheader("Transações Detalhadas")
    st.dataframe(df_filtered[['data','descricao','categoria','tipo','valor']].sort_values(by='data', ascending=False))
    csv = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button("Exportar CSV", csv, "transacoes.csv", "text/csv")

# ---------------------------
# Interface Streamlit
# ---------------------------
st.set_page_config(page_title="Contabilidade MEI", layout="wide")
st.title("📊 Contabilidade MEI - Dashboard Financeiro")

if "usuario" not in st.session_state:
    st.session_state.usuario = None

# ---------------------------
# Tela de cadastro
# ---------------------------
def tela_cadastro():
    st.subheader("Cadastro de Usuário")
    col1, col2 = st.columns(2)
    with col1:
        nome = st.text_input("Nome", key="cad_nome")
        email = st.text_input("Email", key="cad_email")
    with col2:
        senha = st.text_input("Senha", type="password", key="cad_senha")
        admin_checkbox = st.checkbox("Cadastrar como admin", key="cad_admin")
    if st.button("Cadastrar", key="btn_cadastrar"):
        admin_val = 1 if admin_checkbox else 0
        if cadastrar_usuario(email, nome, senha, admin_val):
            st.success("Usuário cadastrado com sucesso! Faça login na aba lateral.")
        else:
            st.error("Email já cadastrado!")

# ---------------------------
# Tela de login
# ---------------------------
def tela_login():
    st.subheader("Login")
    email = st.text_input("Email", key="login_email")
    senha = st.text_input("Senha", type="password", key="login_senha")
    if st.button("Login", key="btn_login"):
        user = login_usuario(email, senha)
        if user:
            st.session_state.usuario = user
            st.success(f"Bem-vindo, {user['nome']}!")
        else:
            st.error("Email ou senha incorretos!")

# ---------------------------
# Tela principal (corrigida)
# ---------------------------
def tela_principal():
    usuario = st.session_state.usuario

    if not usuario:
        st.warning("Usuário não logado. Por favor, faça login.")
        st.stop()

    tabs = ["Dashboard", "Registrar Transação"]
    if usuario.get("admin", 0):
        tabs += ["Categorias", "Usuários"]

    selected_tab = st.tabs(tabs)

    with selected_tab[0]:
        dashboard_financeiro(usuario["id"])

    with selected_tab[1]:
        st.subheader("Registrar nova transação")
        col1, col2 = st.columns([3, 1])
        with col1:
            descricao = st.text_input("Descrição", key="trans_desc")
            valor = st.number_input("Valor", min_value=0.0, format="%.2f", key="trans_valor")
            tipo = st.selectbox("Tipo", ["entrada", "saida"], key="trans_tipo")
            categorias = listar_categorias(tipo)
            if categorias:
                cat_dict = {c['nome']: c['id'] for c in categorias}
                categoria_selecionada = st.selectbox("Categoria", list(cat_dict.keys()), key="trans_cat")
                categoria_id = cat_dict[categoria_selecionada]
            else:
                st.warning("Nenhuma categoria cadastrada para este tipo.")
                categoria_id = None
            data = st.date_input("Data", datetime.today(), key="trans_data")
        with col2:
            st.write("")
            if st.button("Registrar", key="btn_registrar_trans"):
                if descricao and valor > 0 and categoria_id:
                    registrar_transacao(usuario["id"], descricao, valor, tipo, categoria_id, data.strftime("%Y-%m-%d"))
                    st.success("✅ Transação registrada!")
                else:
                    st.error("Preencha todos os campos corretamente.")

    if usuario.get("admin", 0):
        with selected_tab[2]:
            st.subheader("Gerenciar Categorias")
            col1, col2 = st.columns(2)
            with col1:
                tipo_cat = st.selectbox("Tipo de Categoria", ["entrada", "saida"], key="adm_tipo_cat")
            with col2:
                nova_cat = st.text_input("Nova Categoria", key="adm_nova_cat")
            if st.button("Adicionar Categoria", key="btn_add_cat"):
                if nova_cat:
                    adicionar_categoria(nova_cat, tipo_cat)
                    st.success("✅ Categoria adicionada!")
                else:
                    st.error("Digite o nome da categoria.")

        with selected_tab[3]:
            st.subheader("Usuários cadastrados")
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome, email, admin FROM usuarios")
            rows = cursor.fetchall()
            conn.close()
            df_users = pd.DataFrame(rows)
            st.dataframe(df_users)

    if st.button("Logout"):
        st.session_state.usuario = None
        st.experimental_rerun()

# ---------------------------
# Menu lateral
# ---------------------------
if st.session_state.usuario is None:
    menu = st.sidebar.selectbox("Menu", ["Login", "Cadastrar"])
    if menu == "Cadastrar":
        tela_cadastro()
    else:
        tela_login()
else:
    tela_principal()
