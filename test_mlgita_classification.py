from extract_bb_statement import extract_mlgita_statement
from classify_transactions import add_category_column
import pandas as pd

# Carregar o conteúdo Markdown do extrato MLGITA
with open("docling_output_mlgita.md", "r") as f:
    mlgita_markdown = f.read()

# Extrair o DataFrame
df_mlgita = extract_mlgita_statement(mlgita_markdown)

# Adicionar a coluna de categoria
df_mlgita_classified = add_category_column(df_mlgita)

# Exibir as primeiras linhas do DataFrame classificado
print(df_mlgita_classified.head(10).to_markdown(index=False))

