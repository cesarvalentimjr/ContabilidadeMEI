import streamlit as st
import pandas as pd
import json
import io
from PIL import Image
from pydantic import BaseModel, Field
from typing import List, Optional
from google import genai
from google.genai import types
import calendar
from pypdf import PdfReader
import pdfplumber


# --- FUNÇÃO DE FORMATAÇÃO BRL (NOVO) ---
def formatar_brl(valor: float) -> str:
    """
    Formata um valor float para a moeda Real Brasileiro (R$ xx.xxx,xx).
    Esta função usa uma abordagem manual para garantir a portabilidade do separador de milhares (ponto) 
    e separador decimal (vírgula).
    """
    # Arredonda o valor e usa formatação US (vírgula para milhar, ponto para decimal)
    # Ex: 12345.67 -> '12,345.67'
    valor_us = f"{valor:,.2f}"
    
    # 1. Troca o separador de milhares US (vírgula) por um temporário
    valor_brl = valor_us.replace(",", "TEMP_SEP")
    
    # 2. Troca o separador decimal US (ponto) por vírgula BR
    valor_brl = valor_brl.replace(".", ",")
    
    # 3. Troca o separador temporário por ponto BR (milhares)
    valor_brl = valor_brl.replace("TEMP_SEP", ".")
    
    return "R$ " + valor_brl
# --- FIM FUNÇÃO DE FORMATAÇÃO BRL ---


# --- 1. CONFIGURAÇÃO DE SEGURANÇA E TEMA ---

# Cores baseadas na logo Hedgewise
PRIMARY_COLOR = "#0A2342"   # Azul Marinho Escuro (para botões, links)
SECONDARY_COLOR = "#000000" # Preto (para títulos e texto principal)
BACKGROUND_COLOR = "#F0F2F6" # Cinza Claro (fundo sutil)
ACCENT_COLOR = "#007BFF" # Azul de Destaque para Fluxo Positivo
NEGATIVE_COLOR = "#DC3545" # Vermelho para Fluxo Negativo
FINANCING_COLOR = "#FFC107" # Amarelo/Dourado para Financiamento

# Nome do arquivo da logo no formato PNG
LOGO_FILENAME = "logo_hedgewise.png" 

st.set_page_config(
    page_title="Hedgewise | Análise Financeira Inteligente",
    page_icon="📈",
    layout="wide"
)

# Adiciona CSS customizado para o tema
st.markdown(
    f"""
    <style>
        /* Estilo para o Botão Principal */
        .stButton>button {{
            background-color: {PRIMARY_COLOR};
            color: white;
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: bold;
            border: none;
            transition: background-color 0.3s;
        }}
        .stButton>button:hover {{
            background-color: #1C3757; 
            color: white;
        }}
        /* Fundo da Aplicação */
        .stApp {{
            background-color: {BACKGROUND_COLOR};
        }}
        /* Header Principal */
        .main-header {{
            color: {SECONDARY_COLOR};
            font-size: 2.5em;
            padding-bottom: 10px;
        }}
        /* Container dos Widgets/KPIs - Estilo de Card Profissional */
        .kpi-container {{
            background-color: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 6px 15px 0 rgba(0, 0, 0, 0.08); /* Sombra mais suave */
            margin-bottom: 20px;
            height: 100%; /* Garante altura uniforme */
        }}
        /* Estilos de Métricas */
        [data-testid="stMetricLabel"] label {{
            font-weight: 600 !important;
            color: #6c757d; /* Texto cinza suave para a label */
        }}
        [data-testid="stMetricValue"] {{
            font-size: 1.8em !important;
            color: {SECONDARY_COLOR};
        }}
        /* Estilo para Abas (Tabs) */
        button[data-baseweb="tab"] {{
            color: #6c757d;
            border-bottom: 2px solid transparent;
            font-weight: 600;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            color: {PRIMARY_COLOR};
            border-bottom: 3px solid {PRIMARY_COLOR} !important;
        }}
        /* Títulos */
        h2 {{
            color: {PRIMARY_COLOR};
            border-left: 5px solid {PRIMARY_COLOR};
            padding-left: 10px;
            margin-top: 20px;
            margin-bottom: 20px;
        }}
    </style>
    """,
    unsafe_allow_html=True
)

