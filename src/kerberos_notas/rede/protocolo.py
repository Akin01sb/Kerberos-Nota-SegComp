"""
@file protocolo.py
@brief Protocolo simples de mensagens JSON sobre TCP.

@details
Cada mensagem possui um cabecalho de 4 bytes em ordem de rede informando o
tamanho do JSON UTF-8. Isso evita leitura parcial de pacotes e permite que AS,
TGS e Portal de Notas troquem dicionarios de forma previsivel por sockets.
"""

import json
import struct


TAMANHO_MAXIMO_MENSAGEM = 1024 * 1024
FORMATO_CABECALHO = "!I"
TAMANHO_CABECALHO = struct.calcsize(FORMATO_CABECALHO)


def _receber_exatamente(conexao, quantidade):
    """
    @brief Le exatamente a quantidade de bytes solicitada.

    @param conexao Socket conectado.
    @param quantidade Numero de bytes esperados.
    @return Bytes recebidos.
    @throws ConnectionError Quando a conexao encerra antes da mensagem completa.
    """
    partes = []
    restante = quantidade

    while restante:
        parte = conexao.recv(restante)
        if not parte:
            raise ConnectionError("Conexao encerrada antes do fim da mensagem.")
        partes.append(parte)
        restante -= len(parte)

    return b"".join(partes)


def enviar_mensagem(conexao, dados):
    """
    @brief Envia um dicionario JSON com cabecalho de tamanho.

    @param conexao Socket conectado.
    @param dados Dicionario serializavel em JSON.
    @throws ValueError Quando a mensagem excede o limite configurado.
    """
    conteudo = json.dumps(
        dados,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    if len(conteudo) > TAMANHO_MAXIMO_MENSAGEM:
        raise ValueError("Mensagem de rede muito grande.")

    cabecalho = struct.pack(FORMATO_CABECALHO, len(conteudo))
    conexao.sendall(cabecalho + conteudo)


def receber_mensagem(conexao):
    """
    @brief Recebe e decodifica uma mensagem JSON completa.

    @param conexao Socket conectado.
    @return Dicionario decodificado do JSON recebido.
    @throws ValueError Quando o tamanho anunciado e invalido.
    """
    cabecalho = _receber_exatamente(conexao, TAMANHO_CABECALHO)
    tamanho = struct.unpack(FORMATO_CABECALHO, cabecalho)[0]
    if tamanho <= 0 or tamanho > TAMANHO_MAXIMO_MENSAGEM:
        raise ValueError("Tamanho de mensagem de rede invalido.")

    conteudo = _receber_exatamente(conexao, tamanho)
    return json.loads(conteudo.decode("utf-8"))
