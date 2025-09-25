from extract_bb_statement import extract_bb_statement
import pandas as pd

with open('docling_output.md', 'r') as f:
    bb_markdown = f.read()

df_bb = extract_bb_statement(bb_markdown)
print(df_bb.head().to_markdown(index=False))

