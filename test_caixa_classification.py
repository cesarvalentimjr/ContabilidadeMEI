from extract_bb_statement import extract_caixa_statement
from classify_transactions import add_category_column
import pandas as pd

# Carregar o conteúdo Markdown do extrato da Caixa
with open("docling_output_2.md", "r") as f:
    caixa_markdown = f.read()

# Extrair o DataFrame
df_caixa = extract_caixa_statement(caixa_markdown)

# Adicionar a coluna de categoria
df_caixa_classified = add_category_column(df_caixa)

# Exibir as primeiras linhas do DataFrame classificado
print(df_caixa_classified.head(10).to_markdown(index=False))

