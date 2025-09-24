import streamlit as st
import pandas as pd
import os
from docling.document_converter import DocumentConverter
from extract_bb_statement import (
    extract_bb_statement, extract_caixa_statement,
    extract_mlgita_statement, extract_mlgsan_statement
)
from classify_transactions import add_category_column
from generate_reports import generate_cash_flow_report, generate_monthly_cash_flow

st.set_page_config(page_title="Extrator de Extratos Bancários", layout="wide")

st.title("📊 Extrator e Analisador de Extratos Bancários")

uploaded_files = st.file_uploader("Selecione um ou mais PDFs de extratos bancários:", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    converter = DocumentConverter()
    all_data = []

    for uploaded_file in uploaded_files:
        st.write(f"### Processando **{uploaded_file.name}**")
        # Salvar temporariamente
        pdf_path = uploaded_file.name
        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Converter para markdown
        try:
            result = converter.convert(pdf_path)
            markdown_content = result.document.export_to_markdown()
        except Exception as e:
            st.error(f"Erro ao converter {uploaded_file.name}: {e}")
            continue

        # Escolher função de extração
        name = uploaded_file.name.lower()
        if "bb" in name:
            df = extract_bb_statement(markdown_content)
        elif "caixa" in name:
            df = extract_caixa_statement(markdown_content)
        elif "mlgita" in name:
            df = extract_mlgita_statement(markdown_content)
        elif "mlgsan" in name:
            df = extract_mlgsan_statement(markdown_content)
        else:
            st.warning(f"Não reconheci o banco para {uploaded_file.name}.")
            continue

        if df.empty:
            st.warning(f"Nenhuma transação encontrada em {uploaded_file.name}.")
            continue

        # Classificar transações
        df = add_category_column(df)
        st.dataframe(df, use_container_width=True)
        all_data.append(df)

    # Juntar tudo para relatórios
    if all_data:
        df_all = pd.concat(all_data)
        st.subheader("📑 Relatório Consolidado")
        receitas, despesas, saldo = generate_cash_flow_report(df_all)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Receitas")
            st.dataframe(receitas)
        with col2:
            st.markdown("#### Despesas")
            st.dataframe(despesas)

        st.metric("💰 Saldo Total", f"R$ {saldo:,.2f}")

        st.subheader("📆 Fluxo de Caixa Mensal")
        monthly = generate_monthly_cash_flow(df_all)
        st.dataframe(monthly)

        # Gráfico de evolução do saldo mensal
        saldo_mensal = monthly["Total Mensal"].reset_index()
        saldo_mensal["AnoMes"] = saldo_mensal["AnoMes"].astype(str)
        st.line_chart(data=saldo_mensal, x="AnoMes", y="Total Mensal")


