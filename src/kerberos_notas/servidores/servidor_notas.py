"""
@file servidor_notas.py
@brief Ponto de entrada TCP do servico protegido de notas.

@details
Recebe autenticacao inicial Cliente-Servico e operacoes cifradas de notas. A
validacao Kerberos fica em `notes.portal_notas`.
"""

from kerberos_notas.config import HOST_KERBEROS, PORTA_NOTAS
from kerberos_notas.notes.portal_notas import (
    autenticar_portal_notas,
    processar_operacao_portal,
)
from kerberos_notas.logs import log_erro, log_evento, log_ok
from kerberos_notas.rede.servidor import criar_servidor_tcp


def processar_requisicao_notas(requisicao):
    """
    @brief Processa uma chamada remota destinada ao Portal de Notas.

    @param requisicao Dicionario JSON recebido por socket.
    @return Confirmacao de autenticacao ou resultado cifrado de operacao.
    @throws ValueError Quando a acao nao existe.
    """
    acao = requisicao.get("acao")
    log_evento(
        "PORTAL NOTAS",
        "Processando acao recebida pelo servico protegido",
        {"acao": acao},
    )

    if acao == "autenticar_portal":
        resposta = autenticar_portal_notas(
            requisicao.get("ticket_servico"),
            requisicao.get("autenticador"),
        )
        log_ok(
            "PORTAL NOTAS",
            "Autenticacao Cliente-Servico respondida",
            {"confirmacao_portal": resposta},
        )
        return resposta

    if acao == "executar_operacao":
        resposta = processar_operacao_portal(
            requisicao.get("ticket_servico"),
            requisicao.get("autenticador"),
            requisicao.get("requisicao"),
        )
        log_ok(
            "PORTAL NOTAS",
            "Operacao protegida processada",
            {"resposta_operacao": resposta},
        )
        return resposta

    log_erro("PORTAL NOTAS", "Acao desconhecida recebida", {"acao": acao})
    raise ValueError("Acao desconhecida no Portal de Notas.")


def criar_servidor_notas(host=HOST_KERBEROS, porta=PORTA_NOTAS):
    """
    @brief Cria a instancia TCP do Portal de Notas.

    @param host Interface de escuta.
    @param porta Porta TCP do servico de notas.
    @return Servidor TCP configurado.
    """
    return criar_servidor_tcp(
        host,
        porta,
        processar_requisicao_notas,
        "NOTAS",
    )


def executar_servidor_notas(host=HOST_KERBEROS, porta=PORTA_NOTAS):
    """@brief Executa o Portal de Notas em loop ate interrupcao externa."""
    with criar_servidor_notas(host, porta) as servidor:
        log_ok(
            "PORTAL NOTAS",
            "Servico de Notas ouvindo",
            {"host": host, "porta": servidor.server_address[1]},
        )
        servidor.serve_forever()


if __name__ == "__main__":
    executar_servidor_notas()
