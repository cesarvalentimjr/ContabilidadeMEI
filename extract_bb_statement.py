import pandas as pd
import re

def extract_bb_statement(markdown_content):
    lines = markdown_content.split("\n")
    transactions = []
    current_date = None

    # Regex para linhas de tabela que começam com data
    # Grupo 1: Data (DD/MM/YYYY)
    # Grupo 2: Histórico/Descrição
    # Grupo 3: Valor (com vírgula como separador decimal)
    # Grupo 4: Tipo (C ou D)
    transaction_pattern_bb = re.compile(r'\|\s*(\d{2}/\d{2}/\d{4})\s*\|.*?\|\s*(.*?)\s*\|.*?\|\s*([\d\.,]+)\s*([CD])\s*\|')

    # Regex para o caso onde a data não está na primeira coluna, mas o histórico e valor estão
    # e a data é inferida da linha anterior. Isso é mais comum em linhas que o Docling não formatou como tabela.
    # Para o BB, o formato de tabela parece ser mais consistente, mas vamos manter a flexibilidade.
    # Esta regex tenta capturar histórico e valor em linhas que não começam com data, mas estão dentro de uma tabela.
    transaction_pattern_bb_no_date = re.compile(r'\|.*?\|\s*(.*?)\s*\|.*?\|\s*([\d\.,]+)\s*([CD])\s*\|')

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

def extract_caixa_statement(markdown_content):
    lines = markdown_content.split("\n")
    transactions = []
    current_date = None

    # Regex para linhas de tabela que começam com data
    # | Data Mov. | Nr. Doc. | Histórico | Valor | Saldo |
    transaction_pattern_caixa_table = re.compile(r'\|\s*(\d{2}/\d{2}/\d{4})\s*\|.*?\|\s*(.*?)\s*\|\s*([\d\.,]+)\s*([CD])\s*\|')

    # Padrão para encontrar uma transação em texto corrido: (Histórico) (Valor) (Tipo) (Opcional: Saldo)
    # A regex é mais robusta para capturar o histórico de forma mais abrangente.
    # Ela busca por um padrão de valor e tipo, e o que vem antes disso é considerado o histórico.
    # O (?:\s+[\d\.,]+\s*[CD])? no final é para ignorar o saldo se ele estiver presente após a transação.
    # A descrição pode conter números e caracteres especiais, mas não deve ser um valor ou tipo.
    # O valor é sempre um número com vírgula/ponto e C/D.
    # A regex foi ajustada para ser mais flexível no histórico e garantir que o valor e o tipo sejam capturados corretamente.
    # Novo padrão para transações em texto corrido, que pode ter um número de documento opcional antes do histórico.
    # Exemplo: 01/06/2022 000341 CRED TED 5.600,00 C 8.468,58 D
    # O padrão para transações em texto corrido deve ser capaz de capturar múltiplas transações na mesma linha.
    # Vamos procurar por um padrão de (Histórico) (Valor) (Tipo) e iterar sobre a linha.
    # O histórico pode ser qualquer coisa que não seja um valor ou tipo de transação.
    # A regex para um item de transação: (opcional num doc) (histórico) (valor) (tipo) (opcional saldo)
    transaction_item_pattern_caixa_text = re.compile(r'(\d{6}\s+)?(.+?)\s+([\d\.,]+)\s*([CD])(?:\s+[\d\.,]+\s*[CD])?')

    for line in lines:
        # Tenta extrair da tabela primeiro
        match_table = transaction_pattern_caixa_table.search(line)
        if match_table:
            date_str = match_table.group(1)
            current_date = pd.to_datetime(date_str, format='%d/%m/%Y')
            description = match_table.group(2).strip()
            value_str = match_table.group(3).replace('.', '').replace(',', '.')
            value_type = match_table.group(4)
            value = float(value_str)
            if value_type == 'D':
                value *= -1
            transactions.append({'Data': current_date, 'Histórico': description, 'Valor': value})
        else:
            # Se não for uma linha de tabela, tenta encontrar a data no início da linha
            date_match = re.match(r'^(\d{2}/\d{2}/\d{4})', line)
            line_content = line
            if date_match:
                current_date = pd.to_datetime(date_match.group(1), format='%d/%m/%Y')
                # Remove a data do início da linha para processar o resto como transações
                line_content = line[len(date_match.group(0)):].strip()

            # Procura por padrões de transação dentro da linha (pode haver múltiplos)
            # Certifica-se de que current_date está definida antes de adicionar transações
            if current_date:
                temp_line = line_content
                # Itera para encontrar todas as transações na linha
                while True:
                    match_item = transaction_item_pattern_caixa_text.search(temp_line)
                    if match_item:
                        # O grupo 1 é o número do documento opcional, o grupo 2 é o histórico
                        description = match_item.group(2).strip()
                        value_str = match_item.group(3).replace('.', '').replace(',', '.')
                        value_type = match_item.group(4)
                        value = float(value_str)
                        if value_type == 'D':
                            value *= -1
                        transactions.append({'Data': current_date, 'Histórico': description, 'Valor': value})
                        # Remove a transação encontrada da linha para procurar a próxima
                        temp_line = temp_line[match_item.end(0):].strip()
                    else:
                        break

    df = pd.DataFrame(transactions)
    return df


