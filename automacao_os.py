from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os   
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime as dt
from logger import logger
from config import Timeouts, Locators_RAUZEE, Locators_SIOPI, formatters

# Carrega variáveis de ambiente
load_dotenv()

# Configurações
URL_SIOPI = os.getenv("URL_SIOPI")
URL_RAUZEE = os.getenv("URL_RAUZEE")

SIOPI_USER = os.getenv("SIOPI_USER")
SIOPI_PASS = os.getenv("SIOPI_PASS")
RAUZEE_USER = os.getenv("RAUZEE_USER")
RAUZEE_PASS = os.getenv("RAUZEE_PASS")

# LOGIN RAUZEE

def login_rauzee(page):
    if not RAUZEE_USER or not RAUZEE_PASS:
        raise EnvironmentError(
        "Variáveis RAUZEE_USER ou RAUZEE_PASS não definidas. "
        "Verifique o arquivo .env."
    )

    if RAUZEE_USER.lower() == "xxxx" or RAUZEE_PASS.lower() == "xxxx":
        raise ValueError(
        "Credenciais do RAUZEE ainda estão com valor placeholder (xxxx). "
        "Atualize o arquivo .env antes de executar."
    )
    
    page.goto(URL_RAUZEE)

    # Aguarda os campos existirem
    page.wait_for_selector(Locators_RAUZEE["login_usuario"], timeout=Timeouts["PADRAO"])
    page.fill(Locators_RAUZEE["login_usuario"], RAUZEE_USER)

    page.wait_for_selector(Locators_RAUZEE["login_senha"], timeout=Timeouts["PADRAO"])
    page.fill(Locators_RAUZEE["login_senha"], RAUZEE_PASS)
    page.get_by_text(Locators_RAUZEE["botao_acessar"]).click()
    page.wait_for_load_state("networkidle")

# LOGIN SIOPI

def login_siopi(page):
    if not SIOPI_USER or not SIOPI_PASS:
        raise EnvironmentError(
        "Variáveis SIOPI_USER ou SIOPI_PASS não definidas. "
        "Verifique o arquivo .env."
    )

    if SIOPI_USER.lower() == "xxxx" or SIOPI_PASS.lower() == "xxxx":
        raise ValueError(
        "Credenciais do SIOPI ainda estão com valor placeholder (xxxx). "
        "Atualize o arquivo .env antes de executar."
    )

    page.goto(URL_SIOPI)

    # Aguarda os campos existirem
    page.wait_for_selector(Locators_SIOPI["login_usuario"], timeout=Timeouts["PADRAO"])
    page.fill(Locators_SIOPI["login_usuario"], SIOPI_USER)

    page.wait_for_selector(Locators_SIOPI["login_senha"], timeout=Timeouts["PADRAO"])
    page.fill(Locators_SIOPI["login_senha"], SIOPI_PASS)

    page.get_by_text(Locators_SIOPI["botao_entrar"]).click()
    page.wait_for_load_state("networkidle")

# FUNÇÕES SIOPI

# Controla o frame principal do SIOPI
def get_siopi_frame(page, tentativas=10):
    for _ in range(tentativas):
        for frame in page.frames:
            if Locators_SIOPI["Frame"] in frame.url:
                return frame
        page.wait_for_timeout(Timeouts["MEDIO"])

    logger.critical(
    "[SIOPI] Frame principal não encontrado após múltiplas tentativas. "
    "Sistema possivelmente fora do ar ou estrutura alterada.")

    raise RuntimeError("Frame principal do SIOPI não encontrado após múltiplas tentativas."
    "Possível mudança estrutural ou indisponibilidade do sistema.")

def abrir_menu_e_navegar(page):
    frame = get_siopi_frame(page)

    frame.wait_for_selector(Locators_SIOPI["menu"], timeout=Timeouts["PADRAO"])
    frame.locator(Locators_SIOPI["menu"]).click(force=True)
    frame.wait_for_timeout(Timeouts["CURTO"])

    frame.get_by_text(Locators_SIOPI["submenu_servicos"]).hover()
    frame.wait_for_timeout(Timeouts["CURTO"])

    frame.get_by_text(Locators_SIOPI["submenu_imoveis"]).hover()
    frame.wait_for_timeout(Timeouts["CURTO"])

    frame.get_by_text(Locators_SIOPI["submenu_os"]).click()
    frame.wait_for_load_state("networkidle")

