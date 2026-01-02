from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime

# =========================
# CONFIGURAÇÃO
# =========================
load_dotenv()

URL_SIOPI = os.getenv("URL_SIOPI")
SIOPI_USER = os.getenv("SIOPI_USER")
SIOPI_PASS = os.getenv("SIOPI_PASS")

# =========================
# FUNÇÕES
# =========================

def carregar_lista_os(caminho_arquivo):
    with open(caminho_arquivo, "r", encoding="utf-8") as f:
        return [linha.strip() for linha in f if linha.strip()]

lista_os = carregar_lista_os("os_list.txt")

def login_siopi(page):
    if not SIOPI_USER or not SIOPI_PASS:
        raise Exception("Credenciais do SIOPI não encontradas no arquivo .env")

    page.goto(URL_SIOPI)

    # Aguarda os campos existirem
    page.wait_for_selector("#username", timeout=20000)
    page.fill("#username", SIOPI_USER)

    page.wait_for_selector("#password", timeout=20000)
    page.fill("#password", SIOPI_PASS)

    page.get_by_text("Entrar").click()
    page.wait_for_load_state("networkidle")

def get_siopi_frame(page, tentativas=10):
    for _ in range(tentativas):
        for frame in page.frames:
            if "mantemAlertaOriginacao.do" in frame.url:
                return frame
        page.wait_for_timeout(1000)

    raise Exception("Frame principal do SIOPI não encontrado")


def abrir_menu_e_navegar(page):
    frame = get_siopi_frame(page)

    frame.wait_for_selector("#btn_menu", timeout=20000)
    frame.locator("#btn_menu").click(force=True)
    frame.wait_for_timeout(800)

    frame.get_by_text("Serviços").hover()
    frame.wait_for_timeout(400)

    frame.get_by_text("Cadastro de Imóveis").hover()
    frame.wait_for_timeout(400)

    frame.get_by_text("Ordens de Serviço de Engenharia").click()
    frame.wait_for_load_state("networkidle")

def consultar_os(page, codigo_os):
    frame = get_siopi_frame(page)
    
    frame.fill("#num_os", codigo_os)
    frame.locator("#botao0").click(force=True)
    frame.wait_for_timeout(2000)

    frame.get_by_text(codigo_os).click()
    frame.wait_for_load_state("networkidle")
    frame.wait_for_timeout(2000)

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
    frame.wait_for_timeout(400)
     
    return {
        "os": codigo_os,
        "cliente": nome_cliente,
        "matricula": matricula,
        "data_abertura": data_abertura,
        "status": status
    }

# =========================
# Email
# =========================

def montar_corpo_email(resultados):
    linhas = []
    data = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    linhas.append(f"Relatório Automático - Consulta em: {data}\n")

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

# =========================
# EXECUÇÃO
# =========================
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    
    login_siopi(page)
    Resultados = []

    # Loop para consultar cada OS e enviar email
    for os_codigo in lista_os:
        abrir_menu_e_navegar(page)
        dados = consultar_os(page, os_codigo)
        Resultados.append(dados)

    enviar_email(Resultados)

    browser.close()