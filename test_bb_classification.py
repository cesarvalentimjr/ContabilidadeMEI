from extract_bb_statement import extract_bb_statement
from classify_transactions import add_category_column
import pandas as pd

# Carregar o conteúdo Markdown do extrato do BB
with open("docling_output.md", "r") as f:
    bb_markdown = f.read()

# Extrair o DataFrame
df_bb = extract_bb_statement(bb_markdown)

# Adicionar a coluna de categoria
df_bb_classified = add_category_column(df_bb)

# Exibir as primeiras linhas do DataFrame classificado
print(df_bb_classified.head(10).to_markdown(index=False))