def consultar_os(page, codigo_os):
    frame = get_siopi_frame(page)

    frame.fill(Locators_SIOPI["input_os"], codigo_os)
    frame.locator(Locators_SIOPI["botao_consultar"]).click(force=True)
    frame.wait_for_timeout(Timeouts["LONGO"])

    frame.get_by_text(codigo_os).click()
    frame.wait_for_load_state("networkidle")
    frame.wait_for_timeout(Timeouts["LONGO"])

    # coleta status da OS
    status = frame.locator(
            Locators_SIOPI["status_OS"]
        ).inner_text()
    
    # coleta CPF cliente da OS
    cpf_cliente = frame.locator(
            Locators_SIOPI["CPF_cliente"]
        ).inner_text()

    # coleta nome cliente da OS
    nome_cliente = frame.locator(
        Locators_SIOPI["nome_cliente"]
    ).inner_text().strip()

    # coleta matricula da OS
    matricula = frame.locator(
        Locators_SIOPI["matricula"]
    ).inner_text().strip()

    # coleta cartorio da OS
    cartorio = frame.locator(
        Locators_SIOPI["cartorio"]
        ).inner_text().strip()

    # coleta data abertura da OS
    data_abertura = frame.locator(
        Locators_SIOPI["data_abertura"]
    ).inner_text().strip()

    # coleta nome da empresa contratada
    nome_empresa = frame.locator(
        Locators_SIOPI["nome_empresa"]
    ).inner_text().strip()

    # coleta CNPJ da empresa contratada
    cnpj_empresa = frame.locator(
        Locators_SIOPI["CNPJ_empresa"]
    ).inner_text().strip()
   
    logger.info(f"[SIOPI] Finalizando consulta da OS {codigo_os}. Tentando recarregar página.")

    try:
    # volta para tela inicial
        page.reload(timeout=Timeouts["LONGO"])
        frame.wait_for_timeout(Timeouts["PADRAO"])
        logger.info(f"[SIOPI] Reload executado com sucesso após OS: {codigo_os}")

    except Exception as e:
        logger.error(f"[SIOPI] Erro ao recarregar página após OS: {codigo_os}: {e}"
        f"Possível instabilidade no Sistema. Erro: {str(e)}."             
                     , exc_info=True)
        
        return {
        "os": codigo_os,
        "cliente": None,
        "cpf_cliente": None,
        "matricula": None,
        "cartorio": None,
        "data_abertura": None,
        "nome_empresa": None,
        "CNPJ_empresa": None,
        "status": "Erro pós-consulta (instabilidade SIOPI)"
    }

    logger.info(
    f"[CHECKPOINT] OS {codigo_os} | Cliente: {nome_cliente} | "
    f"CPF: {cpf_cliente} | Matrícula: {matricula} | Cartório: {cartorio} | "
    f"Status: {status}")
     
    return {
        "os": codigo_os,
        "cliente": nome_cliente,
        "cpf_cliente": cpf_cliente,
        "matricula": matricula,
        "cartorio": cartorio,
        "data_abertura": data_abertura,
        "nome_empresa": nome_empresa,
        "CNPJ_empresa": cnpj_empresa,
        "status": status
    }

# FUNÇÕES RAUZEE

def abrir_pesquisa_e_engenharias(page):
    page.wait_for_load_state("networkidle")
    page.locator(Locators_RAUZEE["search_button"]).click(force=True)
    page.wait_for_timeout(Timeouts["CURTO"])

    page.locator(Locators_RAUZEE["engenharias_shortcut"]).click(force=True)

    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(Timeouts["CURTO"])

def filtrar_engenharias(page):
    # 1. Localiza o bloco que contém o label Status
    status_block = page.locator(
        "label", has_text="Status"
        ).locator("..")  

    # 2. Abre o multiselect
    status_block.locator(
        ".multiselect-search").first.click(force=True)
    page.wait_for_timeout(Timeouts["CURTO"])

    # 3. Clica na opção "Solicitada"
    page.locator(".multiselect-option", has_text="Solicitada"
                 ).click(force=True)

    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(Timeouts["LONGO"])

    page.keyboard.press("Escape")

def extrair_codigos_os(page):
    codigos = []

    tabela = page.locator(Locators_RAUZEE["tabela"])
    linhas = tabela.locator(Locators_RAUZEE["tabela_linhas"])

    total = linhas.count()

    for i in range(total):
        linha = linhas.nth(i)
        colunas = linha.locator(Locators_RAUZEE["linha_os_codigo"])
        qtd_colunas = colunas.count()

        if qtd_colunas < 6:
            continue 
        
        texto = colunas.nth(5).inner_text().strip()

        # Regex do padrão SIOPI
        match = re.search(formatters["OS Codigo"], texto)
        if match:
            codigos.append(match.group())

    return list(set(codigos)) 

