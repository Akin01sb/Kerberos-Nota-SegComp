import json
import struct


TAMANHO_MAXIMO_MENSAGEM = 1024 * 1024
FORMATO_CABECALHO = "!I"
TAMANHO_CABECALHO = struct.calcsize(FORMATO_CABECALHO)


def _receber_exatamente(conexao, quantidade):
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
    cabecalho = _receber_exatamente(conexao, TAMANHO_CABECALHO)
    tamanho = struct.unpack(FORMATO_CABECALHO, cabecalho)[0]
    if tamanho <= 0 or tamanho > TAMANHO_MAXIMO_MENSAGEM:
        raise ValueError("Tamanho de mensagem de rede invalido.")

    conteudo = _receber_exatamente(conexao, tamanho)
    return json.loads(conteudo.decode("utf-8"))
