import json
import socket

from kerberos_notas.kerberos.authenticator import criar_autenticador
from kerberos_notas.notes.chat_seguro import (
    criar_mensagem_segura,
    validar_confirmacao_servico,
)


def montar_pacote_chat(
        remetente: str,
        destinatario: str,
        conteudo: str,
        ticket_servico_criptografado: dict,
        chave_sessao_cliente_servico_base64: str,
        nonce_autenticador: str = "nonce-chat"
) -> dict:
    autenticador = criar_autenticador(
        remetente,
        chave_sessao_cliente_servico_base64,
        nonce=nonce_autenticador
    )
    mensagem = criar_mensagem_segura(
        remetente,
        destinatario,
        conteudo,
        chave_sessao_cliente_servico_base64
    )

    return {
        "ticket_servico": ticket_servico_criptografado,
        "autenticador": autenticador,
        "mensagem": mensagem,
        "nonce_autenticador": nonce_autenticador
    }


def validar_resposta_chat(
        chave_sessao_cliente_servico_base64: str,
        resposta: dict,
        nonce_autenticador: str
) -> dict:
    if not resposta.get("ok"):
        raise ValueError(resposta.get("erro", "Erro no servidor de chat."))

    return validar_confirmacao_servico(
        chave_sessao_cliente_servico_base64,
        resposta["confirmacao"],
        nonce_autenticador
    )


def enviar_pacote_chat(
        pacote: dict,
        host: str = "127.0.0.1",
        porta: int = 5050
) -> dict:
    dados = json.dumps(pacote).encode("utf-8")

    with socket.create_connection((host, porta), timeout=5) as conexao:
        conexao.sendall(dados)
        conexao.shutdown(socket.SHUT_WR)

        resposta = b""
        while True:
            parte = conexao.recv(4096)
            if not parte:
                break
            resposta += parte

    return json.loads(resposta.decode("utf-8"))
