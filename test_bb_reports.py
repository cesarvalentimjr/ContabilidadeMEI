from extract_bb_statement import extract_bb_statement
from classify_transactions import add_category_column
from generate_reports import generate_cash_flow_report, generate_monthly_cash_flow
import pandas as pd

# Carregar o conteúdo Markdown do extrato do BB
with open("docling_output.md", "r") as f:
    bb_markdown = f.read()

# Extrair e classificar o DataFrame
df_bb = extract_bb_statement(bb_markdown)
df_bb_classified = add_category_column(df_bb)

# Gerar relatório de fluxo de caixa geral
receitas_bb, despesas_bb, saldo_total_bb = generate_cash_flow_report(df_bb_classified)

print("--- Relatório de Fluxo de Caixa Geral (Banco do Brasil) ---")
print("\nReceitas:")
print(receitas_bb.to_markdown(index=False))
print("\nDespesas:")
print(despesas_bb.to_markdown(index=False))
print(f"\nSaldo Total: {saldo_total_bb:.2f}")

# Gerar relatório de fluxo de caixa mensal
monthly_report_bb = generate_monthly_cash_flow(df_bb_classified)
print("\n--- Relatório de Fluxo de Caixa Mensal (Banco do Brasil) ---")
print(monthly_report_bb.to_markdown())

