import base64
import hashlib
import hmac
import json
import uuid

from kerberos_notas.crypto.crypto_utils import (
    base64_para_bytes,
    criptografar_json,
    descriptografar_json,
)
from kerberos_notas.kerberos.authenticator import abrir_autenticador
from kerberos_notas.kerberos.tgs_server import abrir_ticket_servico
from kerberos_notas.kerberos.tickets import ticket_expirou, timestamp_atual


SERVICO_CHAT = "chat"
TEMPO_MAXIMO_AUTENTICADOR = 60 * 5
ALERTA_INTEGRIDADE = "Mensagem violada: integridade comprometida"
ALERTA_IDENTIDADE = "Identidade invalida: usuario nao corresponde ao ticket"


def validar_ticket_chat(ticket_servico_criptografado: dict) -> dict:
    return abrir_ticket_servico(SERVICO_CHAT, ticket_servico_criptografado)


def autenticar_servico_chat(
        ticket_servico_criptografado: dict,
        autenticador_criptografado: dict
) -> dict:
    ticket = validar_ticket_chat(ticket_servico_criptografado)
    chave_sessao_base64 = ticket["chave_sessao_cliente_servico"]

    try:
        autenticador = abrir_autenticador(
            chave_sessao_base64,
            autenticador_criptografado
        )
    except Exception as erro:
        raise ValueError("Autenticador do chat invalido.") from erro

    if autenticador.get("usuario") != ticket["usuario"]:
        raise ValueError(ALERTA_IDENTIDADE)

    timestamp = autenticador.get("timestamp")
    if timestamp is None:
        raise ValueError("Autenticador do chat sem timestamp.")

    if ticket_expirou(timestamp, TEMPO_MAXIMO_AUTENTICADOR):
        raise ValueError("Autenticador do chat expirado.")

    chave_sessao = base64_para_bytes(chave_sessao_base64)

    return criptografar_json(
        chave_sessao,
        {
            "usuario": ticket["usuario"],
            "timestamp": timestamp_atual(),
            "nonce_autenticador": autenticador.get("nonce"),
            "status": "canal_autenticado"
        }
    )


def validar_confirmacao_servico(
        chave_sessao_cliente_servico_base64: str,
        confirmacao_criptografada: dict,
        nonce_esperado: str
) -> dict:
    chave_sessao = base64_para_bytes(chave_sessao_cliente_servico_base64)

    try:
        confirmacao = descriptografar_json(chave_sessao, confirmacao_criptografada)
    except Exception as erro:
        raise ValueError("Confirmacao do servico invalida.") from erro

    if confirmacao.get("nonce_autenticador") != nonce_esperado:
        raise ValueError("Confirmacao do servico invalida.")

    return confirmacao


def dados_para_hmac(mensagem: dict) -> str:
    dados = {
        "remetente": mensagem["remetente"],
        "destinatario": mensagem["destinatario"],
        "conteudo_criptografado": mensagem["conteudo_criptografado"],
        "timestamp": mensagem["timestamp"],
        "nonce": mensagem["nonce"]
    }

    return json.dumps(dados, sort_keys=True, separators=(",", ":"))


def calcular_hmac_mensagem(
        chave_sessao_cliente_servico_base64: str,
        mensagem: dict
) -> str:
    chave_sessao = base64_para_bytes(chave_sessao_cliente_servico_base64)
    dados = dados_para_hmac(mensagem).encode("utf-8")
    resumo = hmac.new(chave_sessao, dados, hashlib.sha256).digest()

    return base64.b64encode(resumo).decode("utf-8")


def verificar_hmac_mensagem(
        chave_sessao_cliente_servico_base64: str,
        mensagem: dict
) -> bool:
    hmac_calculado = calcular_hmac_mensagem(
        chave_sessao_cliente_servico_base64,
        mensagem
    )

    return hmac.compare_digest(hmac_calculado, mensagem.get("hmac", ""))


def criar_mensagem_segura(
        remetente: str,
        destinatario: str,
        conteudo: str,
        chave_sessao_cliente_servico_base64: str
) -> dict:
    chave_sessao = base64_para_bytes(chave_sessao_cliente_servico_base64)
    conteudo_criptografado = criptografar_json(
        chave_sessao,
        {"conteudo": conteudo}
    )

    mensagem = {
        "remetente": remetente,
        "destinatario": destinatario,
        "conteudo_criptografado": conteudo_criptografado,
        "timestamp": timestamp_atual(),
        "nonce": uuid.uuid4().hex
    }

    mensagem["hmac"] = calcular_hmac_mensagem(
        chave_sessao_cliente_servico_base64,
        mensagem
    )

    return mensagem


def receber_mensagem_segura(
        ticket_servico_criptografado: dict,
        mensagem: dict
) -> dict:
    ticket = validar_ticket_chat(ticket_servico_criptografado)
    chave_sessao_base64 = ticket["chave_sessao_cliente_servico"]

    if mensagem.get("remetente") != ticket["usuario"]:
        raise ValueError(ALERTA_IDENTIDADE)

    if not verificar_hmac_mensagem(chave_sessao_base64, mensagem):
        raise ValueError(ALERTA_INTEGRIDADE)

    chave_sessao = base64_para_bytes(chave_sessao_base64)
    dados = descriptografar_json(
        chave_sessao,
        mensagem["conteudo_criptografado"]
    )

    return {
        "remetente": mensagem["remetente"],
        "destinatario": mensagem["destinatario"],
        "conteudo": dados["conteudo"],
        "timestamp": mensagem["timestamp"],
        "nonce": mensagem["nonce"]
    }
