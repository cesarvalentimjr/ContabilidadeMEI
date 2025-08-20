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
    
    # Tabela de usuários
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        nome TEXT NOT NULL,
        senha TEXT NOT NULL
    )
    """)
    
    # Tabela de transações
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

# Inicializa o banco
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

# Menu lateral
pagina = st.sidebar.selectbox("Menu", ["Login", "Cadastrar"])

if pagina == "Cadastrar":
    st.subheader("Cadastro de Usuário")
    nome = st.text_input("Nome")
    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")
    if st.button("Cadastrar"):
        if cadastrar_usuario(email, nome, senha):
            st.success("Usuário cadastrado com sucesso! Faça login na aba lateral.")
        else:
            st.error("Email já cadastrado!")

elif pagina == "Login":
    st.subheader("Login")
    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")
    if st.button("Login"):
        user = login_usuario(email, senha)
        if user:
            st.success(f"Bem-vindo, {user['nome']}!")

            # ---------------------------
            # Registrar nova transação
            # ---------------------------
            st.subheader("Registrar nova transação")
            descricao = st.text_input("Descrição")
            valor = st.number_input("Valor", min_value=0.0, format="%.2f")
            tipo = st.selectbox("Tipo", ["entrada", "saida"])
            data = st.date_input("Data", datetime.today())
            if st.button("Registrar"):
                registrar_transacao(user["id"], descricao, valor, tipo, data.strftime("%Y-%m-%d"))
                st.success("Transação registrada!")

            # ---------------------------
            # Histórico de transações
            # ---------------------------
            st.subheader("Histórico de transações")
            transacoes = listar_transacoes(user["id"])
            if transacoes:
                for t in transacoes:
                    st.write(f"{t['data']} - {t['descricao']} - {t['tipo']} - R${t['valor']:.2f}")
            else:
                st.info("Nenhuma transação registrada.")

            # ---------------------------
            # Relatório de fluxo de caixa
            # ---------------------------
            st.subheader("Resumo financeiro")
            total_entrada, total_saida, saldo = calcular_fluxo(user["id"])
            st.write(f"Total de entradas: R${total_entrada:.2f}")
            st.write(f"Total de saídas: R${total_saida:.2f}")
            st.write(f"Saldo atual: R${saldo:.2f}")

        else:
            st.error("Email ou senha incorretos!")




