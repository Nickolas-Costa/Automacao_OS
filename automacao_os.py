from logging import config
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os   
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
from logger import logger
from config import Urls, Timeouts, Locators_RAUZEE, Locators_SIOPI, formatters

# Carrega variáveis de ambiente
load_dotenv()

# Configurações
URL_SIOPI = config.URL_SIOPI
URL_RAUZEE = config.URL_RAUZEE

SIOPI_USER = config.SIOPI_USER
SIOPI_PASS = config.SIOPI_PASS
RAUZEE_USER = config.RAUZEE_USER
RAUZEE_PASS = config.RAUZEE_PASS

# LOGIN RAUZEE

def login_rauzee(page):
    if not RAUZEE_USER or not RAUZEE_PASS or RAUZEE_USER == "xxxx" or RAUZEE_PASS == "xxxx":
        raise Exception("Credenciais do RAUZEE não encontradas no arquivo .env")

    page.goto(URL_RAUZEE)

    # Aguarda os campos existirem
    page.wait_for_selector("#email", timeout=Timeouts["PADRAO"])
    page.fill("#email", RAUZEE_USER)

    page.wait_for_selector("#password", timeout=Timeouts["PADRAO"])
    page.fill("#password", RAUZEE_PASS)

    page.get_by_text("Acessar").click()
    page.wait_for_load_state("networkidle")

# LOGIN SIOPI

def login_siopi(page):
    if not SIOPI_USER or not SIOPI_PASS or SIOPI_USER == "xxxx" or SIOPI_PASS == "xxxx":
        raise Exception("Credenciais do SIOPI não encontradas no arquivo .env")

    page.goto(URL_SIOPI)

    # Aguarda os campos existirem
    page.wait_for_selector("#username", timeout=Timeouts["PADRAO"])
    page.fill("#username", SIOPI_USER)

    page.wait_for_selector("#password", timeout=Timeouts["PADRAO"])
    page.fill("#password", SIOPI_PASS)

    page.get_by_text("Entrar").click()
    page.wait_for_load_state("networkidle")

# FUNÇÕES SIOPI

# Controla o frame principal do SIOPI
def get_siopi_frame(page, tentativas=10):
    for _ in range(tentativas):
        for frame in page.frames:
            if "mantemAlertaOriginacao.do" in frame.url:
                return frame
        page.wait_for_timeout(Timeouts["MEDIO"])

    raise Exception("Frame principal do SIOPI não encontrado")

def abrir_menu_e_navegar(page):
    frame = get_siopi_frame(page)

    frame.wait_for_selector("#btn_menu", Timeouts["PADRAO"])
    frame.locator("#btn_menu").click(force=True)
    frame.wait_for_timeout(Timeouts["CURTO"])

    frame.get_by_text("Serviços").hover()
    frame.wait_for_timeout(Timeouts["CURTO"])

    frame.get_by_text("Cadastro de Imóveis").hover()
    frame.wait_for_timeout(Timeouts["CURTO"])

    frame.get_by_text("Ordens de Serviço de Engenharia").click()
    frame.wait_for_load_state("networkidle")

def consultar_os(page, codigo_os):
    frame = get_siopi_frame(page)
    
    frame.fill("#num_os", codigo_os)
    frame.locator("#botao0").click(force=True)
    frame.wait_for_timeout(Timeouts["LONGO"])

    frame.get_by_text(codigo_os).click()
    frame.wait_for_load_state("networkidle")
    frame.wait_for_timeout(Timeouts["LONGO"])

    # coleta status da OS
    status = frame.locator(
            'xpath=//*[@id="formulario"]/fieldset/table[3]/tbody/tr/td[2]'
        ).inner_text()

    # coleta nome cliente da OS
    nome_cliente = frame.locator(
        'xpath=//*[@id="formulario"]/fieldset/table[6]/tbody/tr[2]/td[2]'
    ).inner_text().strip()

    # coleta matricula da OS
    matricula = frame.locator(
        'xpath=//*[@id="formulario"]/fieldset/table[5]/tbody/tr[1]/td[2]'
    ).inner_text().strip()

    # coleta data abertura da OS
    data_abertura = frame.locator(
        'xpath=//*[@id="formulario"]/fieldset/table[1]/tbody/tr[1]/td[4]'
    ).inner_text().strip()
   
    # volta para tela inicial
    page.reload()
    frame.wait_for_timeout(Timeouts["PADRAO"])
     
    return {
        "os": codigo_os,
        "cliente": nome_cliente,
        "matricula": matricula,
        "data_abertura": data_abertura,
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
    # 1. Localiza o bloco que contém o label STATUS
    status_container = page.locator(
        Locators_RAUZEE["status_filter"]
    ).locator("..")  # sobe para o container pai

    # 2. Abre o multiselect
    status_container.locator(Locators_RAUZEE["multiselect_input"]).click(force=True)
    page.wait_for_timeout(Timeouts["CURTO"])

    # 3. Clica na opção "Solicitada"
    page.locator(Locators_RAUZEE["status_busca"]).click(force=True)

    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(Timeouts["MEDIO"])

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
    linhas = []
    data_consulta = datetime.datetime.now().strftime(formatters["data_consulta"])
    linhas.append(f"Relatório Automático - Consulta em: {data_consulta}\n")

    for r in resultados:
        linhas.append(f"🔢 OS: {r['os']}")
        linhas.append(f"👤 Cliente: {r['cliente']}")
        linhas.append(f"🏠 Matrícula: {r['matricula']}")
        linhas.append(f"📅 Data de Abertura: {r['data_abertura']}")
        linhas.append(f"ℹ️ Status Atual: {r['status']}")
        linhas.append("-" * 60)

    return "\n".join(linhas)

def enviar_email(resultados):
    corpo = montar_corpo_email(resultados)

    msg = MIMEMultipart()
    msg["From"] = os.getenv("EMAIL_USER")
    msg["To"] = os.getenv("EMAIL_TO")
    msg["Subject"] = "Relatório Automático - Consultas OS SIOPI"
    

    msg.attach(MIMEText(corpo, "plain"))


    with smtplib.SMTP(os.getenv("EMAIL_HOST"), int(os.getenv("EMAIL_PORT"))) as server:
        server.starttls()
        server.login(
            os.getenv("EMAIL_USER"),
            os.getenv("EMAIL_PASS")
        )
        server.send_message(msg)

# EXECUÇÃO

with sync_playwright() as p:
    logger.info("Início da execução.")

    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    
    # Parte 1 - RAUZEE
    login_rauzee(page)
    abrir_pesquisa_e_engenharias(page)
    filtrar_engenharias(page)
    extrair_codigos_os(page)
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

    print("Processo concluído com sucesso! Verifique seu email.")
