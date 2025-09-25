from extract_bb_statement import extract_mlgsan_statement
from classify_transactions import add_category_column
import pandas as pd

# Carregar o conteúdo Markdown do extrato MLGSAN
with open("docling_output_mlgsan.md", "r") as f:
    mlgsan_markdown = f.read()

# Extrair o DataFrame
df_mlgsan = extract_mlgsan_statement(mlgsan_markdown)

# Adicionar a coluna de categoria
df_mlgsan_classified = add_category_column(df_mlgsan)

# Exibir as primeiras linhas do DataFrame classificado
print(df_mlgsan_classified.head(10).to_markdown(index=False))

