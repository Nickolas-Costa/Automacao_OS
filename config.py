import os
import re

# URLs
Urls = {
    "SIOPI": os.getenv("URL_SIOPI"),
    "RAUZEE": os.getenv("URL_RAUZEE"),
}

# TIMEOUTS
Timeouts = {
    "PADRAO": 2_000,
    "CURTO": 500,
    "MEDIO": 800,
    "LONGO": 5_000,
}

# SELETORES RAUZEE
Locators_RAUZEE = {
    "search_button": 'input[placeholder="Pesquisar..."]',
    "engenharias_shortcut": "text=Listar engenharias",
    "status_filter": "xpath=//*[@aria-labelledby='assist']",
    "multiselect_input": "input.multiselect-search",
    "status_busca": "text=Solicitada",
    "tabela": "table",
    "tabela_linhas": "tbody tr",
    "linha_os_codigo": "td",
}

# SELETORES SIOPI
Locators_SIOPI = {
    "menu": "#btn_menu",
    "num_os": "#num_os",
    "botao_consultar": "#botao0",
    "status": 'xpath=//*[@id="formulario"]/fieldset/table[3]/tbody/tr/td[2]',
}

formatters = {
    "OS Codigo": r"\d{4}\.\d{4}\.\d+\/\d{4}\.\d{2}\.\d{2}",
    "data_consulta": "%d/%m/%Y %H:%M"
}