# Inicializa o estado da sessão para armazenar o DataFrame
if 'df_transacoes_editado' not in st.session_state:
    st.session_state['df_transacoes_editado'] = pd.DataFrame()
if 'relatorio_consolidado' not in st.session_state:
    st.session_state['relatorio_consolidado'] = "Aguardando análise de dados..."
if 'contexto_adicional' not in st.session_state:
    st.session_state['contexto_adicional'] = ""

# Inicializa o cliente Gemini
try:
    # Tenta carregar a chave de API dos secrets do Streamlit Cloud
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
except (KeyError, AttributeError):
    st.error("ERRO: Chave 'GEMINI_API_KEY' não encontrada nos secrets do Streamlit. Por favor, configure-a para rodar a aplicação.")
    st.stop()


# --- 2. DEFINIÇÃO DO SCHEMA PYDANTIC (Estrutura de Saída) ---

class Transacao(BaseModel):
    """Representa uma única transação no extrato bancário."""
    data: str = Field(
        description="A data da transação no formato 'DD/MM/AAAA' ou 'AAAA-MM-DD'."
    )
    descricao: str = Field(
        description="Descrição detalhada da transação, como o nome do estabelecimento ou tipo de serviço."
    )
    valor: float = Field(
        description="O valor numérico da transação. Sempre positivo. Ex: 150.75"
    )
    tipo_movimentacao: str = Field(
        description="Classificação da movimentação: 'DEBITO' ou 'CREDITO'."
    )
    categoria_sugerida: str = Field(
        description="Sugestão de categoria mais relevante para esta transação (Ex: 'Alimentação', 'Transporte', 'Salário', 'Investimento', 'Serviços')."
    )
    categoria_dcf: str = Field( 
        description="Classificação da transação para o Demonstrativo de Fluxo de Caixa (DCF): 'OPERACIONAL', 'INVESTIMENTO' ou 'FINANCIAMENTO'."
    )
    entidade: str = Field(
        description="Classificação binária para identificar a origem/destino da movimentação: 'EMPRESARIAL' (relacionada ao negócio) ou 'PESSOAL' (retiradas dos sócios ou gastos pessoais detectados)."
    )

class ExtratoBancarioCompleto(BaseModel):
    """Contém a lista de transações e o relatório de análise."""
    transacoes: List[Transacao] = Field(
        description="Uma lista de objetos 'Transacao' extraídos do documento."
    )
    saldo_final: float = Field(
        description="O saldo final da conta no extrato. Use zero se não for encontrado."
    )
    relatorio_analise: str = Field(
        description="Confirmação de extração dos dados deste extrato. Use 'Extração de dados concluída com sucesso.'"
    )


# --- 3. FUNÇÃO DE CHAMADA DA API PARA EXTRAÇÃO ---

@st.cache_data(show_spinner=False, hash_funcs={genai.Client: lambda _: None})
def extract_text_and_tables_from_pdf(pdf_bytes: bytes) -> str:
    """Extrai texto e tenta extrair tabelas de um PDF em bytes usando pdfplumber."""
    full_text = []
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                # Extrair texto da página
                page_text = page.extract_text(x_tolerance=2) or ""
                full_text.append(page_text)

                # Extrair tabelas da página
                tables = page.extract_tables()
                for table in tables:
                    table_str = "\n".join(["\t".join(row) for row in table if row])
                    if table_str:
                        full_text.append("\n--- TABELA INÍCIO ---\n" + table_str + "\n--- TABELA FIM ---\n")

        return "\n".join(full_text)
    except Exception as e:
        st.error(f"Erro ao extrair texto e tabelas do PDF: {e}")
        return ""

