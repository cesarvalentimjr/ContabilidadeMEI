import pandas as pd
import re

def extract_bb_statement(markdown_content):
    """
    Extrai transações do Banco do Brasil a partir do markdown gerado pelo Docling.
    Agora suporta linhas sem delimitadores '|' e com saldo final opcional.
    """
    lines = markdown_content.split("\n")
    transactions = []

    # Novo padrão flexível para BB
    transaction_pattern_bb = re.compile(
        r'(\d{2}/\d{2}/\d{4})'                       # Data
        r'\s+(?:\d+\s+){0,3}'                        # Campos numéricos opcionais (agência, lote etc.)
        r'([A-ZÁ-Úa-zá-ú0-9\-\s\.\,\/]+?)'           # Histórico
        r'\s+([\d\.]+,\d{2})\s*([CD])'               # Valor + C/D
        r'(?:\s+[\d\.]+,\d{2}\s*[CD])?'              # Saldo opcional
    )

    for line in lines:
        match = transaction_pattern_bb.search(line)
        if match:
            date_str = match.group(1)
            description = match.group(2).strip()
            value_str = match.group(3).replace('.', '').replace(',', '.')
            value_type = match.group(4)

            try:
                date = pd.to_datetime(date_str, format='%d/%m/%Y')
                value = float(value_str)
                if value_type.upper() == 'D':
                    value *= -1
                transactions.append({'Data': date, 'Histórico': description, 'Valor': value})
            except Exception:
                continue

    return pd.DataFrame(transactions)
