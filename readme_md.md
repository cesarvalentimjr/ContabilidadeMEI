# 🏦 Extrator de Extratos Bancários

Uma aplicação Streamlit inteligente para extração automática de dados de extratos bancários em PDF, com suporte a múltiplos bancos brasileiros.

## 🚀 Funcionalidades

- **Extração Inteligente**: Algoritmos avançados de reconhecimento de padrões para diferentes formatos de extratos
- **Múltiplos Bancos**: Suporte para Banco do Brasil, Itaú, Bradesco, Santander, Caixa, Nubank, Inter, C6 Bank, BTG Pactual e outros
- **Processamento em Lote**: Upload e processamento de múltiplos PDFs simultaneamente
- **Categorização Automática**: Classificação inteligente de transações por categoria (Alimentação, Transporte, Casa, etc.)
- **Análises Visuais**: Gráficos interativos de fluxo de caixa e distribuição de gastos
- **Filtros Avançados**: Filtros por tipo, categoria e período
- **Export Flexível**: Download dos dados em CSV com opções de filtro

## 📋 Pré-requisitos

- Python 3.8 ou superior
- Conexão com internet para instalar dependências

## 🛠️ Instalação

### Instalação Local

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/extrator-extratos-bancarios.git
cd extrator-extratos-bancarios
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Execute a aplicação:
```bash
streamlit run app.py
```

4. Acesse no seu navegador: `http://localhost:8501`

### Deploy no Streamlit Cloud

1. Faça fork deste repositório
2. Acesse [share.streamlit.io](https://share.streamlit.io)
3. Conecte sua conta GitHub
4. Selecione o repositório e o arquivo `app.py`
5. Clique em "Deploy"

## 📖 Como Usar

1. **Upload**: Selecione um ou mais arquivos PDF de extratos bancários
2. **Processamento**: Clique em "Processar Extratos" e aguarde a análise
3. **Visualização**: Explore os dados extraídos, gráficos e estatísticas
4. **Filtros**: Use os filtros para analisar períodos ou categorias específicas
5. **Download**: Baixe os resultados em formato CSV

## 🏛️ Bancos Suportados

A aplicação foi testada e otimizada para extratos dos seguintes bancos:

- **Banco do Brasil**
- **Itaú Unibanco**
- **Bradesco**
- **Santander**
- **Caixa Econômica Federal**
- **Nubank**
- **Banco Inter**
- **C6 Bank**
- **BTG Pactual**
- **Original**
- **PagBank**
- **PicPay**
- **Stone**

> **Nota**: O sistema também pode funcionar com outros bancos, mas a precisão pode variar.

## 🔍 Tipos de Dados Extraídos

- **Data da transação**
- **Descrição detalhada**
- **Valor da transação**
- **Saldo (quando disponível)**
- **Tipo de transação** (PIX, TED, Saque, Compra, etc.)
- **Categoria** (Alimentação, Transporte, Casa, Saúde, etc.)
- **Arquivo de origem**

## 📊 Recursos de Análise

- **Resumo Financeiro**: Totais de créditos, débitos e fluxo líquido
- **Fluxo de Caixa Mensal**: Gráfico de linha mostrando a evolução temporal
- **Gastos por Categoria**: Gráfico de barras com distribuição dos gastos
- **Filtros Dinâmicos**: Por tipo, categoria e período
- **Tabela Interativa**: Visualização completa dos dados com ordenação

## 🎯 Melhorias Implementadas

### Em relação ao código original:

1. **Interface Streamlit Completa**: Interface web intuitiva e responsiva
2. **Processamento em Lote**: Capacidade de processar múltiplos arquivos
3. **Algoritmo de Extração Aprimorado**: Melhor reconhecimento de padrões
4. **Suporte a Mais Formatos**: Reconhecimento de diversos formatos de data e valor
5. **Categorização Inteligente**: Sistema de categorização automática
6. **Visualizações Interativas**: Gráficos com Plotly
7. **Sistema de Filtros**: Filtros avançados para análise
8. **Export Flexível**: Download de dados filtrados ou completos
9. **Tratamento Robusto de Erros**: Melhor handling de exceções
10. **Logging e Feedback**: Sistema de progresso e status

## ⚙️ Configuração Avançada

### Adicionando Novos Bancos

Para adicionar suporte a um novo banco, crie uma nova classe herdando de `BankPatternMatcher`:

```python
class NovoBancoMatch