@st.cache_data(show_spinner=False, hash_funcs={genai.Client: lambda _: None})
def analisar_extrato(pdf_bytes: bytes, filename: str, client: genai.Client) -> dict:
    """Chama a Gemini API para extrair dados estruturados e classificar DCF e Entidade."""
    
    extracted_text = extract_text_and_tables_from_pdf(pdf_bytes)
    if not extracted_text:
        return {
            'transacoes': [],
            'saldo_final': 0.0,
            'relatorio_analise': f"**Falha na Extração:** Não foi possível extrair texto do arquivo {filename}."
        }
    prompt_analise = (
        f"Você é um especialista em extração e classificação de dados financeiros. "        f"Seu trabalho é extrair todas as transações deste extrato bancário fornecido como TEXTO do arquivo '{filename}' e "        "classificar cada transação rigorosamente em uma 'categoria_dcf' ('OPERACIONAL', 'INVESTIMENTO' ou 'FINANCIAMENTO') E "
        "em uma 'entidade' ('EMPRESARIAL' ou 'PESSOAL'). "
        "Use o contexto de que a maioria das movimentações devem ser EMPRESARIAIS, mas qualquer retirada para sócios, pagamento de contas pessoais ou compras não relacionadas ao CNPJ deve ser classificada como PESSOAL. "
        "Não gere relatórios. Preencha apenas a estrutura JSON rigorosamente. "
        "Use sempre o valor positivo para 'valor' e classifique estritamente como 'DEBITO' ou 'CREDITO'."
    )
    
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=ExtratoBancarioCompleto,
        temperature=0.2 # Baixa temperatura para foco na extração
    )

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash', # ALTERADO DE gemini-2.5-pro PARA gemini-2.5-flash
            contents=[extracted_text, prompt_analise],
            config=config,
        )
        
        response_json = json.loads(response.text)
        dados_pydantic = ExtratoBancarioCompleto(**response_json)
        
        return dados_pydantic.model_dump()
    
    except Exception as e:
        error_message = str(e)
        
        # TRATAMENTO ESPECÍFICO PARA ERRO DE SOBRECARGA DA API (503 UNAVAILABLE)
        if "503 UNAVAILABLE" in error_message or "model is overloaded" in error_message:
            st.error(f"⚠️ ERRO DE CAPACIDADE DA API: O modelo Gemini está sobrecarregado (503 UNAVAILABLE) ao processar {filename}.")
            st.info("Este é um erro temporário do servidor da API. Por favor, tente novamente em alguns minutos. O problema não está no seu código ou no seu PDF.")
        else:
            # Erro genérico (API Key errada, PDF ilegível, etc.)
            print(f"Erro ao chamar a Gemini API para {filename}: {error_message}")

        return {
            'transacoes': [], 
            'saldo_final': 0.0, 
            'relatorio_analise': f"**Falha na Extração:** Ocorreu um erro ao processar o arquivo {filename}. Motivo: {error_message}"
        }

# --- 3.1. FUNÇÃO DE GERAÇÃO DE RELATÓRIO CONSOLIDADO ---

