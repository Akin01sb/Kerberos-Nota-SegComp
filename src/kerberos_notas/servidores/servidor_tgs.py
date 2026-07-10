"""
@file servidor_tgs.py
@brief Ponto de entrada TCP do Ticket Granting Server.

@details
Recebe requisicoes para emissao de Service Ticket e chama a logica do TGS,
mantendo o TGS em processo/porta separados do AS e do servico de notas.
"""

from kerberos_notas.config import HOST_KERBEROS, PORTA_TGS
from kerberos_notas.kerberos.tgs_server import emitir_ticket_servico
from kerberos_notas.logs import log_erro, log_evento, log_ok
from kerberos_notas.rede.servidor import criar_servidor_tcp


def processar_requisicao_tgs(requisicao):
    """
    @brief Processa uma chamada remota destinada ao TGS.

    @param requisicao Dicionario JSON recebido por socket.
    @return Resposta do TGS com Service Ticket e dados cifrados ao cliente.
    @throws ValueError Quando a acao nao existe.
    """
    log_evento(
        "TGS",
        "Processando acao recebida pelo Ticket Granting Server",
        {
            "acao": requisicao.get("acao"),
            "usuario": requisicao.get("usuario"),
            "servico": requisicao.get("servico"),
        },
    )
    if requisicao.get("acao") != "emitir_ticket":
        log_erro(
            "TGS",
            "Acao desconhecida recebida",
            {"acao": requisicao.get("acao")},
        )
        raise ValueError("Acao desconhecida no TGS.")

    resposta = emitir_ticket_servico(
        usuario=requisicao.get("usuario", ""),
        servico=requisicao.get("servico", ""),
        tgt_criptografado=requisicao.get("tgt"),
        autenticador_criptografado=requisicao.get("autenticador"),
    )
    log_ok(
        "TGS",
        "Resposta com Service Ticket emitida",
        resposta,
    )
    return resposta


def criar_servidor_tgs(host=HOST_KERBEROS, porta=PORTA_TGS):
    """
    @brief Cria a instancia TCP do TGS.

    @param host Interface de escuta.
    @param porta Porta TCP do TGS.
    @return Servidor TCP configurado.
    """
    return criar_servidor_tcp(
        host,
        porta,
        processar_requisicao_tgs,
        "TGS",
    )


def executar_servidor_tgs(host=HOST_KERBEROS, porta=PORTA_TGS):
    """@brief Executa o TGS em loop ate interrupcao externa."""
    with criar_servidor_tgs(host, porta) as servidor:
        log_ok(
            "TGS",
            "Ticket Granting Server ouvindo",
            {"host": host, "porta": servidor.server_address[1]},
        )
        servidor.serve_forever()


if __name__ == "__main__":
    executar_servidor_tgs()
