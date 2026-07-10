"""
@file servidor_as.py
@brief Ponto de entrada TCP do Authentication Server.

@details
Recebe requisicoes JSON do cliente Flask e encaminha para a logica do AS:
obtencao de parametros de desafio e autenticacao por prova HMAC.
"""

from kerberos_notas.config import HOST_KERBEROS, PORTA_AS
from kerberos_notas.kerberos.as_server import (
    autenticar_no_as_com_prova,
    criar_desafio_as,
)
from kerberos_notas.rede.servidor import criar_servidor_tcp


def processar_requisicao_as(requisicao):
    """
    @brief Processa uma chamada remota destinada ao AS.

    @param requisicao Dicionario JSON recebido por socket.
    @return Resposta produzida pela logica do AS.
    @throws ValueError Quando a acao nao existe.
    """
    acao = requisicao.get("acao")
    usuario = requisicao.get("usuario", "")

    if acao == "obter_parametros":
        return criar_desafio_as(usuario)

    if acao == "autenticar":
        return autenticar_no_as_com_prova(
            usuario,
            requisicao.get("desafio", ""),
            requisicao.get("prova", ""),
        )

    raise ValueError("Acao desconhecida no AS.")


def criar_servidor_as(host=HOST_KERBEROS, porta=PORTA_AS):
    """
    @brief Cria a instancia TCP do AS.

    @param host Interface de escuta.
    @param porta Porta TCP do AS.
    @return Servidor TCP configurado.
    """
    return criar_servidor_tcp(
        host,
        porta,
        processar_requisicao_as,
        "AS",
    )


def executar_servidor_as(host=HOST_KERBEROS, porta=PORTA_AS):
    """@brief Executa o AS em loop ate interrupcao externa."""
    with criar_servidor_as(host, porta) as servidor:
        print(f"[AS] Servidor ouvindo em {host}:{servidor.server_address[1]}.")
        servidor.serve_forever()


if __name__ == "__main__":
    executar_servidor_as()