def gerar_relatorio_consolidado(df_transacoes: pd.DataFrame, contexto_adicional: str, client: genai.Client) -> str:
    """Gera o relatório de análise consolidado, agora mais conciso e focado no split Entidade/DCF. 
        Aplica filtro de colunas e formatação de data para reduzir o payload de JSON."""
    
    # CRITICAL FIX: Criar uma cópia do DF e formatar/filtrar colunas para reduzir o tamanho do JSON payload
    df_temp = df_transacoes.copy()
    
    # 1. Formatar a data para uma string simples (YYYY-MM-DD) antes de serializar
    df_temp['data'] = df_temp['data'].dt.strftime('%Y-%m-%d')
    
    # 2. Selecionar apenas as colunas essenciais para a análise do LLM
    df_analise = df_temp[['data', 'descricao', 'valor', 'tipo_movimentacao', 
                          'categoria_sugerida', 'categoria_dcf', 'entidade']]
    
    # Gerar o JSON a partir do DF filtrado (muito menor)
    transacoes_json = df_analise.to_json(orient='records', date_format='iso', indent=2)
    
    # Adiciona o contexto do usuário ao prompt
    contexto_prompt = ""
    if contexto_adicional:
        contexto_prompt = f"Considere também o seguinte contexto adicional fornecido pelo usuário: {contexto_adicional}\n\n"

    prompt_consolidado = (
        f"Você é um analista financeiro experiente. Analise o seguinte conjunto de transações bancárias em formato JSON: "
        f"\n\n```json\n{transacoes_json}\n```\n\n"
        f"{contexto_prompt}"
        "Com base nessas transações, forneça um relatório conciso e objetivo, com foco na classificação de 'entidade' (EMPRESARIAL ou PESSOAL) e 'categoria_dcf' (OPERACIONAL, INVESTIMENTO, FINANCIAMENTO). "
        "Destaque os principais pontos de entrada e saída de recursos, e aponte quaisquer anomalias ou observações relevantes sobre o fluxo de caixa da entidade. "
        "Não inclua o saldo final, pois ele já é uma métrica separada. O relatório deve ser em português do Brasil e ter no máximo 200 palavras."
    )

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash', # ALTERADO DE gemini-2.5-pro PARA gemini-2.5-flash
            contents=[prompt_consolidado],
            config=types.GenerateContentConfig(
                temperature=0.7 # Temperatura mais alta para criatividade na análise
            )
        )
        return response.text
    except Exception as e:
        st.error(f"Erro ao gerar relatório consolidado: {e}")
        return f"Falha ao gerar relatório consolidado. Motivo: {e}"

# --- 4. FUNÇÕES DE PROCESSAMENTO E VISUALIZAÇÃO ---

def processar_df_transacoes(df: pd.DataFrame) -> pd.DataFrame:
    """Processa o DataFrame para garantir tipos corretos e adicionar colunas calculadas."""
    df['data'] = pd.to_datetime(df['data'], errors='coerce', dayfirst=True)
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
    
    # Calcula o fluxo de caixa (valor positivo para crédito, negativo para débito)
    df['fluxo_caixa'] = df.apply(
        lambda row: row['valor'] if row['tipo_movimentacao'] == 'CREDITO' else -row['valor'],
        axis=1
    )
    return df

def exibir_kpis(df_transacoes: pd.DataFrame):
    """Exibe os principais KPIs financeiros em cards estilizados."""
    st.markdown("<h2 style='text-align: center; color: #0A2342;'>Resumo Financeiro</h2>", unsafe_allow_html=True)

    total_credito = df_transacoes[df_transacoes['tipo_movimentacao'] == 'CREDITO']['valor'].sum()
    total_debito = df_transacoes[df_transacoes['tipo_movimentacao'] == 'DEBITO']['valor'].sum()
    saldo_liquido = total_credito - total_debito

    col1, col2, col3 = st.columns(3)

    with col1:
        with st.container(border=True):
            st.markdown(f"<div class='kpi-container'>"
                        f"<p style='font-size: 1.2em; color: #6c757d;'>Total de Créditos</p>"
                        f"<p style='font-size: 2em; font-weight: bold; color: {ACCENT_COLOR};'>{formatar_brl(total_credito)}</p>"
                        f"</div>", unsafe_allow_html=True)
    with col2:
        with st.container(border=True):
            st.markdown(f"<div class='kpi-container'>"
                        f"<p style='font-size: 1.2em; color: #6c757d;'>Total de Débitos</p>"
                        f"<p style='font-size: 2em; font-weight: bold; color: {NEGATIVE_COLOR};'>{formatar_brl(total_debito)}</p>"
                        f"</div>", unsafe_allow_html=True)
    with col3:
        with st.container(border=True):
            color_saldo = ACCENT_COLOR if saldo_liquido >= 0 else NEGATIVE_COLOR
            st.markdown(f"<div class='kpi-container'>"
                        f"<p style='font-size: 1.2em; color: #6c757d;'>Saldo Líquido</p>"
                        f"<p style='font-size: 2em; font-weight: bold; color: {color_saldo};'>{formatar_brl(saldo_liquido)}</p>"
                        f"</div>", unsafe_allow_html=True)