# Funções para os novos extratos (MLGITA e MLGSAN)
def extract_mlgita_statement(markdown_content):
    lines = markdown_content.split("\n")
    transactions = []
    current_date = None

    # Mapeamento de meses abreviados em português para números
    month_mapping = {
        'jan': '01', 'fev': '02', 'mar': '03', 'abr': '04',
        'mai': '05', 'jun': '06', 'jul': '07', 'ago': '08',
        'set': '09', 'out': '10', 'nov': '11', 'dez': '12'
    }

    # Regex para linhas de transação. O formato parece ser similar ao BB, mas com algumas variações.
    # Exemplo: | 01 / dez | MOVTIT COB DISP 02/12S | | 29.834,16 | |
    # Para MLGITA, o valor já vem com o sinal negativo para débitos.
    # | data | lançamentos | ag/origem | valor (R$) | saldo (R$) |
    transaction_pattern_mlgita = re.compile(r'\|\s*(\d{2}\s*/\s*(\w{3}))\s*\|\s*(.*?)\s*\|.*?\|\s*([\d\.,-]+)\s*\|')

    for line in lines:
        match = transaction_pattern_mlgita.search(line)
        if match:
            day = match.group(1).split('/')[0].strip()
            month_abbr = match.group(2).strip().lower()
            month_num = month_mapping.get(month_abbr, '01') # Default para '01' se não encontrar
            # O ano é fixo para 2024, conforme o nome do arquivo MLGITA122024.pdf
            date_str = f"{day}/{month_num}/2024"
            current_date = pd.to_datetime(date_str, format='%d/%m/%Y')
            description = match.group(3).strip()
            value_str = match.group(4).replace('.', '').replace(',', '.')
            value = float(value_str)
            transactions.append({'Data': current_date, 'Histórico': description, 'Valor': value})

    df = pd.DataFrame(transactions)
    return df

def extract_mlgsan_statement(markdown_content):
    lines = markdown_content.split("\n")
    transactions = []
    current_date = None

    # Regex para linhas de transação. Assumindo formato similar ao BB/MLGITA.
    # O extrato MLGSAN tem um formato de tabela com 5 colunas: Data, Histórico, Documento, Valor, Saldo.
    # A data está na primeira coluna, o histórico na segunda, o valor na quarta.
    # Exemplo: | 02/12/2024 | TARIFA MENSALIDADE PACOTE SERVICOS NOVEMBRO / 2024 | 000000 | -280,00 | |
    # Exemplo: | 02/12/2024 | TED RECEBIDA 03642342000101 | 000000 | 28.239,25 | |
    # O valor pode ser negativo ou positivo, e o tipo (C/D) não está explicitamente na coluna de valor.
    # Precisamos inferir o tipo pelo sinal do valor.
    transaction_pattern_mlgsan = re.compile(r'\|\s*(\d{2}/\d{2}/\d{4})\s*\|\s*(.*?)\s*\|.*?\|\s*([\d\.,-]+)\s*\|')

    for line in lines:
        match = transaction_pattern_mlgsan.search(line)
        if match:
            date_str = match.group(1)
            current_date = pd.to_datetime(date_str, format='%d/%m/%Y')
            description = match.group(2).strip()
            value_str = match.group(3).replace('.', '').replace(',', '.')
            value = float(value_str)
            transactions.append({'Data': current_date, 'Histórico': description, 'Valor': value})

    df = pd.DataFrame(transactions)
    return df


