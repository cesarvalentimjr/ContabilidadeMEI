import pandas as pd
import re

def extract_bb_statement(markdown_content):
    lines = markdown_content.split("\n")
    transactions = []
    current_date = None

    # Novo padrão flexível
    transaction_pattern_bb = re.compile(
        r'(\d{2}/\d{2}/\d{4})\s+(?:\d+\s+){0,3}([A-ZÁ-Úa-zá-ú0-9\-\s\.\,\/]+?)\s+([\d\.]+,\d{2})\s*([CD])(?:\s+[\d\.]+,\d{2}\s*[CD])?'
    )

    for line in lines:
        match = transaction_pattern_bb.search(line)
        if match:
            date_str = match.group(1)
            current_date = pd.to_datetime(date_str, format='%d/%m/%Y', errors='coerce')
            description = match.group(2).strip()
            value_str = match.group(3).replace('.', '').replace(',', '.')
            value_type = match.group(4)
            value = float(value_str)
            if value_type == 'D':
                value *= -1
            transactions.append({'Data': current_date, 'Histórico': description, 'Valor': value})

    return pd.DataFrame(transactions)


