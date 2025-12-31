from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os
import re
import time

# =========================
# CONFIGURAÇÃO
# =========================
load_dotenv()

URL_RAUZEE = os.getenv("URL_RAUZEE")
RAUZEE_USER = os.getenv("RAUZEE_USER")
RAUZEE_PASS = os.getenv("RAUZEE_PASS")

# =========================
# LOGIN
# =========================

def login_rauzee(page):
    if not RAUZEE_USER or not RAUZEE_PASS or RAUZEE_USER == "xxxx" or RAUZEE_PASS == "xxxx":
        raise Exception("Credenciais do RAUZEE não encontradas no arquivo .env")

    page.goto(URL_RAUZEE)

    # Aguarda os campos existirem
    page.wait_for_selector("#email", timeout=20000)
    page.fill("#email", RAUZEE_USER)

    page.wait_for_selector("#password", timeout=20000)
    page.fill("#password", RAUZEE_PASS)

    page.get_by_text("Acessar").click()
    page.wait_for_load_state("networkidle")

# =========================
# FUNÇÕES
# =========================

def abrir_pesquisa_e_engenharias(page):
    page.wait_for_load_state("networkidle")
    page.locator('input[placeholder="Pesquisar..."]').click(force=True)
    page.wait_for_timeout(500)

    page.locator("text=Listar engenharias").click(force=True)

    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(800)

def filtrar_engenharias(page):
    # 1. Localiza o bloco que contém o label STATUS
    status_container = page.locator(
        "text=STATUS"
    ).locator("..")  # sobe para o container pai

    # 2. Abre o multiselect
    status_container.locator("input.multiselect-search").click(force=True)
    page.wait_for_timeout(500)

    # 3. Clica na opção "Solicitada"
    page.locator("li:has-text('Solicitada')").click(force=True)

    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(800)

    page.keyboard.press("Escape")

def extrair_codigos_os(page):
    codigos = []

    tabela = page.locator("table")
    linhas = tabela.locator("tbody tr")

    total = linhas.count()

    for i in range(total):
        linha = linhas.nth(i)
        colunas = linha.locator("td")
        qtd_colunas = colunas.count()

        if qtd_colunas < 6:
            continue 
        
        texto = colunas.nth(5).inner_text().strip()

        # Regex do padrão SIOPI
        match = re.search(r"\d{4}\.\d{4}\.\d+\/\d{4}\.\d{2}\.\d{2}", texto)
        if match:
            codigos.append(match.group())

    return list(set(codigos)) 

# =========================
# EXECUÇÃO
# =========================

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    
    login_rauzee(page)
    abrir_pesquisa_e_engenharias(page)
    filtrar_engenharias(page)
    extrair_codigos_os(page)
    lista_os = extrair_codigos_os(page)
    
    print(lista_os)
    print("Processo concluído.")
    
    browser.close()
