from extract_bb_statement import extract_caixa_statement
import pandas as pd

with open("docling_output_2.md", "r") as f:
    caixa_markdown = f.read()

df_caixa = extract_caixa_statement(caixa_markdown)
print(df_caixa.head().to_markdown(index=False))

