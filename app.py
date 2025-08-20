import streamlit as st
import sqlite3
from datetime import datetime
import hashlib
import os

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
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        nome TEXT NOT NULL,
        senha TEXT NOT NULL
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        descricao TEXT,
        valor REAL NOT NULL,
        tipo TEXT CHECK(tipo IN ('entrada','saida')) NOT NULL,
        data TEXT NOT NULL,
        FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
    )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------------------
# Funções de hash de senha
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
def cadastrar_usuario(email, nome, senha):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        senha_hash = hash_senha(senha)
        cursor.execute(
            "INSERT INTO usuarios (email, nome, senha) VALUES (?, ?, ?)",
            (email, nome, senha_hash)
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
# Funções de transações
# ---------------------------
def registrar_transacao(usuario_id, descricao, valor, tipo, data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO transacoes (usuario_id, descricao, valor, tipo, data) VALUES (?, ?, ?, ?, ?)",
        (usuario_id, descricao, valor, tipo, data)
    )
    conn.commit()
    conn.close()

def listar_transacoes(usuario_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM transacoes WHERE usuario_id = ? ORDER BY data DESC",
        (usuario_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows

def calcular_fluxo(usuario_id):
    transacoes = listar_transacoes(usuario_id)
    total_entrada = sum(t["valor"] for t in transacoes if t["tipo"] == "entrada")
    total_saida = sum(t["valor"] for t in transacoes if t["tipo"] == "saida")
    saldo = total_entrada - total_saida
    return total_entrada, total_saida, saldo

# ---------------------------
# Interface Streamlit
# ---------------------------
st.title("📊 Contabilidade MEI")

# Inicializa o estado de sessão
if "usuario" not in st.session_state:
    st.session_state.usuario = None

# ---------------------------
# Tela de cadastro
# ---------------------------
def tela_cadastro():
    st.subheader("Cadastro de Usuário")
    nome = st.text_input("Nome", key="cad_nome")
    email = st.text_input("Email", key="cad_email")
    senha = st.text_input("Senha", type="password", key="cad_senha")
    if st.button("Cadastrar", key="btn_cadastrar"):
        if cadastrar_usuario(email, nome, senha):
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
# Tela principal após login
# ---------------------------
def tela_principal():
    st.subheader("Registrar nova transação")
    descricao = st.text_input("Descrição", key="trans_desc")
    valor = st.number_input("Valor", min_value=0.0, format="%.2f", key="trans_valor")
    tipo = st.selectbox("Tipo", ["entrada", "saida"], key="trans_tipo")
    data = st.date_input("Data", datetime.today(), key="trans_data")
    if st.button("Registrar transação", key="btn_registrar_trans"):
        if descricao and valor > 0:
            registrar_transacao(
                st.session_state.usuario["id"],
                descricao,
                valor,
                tipo,
                data.strftime("%Y-%m-%d")
            )
            st.success("Transação registrada!")
        else:
            st.error("Preencha descrição e valor corretamente.")

    st.subheader("Histórico de transações")
    transacoes = listar_transacoes(st.session_state.usuario["id"])
    if transacoes:
        for t in transacoes:
            st.write(f"{t['data']} - {t['descricao']} - {t['tipo']} - R${t['valor']:.2f}")
    else:
        st.info("Nenhuma transação registrada.")

    st.subheader("Resumo financeiro")
    total_entrada, total_saida, saldo = calcular_fluxo(st.session_state.usuario["id"])
    st.write(f"Total de entradas: R${total_entrada:.2f}")
    st.write(f"Total de saídas: R${total_saida:.2f}")
    st.write(f"Saldo atual: R${saldo:.2f}")

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


