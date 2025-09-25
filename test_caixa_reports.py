
from extract_bb_statement import extract_caixa_statement
from classify_transactions import add_category_column
from generate_reports import generate_cash_flow_report, generate_monthly_cash_flow
import pandas as pd

# Carregar o conteúdo Markdown do extrato da Caixa
with open("docling_output_2.md", "r") as f:
    caixa_markdown = f.read()

# Extrair e classificar o DataFrame
df_caixa = extract_caixa_statement(caixa_markdown)
df_caixa_classified = add_category_column(df_caixa)

# Gerar relatório de fluxo de caixa geral
receitas_caixa, despesas_caixa, saldo_total_caixa = generate_cash_flow_report(df_caixa_classified)

print("--- Relatório de Fluxo de Caixa Geral (Caixa) ---")
print("\nReceitas:")
print(receitas_caixa.to_markdown(index=False))
print("\nDespesas:")
print(despesas_caixa.to_markdown(index=False))
print(f"\nSaldo Total: {saldo_total_caixa:.2f}")

# Gerar relatório de fluxo de caixa mensal
monthly_report_caixa = generate_monthly_cash_flow(df_caixa_classified)
print("\n--- Relatório de Fluxo de Caixa Mensal (Caixa) ---")
print(monthly_report_caixa.to_markdown())