def exibir_analise_dcf_entidade(df_transacoes: pd.DataFrame):
    """Exibe a análise de fluxo de caixa por DCF e Entidade."""
    st.markdown("<h2 style='text-align: center; color: #0A2342;'>Análise de Fluxo de Caixa por DCF e Entidade</h2>", unsafe_allow_html=True)

    # Agrupamento por Categoria DCF
    dcf_summary = df_transacoes.groupby('categoria_dcf')['fluxo_caixa'].sum().reset_index()
    dcf_summary['fluxo_caixa_abs'] = dcf_summary['fluxo_caixa'].abs() # Para ordenação
    dcf_summary = dcf_summary.sort_values(by='fluxo_caixa_abs', ascending=False)
    dcf_summary['fluxo_caixa_formatado'] = dcf_summary['fluxo_caixa'].apply(formatar_brl)

    # Agrupamento por Entidade
    entidade_summary = df_transacoes.groupby('entidade')['fluxo_caixa'].sum().reset_index()
    entidade_summary['fluxo_caixa_abs'] = entidade_summary['fluxo_caixa'].abs() # Para ordenação
    entidade_summary = entidade_summary.sort_values(by='fluxo_caixa_abs', ascending=False)
    entidade_summary['fluxo_caixa_formatado'] = entidade_summary['fluxo_caixa'].apply(formatar_brl)

    col_dcf, col_entidade = st.columns(2)

    with col_dcf:
        st.subheader("Por Categoria DCF")
        for _, row in dcf_summary.iterrows():
            color = ACCENT_COLOR if row['fluxo_caixa'] >= 0 else NEGATIVE_COLOR
            st.markdown(f"<p style='font-size: 1.1em; font-weight: bold;'>{row['categoria_dcf']}: <span style='color: {color};'>{row['fluxo_caixa_formatado']}</span></p>", unsafe_allow_html=True)

    with col_entidade:
        st.subheader("Por Entidade")
        for _, row in entidade_summary.iterrows():
            color = ACCENT_COLOR if row['fluxo_caixa'] >= 0 else NEGATIVE_COLOR
            st.markdown(f"<p style='font-size: 1.1em; font-weight: bold;'>{row['entidade']}: <span style='color: {color};'>{row['fluxo_caixa_formatado']}</span></p>", unsafe_allow_html=True)

def exibir_transacoes_detalhadas(df_transacoes: pd.DataFrame):
    """Exibe a tabela de transações detalhadas com opções de filtro e edição."""
    st.markdown("<h2 style='text-align: center; color: #0A2342;'>Transações Detalhadas</h2>", unsafe_allow_html=True)

    # Filtros
    col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
    with col_filtro1:
        categorias_dcf_unicas = ['Todas'] + list(df_transacoes['categoria_dcf'].unique())
        filtro_dcf = st.selectbox("Filtrar por DCF", categorias_dcf_unicas)
    with col_filtro2:
        entidades_unicas = ['Todas'] + list(df_transacoes['entidade'].unique())
        filtro_entidade = st.selectbox("Filtrar por Entidade", entidades_unicas)
    with col_filtro3:
        tipos_mov_unicos = ['Todas'] + list(df_transacoes['tipo_movimentacao'].unique())
        filtro_mov = st.selectbox("Filtrar por Movimentação", tipos_mov_unicos)

    df_filtrado = df_transacoes.copy()
    if filtro_dcf != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['categoria_dcf'] == filtro_dcf]
    if filtro_entidade != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['entidade'] == filtro_entidade]
    if filtro_mov != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['tipo_movimentacao'] == filtro_mov]

    # Exibir o DataFrame editável
    st.dataframe(
        df_filtrado.style.apply(lambda x: ['background-color: #e6ffe6' if x['tipo_movimentacao'] == 'CREDITO' else 'background-color: #ffe6e6' for i in x], axis=1),
        use_container_width=True,
        hide_index=True,
        column_config={
            "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
            "descricao": "Descrição",
            "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
            "tipo_movimentacao": "Tipo",
            "categoria_sugerida": "Categoria Sugerida",
            "categoria_dcf": "DCF",
            "entidade": "Entidade",
            "fluxo_caixa": st.column_config.NumberColumn("Fluxo de Caixa", format="R$ %.2f"),
        }
    )

