import pandas as pd
import re

def extract_bb_statement(markdown_content):
    lines = markdown_content.split("\n")
    transactions = []
    current_date = None

    # Regex para linhas de transação com data — agora aceita linhas com ou sem '|'
    transaction_pattern_bb = re.compile(
        r'^\s*\|?\s*(\d{2}/\d{2}/\d{4})\s*\|?.*?\|?\s*(.*?)\s*\|?.*?\|?\s*([\d\.,]+)\s*([CD])'
    )

    # Regex para linhas de transação sem data explícita — também aceita sem '|'
    transaction_pattern_bb_no_date = re.compile(
        r'^\s*\|?.*?\|?\s*(.*?)\s*\|?.*?\|?\s*([\d\.,]+)\s*([CD])'
    )

    for line in lines:
        match_bb = transaction_pattern_bb.search(line)
        if match_bb:
            date_str = match_bb.group(1)
            current_date = pd.to_datetime(date_str, format='%d/%m/%Y')
            description = match_bb.group(2).strip()
            value_str = match_bb.group(3).replace('.', '').replace(',', '.')
            value_type = match_bb.group(4)
            value = float(value_str)
            if value_type == 'D':
                value *= -1
            transactions.append({'Data': current_date, 'Histórico': description, 'Valor': value})
        else:
            # Tenta encontrar transações sem data explícita na linha, usando a última data conhecida
            match_bb_no_date = transaction_pattern_bb_no_date.search(line)
            if match_bb_no_date and current_date:
                description = match_bb_no_date.group(1).strip()
                value_str = match_bb_no_date.group(2).replace('.', '').replace(',', '.')
                value_type = match_bb_no_date.group(3)
                value = float(value_str)
                if value_type == 'D':
                    value *= -1
                transactions.append({'Data': current_date, 'Histórico': description, 'Valor': value})

    df = pd.DataFrame(transactions)
    return df


