from kerberos_notas.config import HOST_KERBEROS, PORTA_TGS
from kerberos_notas.kerberos.tgs_server import emitir_ticket_servico
from kerberos_notas.rede.servidor import criar_servidor_tcp


def processar_requisicao_tgs(requisicao):
    if requisicao.get("acao") != "emitir_ticket":
        raise ValueError("Acao desconhecida no TGS.")

    return emitir_ticket_servico(
        usuario=requisicao.get("usuario", ""),
        servico=requisicao.get("servico", ""),
        tgt_criptografado=requisicao.get("tgt"),
        autenticador_criptografado=requisicao.get("autenticador"),
    )


def criar_servidor_tgs(host=HOST_KERBEROS, porta=PORTA_TGS):
    return criar_servidor_tcp(
        host,
        porta,
        processar_requisicao_tgs,
        "TGS",
    )


def executar_servidor_tgs(host=HOST_KERBEROS, porta=PORTA_TGS):
    with criar_servidor_tgs(host, porta) as servidor:
        print(f"[TGS] Servidor ouvindo em {host}:{servidor.server_address[1]}.")
        servidor.serve_forever()


if __name__ == "__main__":
    executar_servidor_tgs()
