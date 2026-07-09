from kerberos_notas.crypto.crypto_utils import (
    base64_para_bytes,
    criptografar_json,
    descriptografar_json,
)
from kerberos_notas.kerberos.authenticator import abrir_autenticador
from kerberos_notas.kerberos.tgs_server import abrir_ticket_servico
from kerberos_notas.kerberos.tickets import ticket_expirou, timestamp_atual


SERVICO_NOTAS = "notas"
TEMPO_MAXIMO_AUTENTICADOR = 60 * 5


def validar_ticket_portal(ticket_servico_criptografado):
    if not ticket_servico_criptografado:
        raise ValueError("Service Ticket do Portal de Notas nao informado.")

    return abrir_ticket_servico(SERVICO_NOTAS, ticket_servico_criptografado)


def autenticar_portal_notas(
        ticket_servico_criptografado,
        autenticador_criptografado
):
    ticket = validar_ticket_portal(ticket_servico_criptografado)
    chave_sessao_base64 = ticket["chave_sessao_cliente_servico"]

    try:
        autenticador = abrir_autenticador(
            chave_sessao_base64,
            autenticador_criptografado,
        )
    except Exception as erro:
        raise ValueError("Autenticador Cliente-Servico invalido.") from erro

    if autenticador.get("usuario") != ticket.get("usuario"):
        raise ValueError("Autenticador pertence a outro usuario.")

    timestamp = autenticador.get("timestamp")
    if timestamp is None:
        raise ValueError("Autenticador Cliente-Servico sem timestamp.")

    if ticket_expirou(timestamp, TEMPO_MAXIMO_AUTENTICADOR):
        raise ValueError("Autenticador Cliente-Servico expirado.")

    if timestamp > timestamp_atual() + TEMPO_MAXIMO_AUTENTICADOR:
        raise ValueError("Autenticador Cliente-Servico com timestamp invalido.")

    chave_sessao = base64_para_bytes(chave_sessao_base64)
    confirmacao = {
        "usuario": ticket["usuario"],
        "servico": SERVICO_NOTAS,
        "timestamp_resposta": timestamp + 1,
        "nonce_autenticador": autenticador.get("nonce"),
        "status": "portal_autenticado",
    }

    return criptografar_json(chave_sessao, confirmacao)


def validar_confirmacao_portal(
        chave_sessao_cliente_servico_base64,
        confirmacao_criptografada,
        timestamp_esperado,
        nonce_esperado
):
    chave_sessao = base64_para_bytes(chave_sessao_cliente_servico_base64)

    try:
        confirmacao = descriptografar_json(
            chave_sessao,
            confirmacao_criptografada,
        )
    except Exception as erro:
        raise ValueError("Confirmacao do Portal de Notas invalida.") from erro

    if confirmacao.get("servico") != SERVICO_NOTAS:
        raise ValueError("Confirmacao emitida por outro servico.")

    if confirmacao.get("timestamp_resposta") != timestamp_esperado + 1:
        raise ValueError("Timestamp da autenticacao mutua invalido.")

    if confirmacao.get("nonce_autenticador") != nonce_esperado:
        raise ValueError("Nonce da autenticacao mutua invalido.")

    return confirmacao