# --- 5. INTERFACE DO STREAMLIT ---
st.image(LOGO_FILENAME, width=200)
st.markdown("<h1 class='main-header'>Análise de Extratos Bancários com IA</h1>", unsafe_allow_html=True)
st.markdown("### Faça o upload de seus extratos em PDF para uma análise financeira inteligente.")

uploaded_files = st.file_uploader("Arraste e solte seus extratos bancários em PDF aqui ou clique para selecionar", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    if st.button("Processar Extratos"): # Botão para iniciar o processamento
        df_transacoes_acumulado = pd.DataFrame()
        relatorios_analise = []

        for uploaded_file in uploaded_files:
            pdf_bytes = uploaded_file.getvalue()
            filename = uploaded_file.name

            with st.spinner(f"Analisando {filename}..."):
                dados_extraidos = analisar_extrato(pdf_bytes, filename, client)
                
                if dados_extraidos and dados_extraidos['transacoes']:
                    df_temp = pd.DataFrame(dados_extraidos['transacoes'])
                    df_temp = processar_df_transacoes(df_temp)
                    df_transacoes_acumulado = pd.concat([df_transacoes_acumulado, df_temp], ignore_index=True)
                    relatorios_analise.append(dados_extraidos['relatorio_analise'])
                else:
                    st.warning(f"Nenhuma transação extraída ou erro no arquivo {filename}. Mensagem: {dados_extraidos.get('relatorio_analise', 'Erro desconhecido')}")
                    relatorios_analise.append(f"Falha na extração de {filename}.")

        if not df_transacoes_acumulado.empty:
            st.session_state['df_transacoes_editado'] = df_transacoes_acumulado
            st.session_state['relatorios_analise_individuais'] = relatorios_analise
            st.session_state['relatorio_consolidado'] = gerar_relatorio_consolidado(df_transacoes_acumulado, st.session_state['contexto_adicional'], client)
            st.success("Processamento concluído com sucesso!")
        else:
            st.error("Nenhuma transação pôde ser processada de todos os arquivos.")

if not st.session_state['df_transacoes_editado'].empty:
    st.markdown("<h2 style='text-align: center; color: #0A2342;'>Resultados da Análise</h2>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Resumo e KPIs", "Transações Detalhadas", "Relatório IA"])

    with tab1:
        st.markdown("<h3 style='color: #0A2342;'>Visão Geral</h3>", unsafe_allow_html=True)
        exibir_kpis(st.session_state['df_transacoes_editado'])
        exibir_analise_dcf_entidade(st.session_state['df_transacoes_editado'])

    with tab2:
        exibir_transacoes_detalhadas(st.session_state['df_transacoes_editado'])

    with tab3:
        st.markdown("<h3 style='color: #0A2342;'>Relatório de Análise da IA</h3>", unsafe_allow_html=True)
        st.write(st.session_state['relatorio_consolidado'])
        st.markdown("--- \n**Relatórios Individuais de Extração:**")
        for rel in st.session_state['relatorios_analise_individuais']:
            st.info(rel)

    st.markdown("--- \n### Contexto Adicional para Análise da IA")
    st.session_state['contexto_adicional'] = st.text_area(
        "Adicione informações relevantes para refinar a análise da IA (ex: 'Esta conta é para despesas da empresa X', 'Ignorar transações de investimento').",
        value=st.session_state['contexto_adicional'],
        height=100
    )
    if st.button("Atualizar Relatório da IA com Contexto Adicional"):
        if not st.session_state['df_transacoes_editado'].empty:
            st.session_state['relatorio_consolidado'] = gerar_relatorio_consolidado(
                st.session_state['df_transacoes_editado'], 
                st.session_state['contexto_adicional'], 
                client
            )
            st.success("Relatório da IA atualizado com sucesso!")
        else:
            st.warning("Por favor, processe os extratos antes de atualizar o relatório.")
