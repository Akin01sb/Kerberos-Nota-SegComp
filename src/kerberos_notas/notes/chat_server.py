import json
import socket

from kerberos_notas.notes.chat_seguro import (
    autenticar_servico_chat,
    receber_mensagem_segura,
)


def processar_pacote_chat(pacote: dict) -> dict:
    try:
        ticket_servico = pacote["ticket_servico"]
        confirmacao = autenticar_servico_chat(
            ticket_servico,
            pacote["autenticador"]
        )
        mensagem = receber_mensagem_segura(
            ticket_servico,
            pacote["mensagem"]
        )

        return {
            "ok": True,
            "confirmacao": confirmacao,
            "mensagem": mensagem
        }
    except Exception as erro:
        return {
            "ok": False,
            "erro": str(erro)
        }


def iniciar_servidor_chat(
        host: str = "127.0.0.1",
        porta: int = 5050,
        quantidade_conexoes: int = 1
) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind((host, porta))
        servidor.listen()

        for _ in range(quantidade_conexoes):
            conexao, _ = servidor.accept()

            with conexao:
                dados = b""
                while True:
                    parte = conexao.recv(4096)
                    if not parte:
                        break
                    dados += parte

                pacote = json.loads(dados.decode("utf-8"))
                resposta = processar_pacote_chat(pacote)
                conexao.sendall(json.dumps(resposta).encode("utf-8"))
