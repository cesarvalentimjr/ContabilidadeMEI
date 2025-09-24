
import pandas as pd

def generate_cash_flow_report(df_classified):
    # Agrupar por Categoria e somar os valores
    report = df_classified.groupby('Categoria')['Valor'].sum().reset_index()
    report.rename(columns={'Valor': 'Total'}, inplace=True)

    # Separar receitas e despesas
    receitas = report[report['Total'] > 0].sort_values(by='Total', ascending=False)
    despesas = report[report['Total'] <= 0].sort_values(by='Total')

    # Calcular o saldo total
    saldo_total = df_classified['Valor'].sum()

    return receitas, despesas, saldo_total

def generate_monthly_cash_flow(df_classified):
    df_classified['AnoMes'] = df_classified['Data'].dt.to_period('M')
    monthly_summary = df_classified.groupby(['AnoMes', 'Categoria'])['Valor'].sum().unstack(fill_value=0)
    monthly_summary['Total Mensal'] = monthly_summary.sum(axis=1)
    return monthly_summary


# Exemplo de uso (para teste)
if __name__ == "__main__":
    # Criar um DataFrame de exemplo (classificado)
    data = {
        "Data": pd.to_datetime([
            "2024-01-01", "2024-01-01", "2024-01-02", "2024-01-03", "2024-01-03", "2024-01-04",
            "2024-01-05", "2024-02-01", "2024-02-02", "2024-02-03"
        ]),
        "Histórico": [
            "SALARIO MENSAL",
            "COMPRA SUPERMERCADO",
            "PAGAMENTO ALUGUEL",
            "PIX ENVIADO JOAO",
            "CRED TED MARIA",
            "TARIFA BANCARIA",
            "CONTA DE LUZ",
            "SALARIO FEVEREIRO",
            "ALUGUEL FEVEREIRO",
            "COMPRA PADARIA"
        ],
        "Valor": [
            5000.00, -150.00, -1200.00, -200.00, 300.00, -15.00,
            -100.00, 5500.00, -1200.00, -50.00
        ]
    }
    df_test = pd.DataFrame(data)

    # Adicionar uma coluna de categoria (simulando a saída da fase anterior)
    from classify_transactions import add_category_column
    df_test_classified = add_category_column(df_test)

    print("\n--- Relatório de Fluxo de Caixa Geral ---")
    receitas, despesas, saldo_total = generate_cash_flow_report(df_test_classified)
    print("\nReceitas:")
    print(receitas.to_markdown(index=False))
    print("\nDespesas:")
    print(despesas.to_markdown(index=False))
    print(f"\nSaldo Total: {saldo_total:.2f}")

    print("\n--- Relatório de Fluxo de Caixa Mensal ---")
    monthly_report = generate_monthly_cash_flow(df_test_classified)
    print(monthly_report.to_markdown())

