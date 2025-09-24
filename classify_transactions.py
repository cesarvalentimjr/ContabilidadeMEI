
import pandas as pd

def classify_transaction(description, value):
    description = str(description).lower()
    category = "Outros"

    # Receitas
    if value > 0:
        if "salario" in description or "pagamento" in description or "cred ted" in description or "cred pix" in description or "resgate" in description or "deposito" in description or "rendimento" in description or "juros" in description or "movertit" in description or "red ted" in description or "credito" in description:
            category = "Receita"
        elif "transferencia" in description or "pix transf" in description:
            category = "Transferência Recebida"
        elif "aplicacao" in description or "rende facil" in description or "bb rende facil" in description:
            category = "Rendimentos/Investimentos"
    # Despesas
    else:
        if "aluguel" in description or "moradia" in description:
            category = "Moradia"
        elif "supermercado" in description or "alimentacao" in description or "restaurante" in description or "comida" in description or "mercado" in description:
            category = "Alimentação"
        elif "transporte" in description or "combustivel" in description or "uber" in description or "99pop" in description or "passagem" in description or "pedagio" in description or "fin veic" in description:
            category = "Transporte"
        elif "luz" in description or "agua" in description or "gas" in description or "internet" in description or "energia" in description:
            category = "Contas de Consumo"
        elif "saude" in description or "farmacia" in description or "medico" in description or "hospital" in description:
            category = "Saúde"
        elif "educacao" in description or "escola" in description or "faculdade" in description or "curso" in description:
            category = "Educação"
        elif "lazer" in description or "entretenimento" in description or "cinema" in description or "teatro" in description or "viagem" in description:
            category = "Lazer"
        elif "taxa" in description or "tarifa" in description or "juros" in description or "imposto" in description or "tributo" in description:
            category = "Taxas e Tarifas"
        elif "boleto pago" in description or "pagto" in description or "pagamento" in description:
            category = "Pagamento de Contas"
        elif "pix enviado" in description or "transferencia enviada" in description or "transferencia" in description:
            category = "Transferência Enviada"
        elif "aplicacao" in description:
            category = "Investimentos/Aplicações"
        elif "sispag" in description:
            category = "Pagamento de Salários/Fornecedores"
        elif "deb aut" in description or "debito automatico" in description:
            category = "Débito Automático"
        elif "saque" in description:
            category = "Saque"
        elif "saldo anterior" in description:
            category = "Saldo Inicial"

    return category

def add_category_column(df):
    df["Categoria"] = df.apply(lambda row: classify_transaction(row["Histórico"], row["Valor"]), axis=1)
    return df


# Exemplo de uso (para teste)
if __name__ == "__main__":
    # Criar um DataFrame de exemplo
    data = {
        "Data": pd.to_datetime(["2024-01-01", "2024-01-01", "2024-01-02", "2024-01-03", "2024-01-03", "2024-01-04"]),
        "Histórico": [
            "SALARIO MENSAL",
            "COMPRA SUPERMERCADO",
            "PAGAMENTO ALUGUEL",
            "PIX ENVIADO JOAO",
            "CRED TED MARIA",
            "TARIFA BANCARIA"
        ],
        "Valor": [5000.00, -150.00, -1200.00, -200.00, 300.00, -15.00]
    }
    df_test = pd.DataFrame(data)

    print("DataFrame Original:")
    print(df_test.to_markdown(index=False))

    df_classified = add_category_column(df_test)
    print("\nDataFrame Classificado:")
    print(df_classified.to_markdown(index=False))


