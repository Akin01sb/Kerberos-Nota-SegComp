from kerberos_notas.config import HOST_KERBEROS, PORTA_AS
from kerberos_notas.kerberos.as_server import (
    autenticar_no_as_com_prova,
    criar_desafio_as,
)
from kerberos_notas.rede.servidor import criar_servidor_tcp


def processar_requisicao_as(requisicao):
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
    return criar_servidor_tcp(
        host,
        porta,
        processar_requisicao_as,
        "AS",
    )


def executar_servidor_as(host=HOST_KERBEROS, porta=PORTA_AS):
    with criar_servidor_as(host, porta) as servidor:
        print(f"[AS] Servidor ouvindo em {host}:{servidor.server_address[1]}.")
        servidor.serve_forever()


if __name__ == "__main__":
    executar_servidor_as()
