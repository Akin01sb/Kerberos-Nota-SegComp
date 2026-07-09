import hashlib
import hmac
import json
from threading import RLock

from kerberos_notas.crypto.crypto_utils import (
    base64_para_bytes,
    criptografar_json,
    descriptografar_json,
)
from kerberos_notas.kerberos.authenticator import abrir_autenticador
from kerberos_notas.kerberos.tgs_server import abrir_ticket_servico
from kerberos_notas.kerberos.tickets import ticket_expirou, timestamp_atual
from kerberos_notas.notes.service import (
    PERFIL_PROFESSOR,
    criar_nota,
    criar_notas,
    editar_nota,
    excluir_nota,
    listar_alunos,
    listar_notas,
    obter_perfil_usuario,
)


SERVICO_NOTAS = "notas"
TEMPO_MAXIMO_AUTENTICADOR = 60 * 5
NONCES_UTILIZADOS = {}
BLOQUEIO_NONCES = RLock()


def calcular_hash_requisicao(requisicao):
    texto = json.dumps(
        requisicao,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def validar_ticket_portal(ticket_servico_criptografado):
    if not ticket_servico_criptografado:
        raise ValueError("Service Ticket do Portal de Notas nao informado.")

    return abrir_ticket_servico(SERVICO_NOTAS, ticket_servico_criptografado)


def _registrar_nonce(usuario, nonce, timestamp):
    if not nonce:
        raise ValueError("Autenticador Cliente-Servico sem nonce.")

    with BLOQUEIO_NONCES:
        limite = timestamp_atual() - TEMPO_MAXIMO_AUTENTICADOR
        expirados = [
            chave
            for chave, momento in NONCES_UTILIZADOS.items()
            if momento < limite
        ]
        for chave in expirados:
            NONCES_UTILIZADOS.pop(chave, None)

        chave_nonce = (usuario, nonce)
        if chave_nonce in NONCES_UTILIZADOS:
            raise ValueError("Autenticador reutilizado: possivel ataque de replay.")

        NONCES_UTILIZADOS[chave_nonce] = timestamp


def _validar_autenticador_portal(ticket, autenticador_criptografado):
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

    _registrar_nonce(ticket["usuario"], autenticador.get("nonce"), timestamp)
    return autenticador


def autenticar_portal_notas(
        ticket_servico_criptografado,
        autenticador_criptografado
):
    ticket = validar_ticket_portal(ticket_servico_criptografado)
    autenticador = _validar_autenticador_portal(
        ticket,
        autenticador_criptografado,
    )
    chave_sessao = base64_para_bytes(
        ticket["chave_sessao_cliente_servico"]
    )

    confirmacao = {
        "usuario": ticket["usuario"],
        "servico": SERVICO_NOTAS,
        "timestamp_resposta": autenticador["timestamp"] + 1,
        "nonce_autenticador": autenticador["nonce"],
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


def _executar_acao(usuario, acao, dados):
    perfil = obter_perfil_usuario(usuario)

    if acao == "carregar_painel":
        return {
            "perfil": perfil,
            "notas": listar_notas(usuario, perfil),
            "alunos": listar_alunos() if perfil == PERFIL_PROFESSOR else [],
        }

    if acao == "criar_nota":
        return criar_nota(
            professor=usuario,
            perfil=perfil,
            aluno=dados.get("aluno"),
            disciplina=dados.get("disciplina"),
            nota=dados.get("nota"),
            observacao=dados.get("observacao"),
        )

    if acao == "criar_notas":
        return criar_notas(
            professor=usuario,
            perfil=perfil,
            aluno=dados.get("aluno"),
            notas=dados.get("notas"),
        )

    if acao == "editar_nota":
        return editar_nota(
            professor=usuario,
            perfil=perfil,
            nota_id=dados.get("nota_id"),
            disciplina=dados.get("disciplina"),
            nota=dados.get("nota"),
            observacao=dados.get("observacao"),
        )

    if acao == "excluir_nota":
        return excluir_nota(
            dados.get("nota_id"),
            perfil=perfil,
        )

    raise ValueError("Operacao desconhecida no Portal de Notas.")


def processar_operacao_portal(
        ticket_servico_criptografado,
        autenticador_criptografado,
        requisicao_criptografada
):
    ticket = validar_ticket_portal(ticket_servico_criptografado)
    autenticador = _validar_autenticador_portal(
        ticket,
        autenticador_criptografado,
    )
    chave_sessao_base64 = ticket["chave_sessao_cliente_servico"]
    chave_sessao = base64_para_bytes(chave_sessao_base64)

    try:
        requisicao = descriptografar_json(
            chave_sessao,
            requisicao_criptografada,
        )
    except Exception as erro:
        raise ValueError("Requisicao protegida invalida ou adulterada.") from erro

    if requisicao.get("usuario") != ticket["usuario"]:
        raise ValueError("Usuario da requisicao diferente do Service Ticket.")

    if requisicao.get("nonce") != autenticador.get("nonce"):
        raise ValueError("Nonce da requisicao diferente do autenticador.")

    acao = requisicao.get("acao")
    if acao != autenticador.get("acao"):
        raise ValueError("Acao da requisicao diferente do autenticador.")

    hash_calculado = calcular_hash_requisicao(requisicao)
    if not hmac.compare_digest(
        hash_calculado,
        autenticador.get("hash_requisicao", ""),
    ):
        raise ValueError("Requisicao nao corresponde ao autenticador.")

    resultado = _executar_acao(
        ticket["usuario"],
        acao,
        requisicao.get("dados", {}),
    )

    resposta = {
        "status": "operacao_concluida",
        "acao": acao,
        "timestamp_resposta": autenticador["timestamp"] + 1,
        "nonce_autenticador": autenticador["nonce"],
        "resultado": resultado,
    }
    return criptografar_json(chave_sessao, resposta)


def validar_resposta_operacao(
        chave_sessao_cliente_servico_base64,
        resposta_criptografada,
        acao_esperada,
        timestamp_esperado,
        nonce_esperado
):
    chave_sessao = base64_para_bytes(chave_sessao_cliente_servico_base64)

    try:
        resposta = descriptografar_json(chave_sessao, resposta_criptografada)
    except Exception as erro:
        raise ValueError("Resposta da operacao invalida.") from erro

    if resposta.get("acao") != acao_esperada:
        raise ValueError("Resposta pertence a outra operacao.")

    if resposta.get("timestamp_resposta") != timestamp_esperado + 1:
        raise ValueError("Timestamp da resposta da operacao invalido.")

    if resposta.get("nonce_autenticador") != nonce_esperado:
        raise ValueError("Nonce da resposta da operacao invalido.")

    if resposta.get("status") != "operacao_concluida":
        raise ValueError("Operacao nao foi confirmada pelo Portal.")

    return resposta
