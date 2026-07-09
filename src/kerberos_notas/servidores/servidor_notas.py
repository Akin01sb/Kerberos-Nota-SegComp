from kerberos_notas.config import HOST_KERBEROS, PORTA_NOTAS
from kerberos_notas.notes.portal_notas import (
    autenticar_portal_notas,
    processar_operacao_portal,
)
from kerberos_notas.rede.servidor import criar_servidor_tcp


def processar_requisicao_notas(requisicao):
    acao = requisicao.get("acao")

    if acao == "autenticar_portal":
        return autenticar_portal_notas(
            requisicao.get("ticket_servico"),
            requisicao.get("autenticador"),
        )

    if acao == "executar_operacao":
        return processar_operacao_portal(
            requisicao.get("ticket_servico"),
            requisicao.get("autenticador"),
            requisicao.get("requisicao"),
        )

    raise ValueError("Acao desconhecida no Portal de Notas.")


def criar_servidor_notas(host=HOST_KERBEROS, porta=PORTA_NOTAS):
    return criar_servidor_tcp(
        host,
        porta,
        processar_requisicao_notas,
        "NOTAS",
    )


def executar_servidor_notas(host=HOST_KERBEROS, porta=PORTA_NOTAS):
    with criar_servidor_notas(host, porta) as servidor:
        print(
            f"[NOTAS] Servidor ouvindo em "
            f"{host}:{servidor.server_address[1]}."
        )
        servidor.serve_forever()


if __name__ == "__main__":
    executar_servidor_notas()
