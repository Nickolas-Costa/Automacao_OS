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
    "login_usuario": "#email",
    "login_senha": "#password",
    "botao_acessar": "Acessar",
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
   "Frame": "mantemAlertaOriginacao.do",
    "login_usuario": "#username",
    "login_senha": "#password",
    "botao_entrar": 'Entrar',
    "menu": "#btn_menu",
    "submenu_servicos": 'text=Serviços',
    "submenu_imoveis": 'Cadastro de Imóveis',
    "submenu_os": 'Ordens de Serviço de Engenharia',
    "input_os": "#num_os",
    "botao_consultar": "#botao0",
    "status_OS": 'xpath=//*[@id="formulario"]/fieldset/table[3]/tbody/tr/td[2]',
    "nome_cliente": 'xpath=//*[@id="formulario"]/fieldset/table[6]/tbody/tr[2]/td[2]',
    "matricula": 'xpath=//*[@id="formulario"]/fieldset/table[5]/tbody/tr[1]/td[2]',
    "data_abertura": 'xpath=//*[@id="formulario"]/fieldset/table[1]/tbody/tr[1]/td[4]',
}

formatters = {
    "OS Codigo": r"\d{4}\.\d{4}\.\d+\/\d{4}\.\d{2}\.\d{2}",
    "data_consulta": "%d/%m/%Y %H:%M"
}