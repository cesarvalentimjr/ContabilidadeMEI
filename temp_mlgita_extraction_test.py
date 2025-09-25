from extract_bb_statement import extract_mlgita_statement
import pandas as pd

with open("docling_output_mlgita.md", "r") as f:
    mlgita_markdown = f.read()

df_mlgita = extract_mlgita_statement(mlgita_markdown)
print(df_mlgita.head().to_markdown(index=False))