# FUNÇÕES EMAIL

def montar_corpo_email(resultados):
    data_consulta = dt.datetime.now().strftime(formatters["data_consulta"])

    linhas = []

    for r in resultados:
        erro = "Erro" in r["status"]
        cor_linha = "#f8d7da" if erro else "#d4edda"
        status_formatado = r["status"]

        linhas.append(f"""
        <tr style="background-color:{cor_linha}">
            <td>{r['os']}</td>
            <td>{r['cliente'] or 'Indisponível'}</td>
            <td>{r['cpf_cliente'] or 'Indisponível'}</td>
            <td>{r['matricula'] or 'Indisponível'}</td>
            <td>{r['cartorio'] or 'Indisponível'}</td>
            <td>{r['data_abertura'] or 'Indisponível'}</td>
            <td>{r['nome_empresa'] or 'Indisponível'}</td>
            <td>{r['CNPJ_empresa'] or 'Indisponível'}</td>
            <td><strong>{status_formatado}</strong></td>
        </tr>
        """)

    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; font-size: 13px;">
        <h2>📄 Relatório Automático – Consulta de OS</h2>
        <p><strong>Data da consulta:</strong> {data_consulta}</p>

        <table border="1" cellpadding="6" cellspacing="0"
               style="border-collapse: collapse; width: 100%; text-align: left;">
            <thead style="background-color:#343a40; color:white;">
                <tr>
                    <th>OS</th>
                    <th>Cliente</th>
                    <th>CPF</th>
                    <th>Matrícula</th>
                    <th>Cartório</th>
                    <th>Data de Abertura</th>
                    <th>Empresa</th>
                    <th>CNPJ</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {''.join(linhas)}
            </tbody>
        </table>

        <br>
        <p style="font-size:12px; color:#555;">
            ⚠️ Linhas em vermelho indicam erro ou instabilidade na consulta.
        </p>
    </body>
    </html>
    """

def enviar_email(resultados):
    corpo = montar_corpo_email(resultados)

    msg = MIMEMultipart()
    msg["From"] = os.getenv("EMAIL_USER")
    msg["To"] = os.getenv("EMAIL_TO")
    msg["Subject"] = "Relatório Automático - Consultas OS SIOPI"
    

    msg.attach(MIMEText(corpo, "html"))


    with smtplib.SMTP(os.getenv("EMAIL_HOST"), int(os.getenv("EMAIL_PORT"))) as server:
        server.starttls()
        server.login(
            os.getenv("EMAIL_USER"),
            os.getenv("EMAIL_PASS")
        )
        server.send_message(msg)

# FUNÇÕES DE EXECUÇÃO
def banner_inicial():
    separador_maior = "=" * 80
    print(separador_maior)
    print("     AUTOMACAO DE CONSULTA DE OS - SIOPI     ")
    print(separador_maior)
    print("📅 Data:", dt.datetime.now().strftime(formatters["data_consulta"]))
    print(separador_maior)
    print()

def banner_final():
    separador_maior = "=" * 80
    print()
    print(separador_maior)
    print("     ✔ PROCESSO FINALIZADO COM SUCESSO      ")
    if any(r["status"] == "ERRO" for r in resultados):
        print("⚠ ATENÇÃO: Uma(s) OS retornar(am) erro verifique os logs de execução.")

    print(separador_maior)

# EXECUÇÃO

with sync_playwright() as p:
    banner_inicial()
    logger.info("Início da execução.")

    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    # Parte 1 - RAUZEE
    login_rauzee(page)
    abrir_pesquisa_e_engenharias(page)
    filtrar_engenharias(page)
    lista_os = extrair_codigos_os(page)
        
    # Parte 2 - SIOPI
    page = context.new_page()
    login_siopi(page)

    resultados = []
    for os_codigo in lista_os:
        try:
            logger.info(f"Iniciando consulta da OS: {os_codigo}")
            abrir_menu_e_navegar(page)
            dados = consultar_os(page, os_codigo)
            resultados.append(dados)

        except Exception as e:
            logger.error(f"Erro ao consultar OS {os_codigo}: {e}", 
                          exc_info=True)
            
            resultados.append({
                "os": os_codigo,
                "status": "Erro na consulta"
            })

    # Parte 3 - Envio dos resultados via email
    enviar_email(resultados)
    browser.close()

    print("👌Processo concluído com sucesso! Verifique seu email.")
