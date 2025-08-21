import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from passlib.hash import pbkdf2_sha256
import plotly.express as px
from datetime import datetime


# ============================
# 🔑 Conexão com Google Sheets
# ============================
@st.cache_resource
def connect_gsheets():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"]
    )
    client = gspread.authorize(creds)
    # Coloque aqui o ID da sua planilha
    SHEET_ID = "1IvojPJOmgwEl6oySfKTl-5jC7TJfYrpFtwWptHl1Y4w"
    return client.open_by_key(SHEET_ID)


sh = connect_gsheets()
ws_usuarios = sh.worksheet("usuarios")
ws_transacoes = sh.worksheet("transacoes")
ws_categorias = sh.worksheet("categorias")


# =====================================
# 📌 Funções de manipulação de dados
# =====================================
def listar_usuarios():
    dados = ws_usuarios.get_all_records()
    return pd.DataFrame(dados)


def adicionar_usuario(email, senha, admin=0):
    usuarios = listar_usuarios()
    if not usuarios.empty and email in usuarios["email"].values:
        return False
    senha_hash = pbkdf2_sha256.hash(senha)
    nova_linha = [len(usuarios) + 1, email, senha_hash, admin]
    ws_usuarios.append_row(nova_linha)
    return True


def autenticar(email, senha):
    usuarios = listar_usuarios()
    if usuarios.empty:
        return None
    usuario = usuarios.loc[usuarios["email"] == email]
    if usuario.empty:
        return None
    usuario = usuario.iloc[0]
    if pbkdf2_sha256.verify(senha, usuario["senha"]):
        return usuario.to_dict()
    return None


def listar_categorias():
    dados = ws_categorias.get_all_records()
    return [d["nome"] for d in dados]


def listar_transacoes(usuario_id):
    dados = ws_transacoes.get_all_records()
    if not dados:
        return pd.DataFrame()
    df = pd.DataFrame(dados)
    return df[df["usuario_id"] == usuario_id]


def adicionar_transacao(usuario_id, descricao, valor, tipo, categoria, data):
    transacoes = ws_transacoes.get_all_records()
    nova_linha = [
        len(transacoes) + 1,
        usuario_id,
        descricao,
        float(valor),
        tipo,
        categoria,
        data.strftime("%Y-%m-%d")
    ]
    ws_transacoes.append_row(nova_linha)


# =====================================
# 🎨 Layout das telas
# =====================================
def tela_login():
    st.title("📊 Contabilidade MEI - Login")

    email = st.text_input("E-mail")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        usuario = autenticar(email, senha)
        if usuario:
            st.session_state.usuario = usuario
            st.experimental_rerun()
        else:
            st.error("E-mail ou senha inválidos.")


def dashboard_financeiro(usuario):
    st.subheader("📊 Dashboard Financeiro")

    transacoes = listar_transacoes(usuario["id"])
    if transacoes.empty:
        st.info("Nenhuma transação registrada ainda.")
        return

    saldo = transacoes.apply(lambda x: x["valor"] if x["tipo"] == "Receita" else -x["valor"], axis=1).sum()
    st.metric("💰 Saldo Atual", f"R$ {saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    fig = px.bar(
        transacoes,
        x="categoria",
        y="valor",
        color="tipo",
        title="Receitas e Despesas por Categoria"
    )
    st.plotly_chart(fig)


def tela_transacoes(usuario):
    st.subheader("➕ Nova Transação")

    descricao = st.text_input("Descrição")
    valor = st.number_input("Valor", min_value=0.0, step=0.01)
    tipo = st.selectbox("Tipo", ["Receita", "Despesa"])
    categoria = st.selectbox("Categoria", listar_categorias())
    data = st.date_input("Data", datetime.today())

    if st.button("Salvar"):
        adicionar_transacao(usuario["id"], descricao, valor, tipo, categoria, data)
        st.success("Transação adicionada com sucesso!")
        st.experimental_rerun()


def tela_principal():
    usuario = st.session_state.usuario
    st.sidebar.title(f"Bem-vindo, {usuario['email']}")

    menu = st.sidebar.radio("Menu", ["Dashboard", "Transações", "Sair"])

    if menu == "Dashboard":
        dashboard_financeiro(usuario)
    elif menu == "Transações":
        tela_transacoes(usuario)
    elif menu == "Sair":
        st.session_state.clear()
        st.experimental_rerun()


# =====================================
# 🚀 Execução principal
# =====================================
if "usuario" not in st.session_state:
    tela_login()
else:
    tela_principal()
