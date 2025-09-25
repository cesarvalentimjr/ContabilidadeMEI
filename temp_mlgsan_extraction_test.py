from extract_bb_statement import extract_mlgsan_statement
import pandas as pd

with open("docling_output_mlgsan.md", "r") as f:
    mlgsan_markdown = f.read()

df_mlgsan = extract_mlgsan_statement(mlgsan_markdown)
print(df_mlgsan.head().to_markdown(index=False))

