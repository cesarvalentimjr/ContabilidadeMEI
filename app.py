import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ======================
# Configurações
# ======================
SHEET_NAME = "BD_MicroEmpreendedores"
USERS_TAB = "Usuarios"
TX_TAB = "Transacoes"

st.set_page_config(page_title="App Financeiro", layout="wide")

# ======================
# Conexão com Google Sheets
# ======================
def connect_gsheets():
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]

    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope
    )
    client = gspread.authorize(creds)
    return client

def get_worksheet(sheet_name, tab_name):
    client = connect_gsheets()
    return client.open(sheet_name).worksheet(tab_name)

def read_as_df(sheet_name, tab_name):
    sheet = get_worksheet(sheet_name, tab_name)
    records = sheet.get_all_records()
    df = pd.DataFrame(records)
    return df

def add_transaction(sheet_name, tab_name, data):
    sheet = get_worksheet(sheet_name, tab_name)
    sheet.append_row(data)

# ======================
# Autenticação simples
# ======================
def login():
    st.sidebar.subheader("Login")
    email = st.sidebar.text_input("Digite seu e-mail")

    if st.sidebar.button("Entrar"):
        users_df = read_as_df(SHEET_NAME, USERS_TAB)
        if email in users_df["email"].values:
            st.session_state["user"] = email
            st.sidebar.success(f"Bem-vindo, {email}!")
        else:
            st.sidebar.error("Acesso negado: e-mail não autorizado.")

def check_auth():
    return "user" in st.session_state

# ======================
# App principal
# ======================
if not check_auth():
    login()
    st.stop()

st.title("📊 Sistema Financeiro para Microempreendedores")

# Formulário de registro de transações
st.header("Registrar Transação")
with st.form("nova_transacao"):
    data = st.date_input("Data")
    descricao = st.text_input("Descrição")
    categoria = st.selectbox("Categoria", ["Venda", "Despesa Fixa", "Despesa Variável", "Imposto"])
    valor = st.number_input("Valor", step=0.01)
    tipo = st.radio("Tipo", ["Entrada", "Saída"])
    submitted = st.form_submit_button("Salvar")

    if submitted:
        add_transaction(
            SHEET_NAME,
            TX_TAB,
            [str(data), descricao, categoria, valor, tipo, st.session_state["user"]]
        )
        st.success("Transação registrada com sucesso!")

# Consulta das transações
st.header("Transações Registradas")
df = read_as_df(SHEET_NAME, TX_TAB)

if not df.empty:
    df_user = df[df["usuario"] == st.session_state["user"]]
    st.dataframe(df_user)
else:
    st.info("Nenhuma transação registrada ainda.")
