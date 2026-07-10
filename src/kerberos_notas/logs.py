"""
Logs didaticos e seguros para o fluxo Kerberos academico.

O modulo centraliza o uso de print(..., flush=True) e mascara campos sensiveis
antes de exibir dados no terminal.
"""

import json
from datetime import datetime


LINHA = "=" * 78
CAMPOS_SENSIVEIS = (
    "autenticador",
    "chave",
    "ciphertext",
    "desafio",
    "nonce",
    "prova",
    "salt",
    "secret",
    "segredo",
    "senha",
    "sessao",
    "tgt",
    "ticket",
    "token",
    "verificador",
)
METADADOS_SEGUROS = (
    "quantidade_",
    "tamanho_",
    "total_",
)
CAMPOS_SEGUROS = {
    "senha_informada",
}


def _hora_atual():
    return datetime.now().strftime("%H:%M:%S")


def _campo_sensivel(campo):
    nome = str(campo).lower()
    if nome in CAMPOS_SEGUROS:
        return False
    if nome.startswith(METADADOS_SEGUROS):
        return False
    return any(sensivel in nome for sensivel in CAMPOS_SENSIVEIS)


def _resumo_mascarado(valor):
    if valor is None:
        return None
    if isinstance(valor, dict):
        return f"<mascarado:dict:{len(valor)} campos>"
    if isinstance(valor, list):
        return f"<mascarado:list:{len(valor)} itens>"
    texto = str(valor)
    return f"<mascarado:{len(texto)} caracteres>"


def mascarar_dados(dados, campo_atual=""):
    if _campo_sensivel(campo_atual):
        return _resumo_mascarado(dados)

    if isinstance(dados, dict):
        return {
            chave: mascarar_dados(valor, chave)
            for chave, valor in dados.items()
        }

    if isinstance(dados, list):
        return [
            mascarar_dados(item, campo_atual)
            for item in dados
        ]

    if isinstance(dados, tuple):
        return [
            mascarar_dados(item, campo_atual)
            for item in dados
        ]

    if isinstance(dados, str) and len(dados) > 120:
        return f"{dados[:60]}...{dados[-20:]}"

    return dados


def _imprimir_dados(dados):
    dados_mascarados = mascarar_dados(dados)
    texto = json.dumps(
        dados_mascarados,
        ensure_ascii=False,
        indent=4,
        default=str,
    )
    for linha in texto.splitlines():
        print(f"    {linha}", flush=True)


def log_titulo(componente, mensagem):
    print(LINHA, flush=True)
    print(f"[{_hora_atual()}] [{componente}] {mensagem}", flush=True)
    print(LINHA, flush=True)
    print("", flush=True)


def log_evento(componente, mensagem, dados=None, nivel=None):
    prefixo_nivel = f"{nivel} - " if nivel else ""
    print(
        f"[{_hora_atual()}] [{componente}] {prefixo_nivel}{mensagem}",
        flush=True,
    )
    if dados is not None:
        _imprimir_dados(dados)
    print("", flush=True)


def log_ok(componente, mensagem, dados=None):
    log_evento(componente, mensagem, dados=dados, nivel="OK")


def log_erro(componente, mensagem, dados=None):
    log_evento(componente, mensagem, dados=dados, nivel="ERRO")
