"""
@file portal_notas.py
@brief Servico de Notas protegido por Kerberos.

@details
Este modulo representa o servico protegido. Ele valida Service Tickets,
autenticadores Cliente-Servico, timestamps, nonces e hash da requisicao antes
de chamar as regras de negocio de notas. As respostas sao cifradas com a chave
de sessao Cliente-Servico para permitir autenticacao mutua.
"""

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
from kerberos_notas.logs import log_erro, log_evento, log_ok
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
    """
    @brief Calcula hash canonico de uma requisicao protegida.

    @param requisicao Dicionario com usuario, acao, dados e nonce.
    @return Digest SHA-256 hexadecimal usado no autenticador.
    """
    texto = json.dumps(
        requisicao,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def validar_ticket_portal(ticket_servico_criptografado):
    """
    @brief Abre e valida o Service Ticket destinado ao Portal de Notas.

    @param ticket_servico_criptografado Ticket cifrado pelo TGS.
    @return Ticket de servico em claro.
    @throws ValueError Quando o ticket nao foi informado ou e invalido.
    """
    if not ticket_servico_criptografado:
        log_erro("PORTAL NOTAS", "Service Ticket nao informado")
        raise ValueError("Service Ticket do Portal de Notas nao informado.")

    return abrir_ticket_servico(SERVICO_NOTAS, ticket_servico_criptografado)


def _registrar_nonce(usuario, nonce, timestamp):
    """
    @brief Registra nonce de autenticador Cliente-Servico contra replay.

    @param usuario Usuario dono do autenticador.
    @param nonce Valor unico enviado pelo cliente.
    @param timestamp Timestamp do autenticador validado.
    @throws ValueError Quando o nonce esta ausente ou ja foi usado.
    """
    if not nonce:
        log_erro(
            "PORTAL NOTAS",
            "Autenticador Cliente-Servico sem nonce",
            {"usuario": usuario},
        )
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
            log_erro(
                "PORTAL NOTAS",
                "Autenticador Cliente-Servico reutilizado",
                {"usuario": usuario, "nonce": nonce},
            )
            raise ValueError("Autenticador reutilizado: possivel ataque de replay.")

        NONCES_UTILIZADOS[chave_nonce] = timestamp
    log_ok(
        "PORTAL NOTAS",
        "Nonce Cliente-Servico registrado contra replay",
        {"usuario": usuario, "nonce": nonce, "timestamp": timestamp},
    )


def _validar_autenticador_portal(ticket, autenticador_criptografado):
    """
    @brief Valida autenticador Cliente-Servico usando a chave do ticket.

    @param ticket Service Ticket ja aberto.
    @param autenticador_criptografado Autenticador cifrado pelo cliente.
    @return Autenticador em claro.
    @throws ValueError Para autenticador invalido, expirado, futuro ou reutilizado.
    """
    log_evento(
        "PORTAL NOTAS",
        "Validando autenticador Cliente-Servico",
        {
            "usuario_ticket": ticket.get("usuario"),
            "autenticador": autenticador_criptografado,
        },
    )
    chave_sessao_base64 = ticket["chave_sessao_cliente_servico"]

    try:
        autenticador = abrir_autenticador(
            chave_sessao_base64,
            autenticador_criptografado,
        )
    except Exception as erro:
        log_erro(
            "PORTAL NOTAS",
            "Autenticador Cliente-Servico invalido",
            {"usuario_ticket": ticket.get("usuario"), "erro": str(erro)},
        )
        raise ValueError("Autenticador Cliente-Servico invalido.") from erro

    if autenticador.get("usuario") != ticket.get("usuario"):
        log_erro(
            "PORTAL NOTAS",
            "Autenticador pertence a outro usuario",
            {
                "usuario_ticket": ticket.get("usuario"),
                "usuario_autenticador": autenticador.get("usuario"),
            },
        )
        raise ValueError("Autenticador pertence a outro usuario.")

    timestamp = autenticador.get("timestamp")
    if timestamp is None:
        log_erro("PORTAL NOTAS", "Autenticador Cliente-Servico sem timestamp")
        raise ValueError("Autenticador Cliente-Servico sem timestamp.")

    if ticket_expirou(timestamp, TEMPO_MAXIMO_AUTENTICADOR):
        log_erro(
            "PORTAL NOTAS",
            "Autenticador Cliente-Servico expirado",
            {"usuario": ticket.get("usuario"), "timestamp": timestamp},
        )
        raise ValueError("Autenticador Cliente-Servico expirado.")

    if timestamp > timestamp_atual() + TEMPO_MAXIMO_AUTENTICADOR:
        log_erro(
            "PORTAL NOTAS",
            "Autenticador Cliente-Servico com timestamp futuro invalido",
            {"usuario": ticket.get("usuario"), "timestamp": timestamp},
        )
        raise ValueError("Autenticador Cliente-Servico com timestamp invalido.")

    _registrar_nonce(ticket["usuario"], autenticador.get("nonce"), timestamp)
    log_ok(
        "PORTAL NOTAS",
        "Autenticador Cliente-Servico validado",
        autenticador,
    )
    return autenticador


def autenticar_portal_notas(
        ticket_servico_criptografado,
        autenticador_criptografado
):
    """
    @brief Realiza a autenticacao inicial Cliente-Servico no Portal.

    @param ticket_servico_criptografado Service Ticket emitido pelo TGS.
    @param autenticador_criptografado Autenticador cifrado com a chave Cliente-Servico.
    @return Confirmacao cifrada com timestamp incrementado e nonce do autenticador.
    """
    log_evento(
        "PORTAL NOTAS",
        "Recebida autenticacao inicial Cliente-Servico",
        {
            "ticket_servico": ticket_servico_criptografado,
            "autenticador": autenticador_criptografado,
        },
    )
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

    confirmacao_cifrada = criptografar_json(chave_sessao, confirmacao)
    log_ok(
        "PORTAL NOTAS",
        "Autenticacao mutua respondida com confirmacao cifrada",
        {
            "confirmacao": confirmacao,
            "confirmacao_cifrada": confirmacao_cifrada,
        },
    )
    return confirmacao_cifrada


def validar_confirmacao_portal(
        chave_sessao_cliente_servico_base64,
        confirmacao_criptografada,
        timestamp_esperado,
        nonce_esperado
):
    """
    @brief Valida a resposta de autenticacao mutua enviada pelo Portal.

    @param chave_sessao_cliente_servico_base64 Chave Cliente-Servico.
    @param confirmacao_criptografada Confirmacao cifrada pelo servico.
    @param timestamp_esperado Timestamp original do autenticador.
    @param nonce_esperado Nonce original do autenticador.
    @return Confirmacao em claro se a autenticacao mutua for valida.
    """
    log_evento(
        "CLIENTE WEB",
        "Validando confirmacao de autenticacao mutua do Portal",
        {
            "timestamp_esperado": timestamp_esperado,
            "nonce_esperado": nonce_esperado,
            "confirmacao_criptografada": confirmacao_criptografada,
        },
    )
    chave_sessao = base64_para_bytes(chave_sessao_cliente_servico_base64)

    try:
        confirmacao = descriptografar_json(
            chave_sessao,
            confirmacao_criptografada,
        )
    except Exception as erro:
        log_erro(
            "CLIENTE WEB",
            "Confirmacao do Portal nao pode ser aberta",
            {"erro": str(erro)},
        )
        raise ValueError("Confirmacao do Portal de Notas invalida.") from erro

    if confirmacao.get("servico") != SERVICO_NOTAS:
        log_erro(
            "CLIENTE WEB",
            "Confirmacao foi emitida por outro servico",
            {"confirmacao": confirmacao},
        )
        raise ValueError("Confirmacao emitida por outro servico.")

    if confirmacao.get("timestamp_resposta") != timestamp_esperado + 1:
        log_erro(
            "CLIENTE WEB",
            "Timestamp da autenticacao mutua invalido",
            {"confirmacao": confirmacao, "timestamp_esperado": timestamp_esperado},
        )
        raise ValueError("Timestamp da autenticacao mutua invalido.")

    if confirmacao.get("nonce_autenticador") != nonce_esperado:
        log_erro(
            "CLIENTE WEB",
            "Nonce da autenticacao mutua invalido",
            {"confirmacao": confirmacao, "nonce_esperado": nonce_esperado},
        )
        raise ValueError("Nonce da autenticacao mutua invalido.")

    log_ok(
        "CLIENTE WEB",
        "Confirmacao de autenticacao mutua validada",
        confirmacao,
    )
    return confirmacao


def _executar_acao(usuario, acao, dados):
    """
    @brief Executa a regra de negocio depois da validacao Kerberos.

    @param usuario Usuario autenticado pelo Service Ticket.
    @param acao Nome da operacao solicitada.
    @param dados Dados da operacao.
    @return Resultado da acao de notas.
    @throws ValueError Quando a operacao nao existe.
    @throws PermissionError Quando o perfil nao pode alterar notas.
    """
    perfil = obter_perfil_usuario(usuario)
    log_evento(
        "SERVICO NOTAS",
        "Executando regra de negocio solicitada pelo Portal",
        {
            "usuario": usuario,
            "perfil": perfil,
            "acao": acao,
            "dados": dados,
        },
    )

    if acao == "carregar_painel":
        resultado = {
            "perfil": perfil,
            "notas": listar_notas(usuario, perfil),
            "alunos": listar_alunos() if perfil == PERFIL_PROFESSOR else [],
        }
        log_ok("SERVICO NOTAS", "Painel carregado", {
            "perfil": resultado["perfil"],
            "quantidade_notas": len(resultado["notas"]),
            "quantidade_alunos": len(resultado["alunos"]),
        })
        return resultado

    if acao == "criar_nota":
        resultado = criar_nota(
            professor=usuario,
            perfil=perfil,
            aluno=dados.get("aluno"),
            disciplina=dados.get("disciplina"),
            nota=dados.get("nota"),
            observacao=dados.get("observacao"),
        )
        log_ok("SERVICO NOTAS", "Nota criada", resultado)
        return resultado

    if acao == "criar_notas":
        resultado = criar_notas(
            professor=usuario,
            perfil=perfil,
            aluno=dados.get("aluno"),
            notas=dados.get("notas"),
        )
        log_ok(
            "SERVICO NOTAS",
            "Notas criadas em lote",
            {"quantidade": len(resultado), "notas": resultado},
        )
        return resultado

    if acao == "editar_nota":
        resultado = editar_nota(
            professor=usuario,
            perfil=perfil,
            nota_id=dados.get("nota_id"),
            disciplina=dados.get("disciplina"),
            nota=dados.get("nota"),
            observacao=dados.get("observacao"),
        )
        log_ok("SERVICO NOTAS", "Nota editada", resultado)
        return resultado

    if acao == "excluir_nota":
        resultado = excluir_nota(
            dados.get("nota_id"),
            perfil=perfil,
        )
        log_ok("SERVICO NOTAS", "Nota excluida", resultado)
        return resultado

    log_erro(
        "SERVICO NOTAS",
        "Operacao desconhecida solicitada",
        {"usuario": usuario, "acao": acao},
    )
    raise ValueError("Operacao desconhecida no Portal de Notas.")


def processar_operacao_portal(
        ticket_servico_criptografado,
        autenticador_criptografado,
        requisicao_criptografada
):
    """
    @brief Processa uma operacao de notas protegida por Kerberos.

    @param ticket_servico_criptografado Service Ticket do usuario.
    @param autenticador_criptografado Autenticador amarrado a acao e requisicao.
    @param requisicao_criptografada Requisicao cifrada com a chave Cliente-Servico.
    @return Resposta cifrada com o resultado da operacao.
    @throws ValueError Quando ticket, autenticador, nonce, acao ou hash falham.
    """
    log_evento(
        "PORTAL NOTAS",
        "Recebida operacao protegida por Kerberos",
        {
            "ticket_servico": ticket_servico_criptografado,
            "autenticador": autenticador_criptografado,
            "requisicao_criptografada": requisicao_criptografada,
        },
    )
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
        log_erro(
            "PORTAL NOTAS",
            "Requisicao protegida invalida ou adulterada",
            {"usuario": ticket.get("usuario"), "erro": str(erro)},
        )
        raise ValueError("Requisicao protegida invalida ou adulterada.") from erro

    log_evento(
        "PORTAL NOTAS",
        "Requisicao protegida descriptografada",
        requisicao,
    )
    if requisicao.get("usuario") != ticket["usuario"]:
        log_erro(
            "PORTAL NOTAS",
            "Usuario da requisicao diferente do Service Ticket",
            {
                "usuario_ticket": ticket["usuario"],
                "usuario_requisicao": requisicao.get("usuario"),
            },
        )
        raise ValueError("Usuario da requisicao diferente do Service Ticket.")

    if requisicao.get("nonce") != autenticador.get("nonce"):
        log_erro(
            "PORTAL NOTAS",
            "Nonce da requisicao diferente do autenticador",
            {
                "nonce_requisicao": requisicao.get("nonce"),
                "nonce_autenticador": autenticador.get("nonce"),
            },
        )
        raise ValueError("Nonce da requisicao diferente do autenticador.")

    acao = requisicao.get("acao")
    if acao != autenticador.get("acao"):
        log_erro(
            "PORTAL NOTAS",
            "Acao da requisicao diferente do autenticador",
            {"acao_requisicao": acao, "acao_autenticador": autenticador.get("acao")},
        )
        raise ValueError("Acao da requisicao diferente do autenticador.")

    hash_calculado = calcular_hash_requisicao(requisicao)
    if not hmac.compare_digest(
        hash_calculado,
        autenticador.get("hash_requisicao", ""),
    ):
        log_erro(
            "PORTAL NOTAS",
            "Hash da requisicao nao corresponde ao autenticador",
            {
                "hash_calculado": hash_calculado,
                "hash_autenticador": autenticador.get("hash_requisicao", ""),
            },
        )
        raise ValueError("Requisicao nao corresponde ao autenticador.")

    log_ok(
        "PORTAL NOTAS",
        "Ticket, autenticador, nonce, acao e hash da requisicao validados",
        {
            "usuario": ticket["usuario"],
            "acao": acao,
            "hash_requisicao": hash_calculado,
        },
    )
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
    resposta_cifrada = criptografar_json(chave_sessao, resposta)
    log_ok(
        "PORTAL NOTAS",
        "Resposta da operacao cifrada para o cliente",
        {
            "resposta": resposta,
            "resposta_cifrada": resposta_cifrada,
        },
    )
    return resposta_cifrada


def validar_resposta_operacao(
        chave_sessao_cliente_servico_base64,
        resposta_criptografada,
        acao_esperada,
        timestamp_esperado,
        nonce_esperado
):
    """
    @brief Valida a resposta cifrada do Portal para uma operacao.

    @param chave_sessao_cliente_servico_base64 Chave Cliente-Servico.
    @param resposta_criptografada Resposta cifrada pelo Portal.
    @param acao_esperada Acao que o cliente executou.
    @param timestamp_esperado Timestamp do autenticador enviado.
    @param nonce_esperado Nonce usado na operacao.
    @return Resposta em claro validada.
    """
    log_evento(
        "CLIENTE WEB",
        "Validando resposta cifrada da operacao",
        {
            "acao_esperada": acao_esperada,
            "timestamp_esperado": timestamp_esperado,
            "nonce_esperado": nonce_esperado,
            "resposta_criptografada": resposta_criptografada,
        },
    )
    chave_sessao = base64_para_bytes(chave_sessao_cliente_servico_base64)

    try:
        resposta = descriptografar_json(chave_sessao, resposta_criptografada)
    except Exception as erro:
        log_erro(
            "CLIENTE WEB",
            "Resposta da operacao nao pode ser aberta",
            {"acao_esperada": acao_esperada, "erro": str(erro)},
        )
        raise ValueError("Resposta da operacao invalida.") from erro

    if resposta.get("acao") != acao_esperada:
        log_erro(
            "CLIENTE WEB",
            "Resposta pertence a outra operacao",
            {"acao_esperada": acao_esperada, "resposta": resposta},
        )
        raise ValueError("Resposta pertence a outra operacao.")

    if resposta.get("timestamp_resposta") != timestamp_esperado + 1:
        log_erro(
            "CLIENTE WEB",
            "Timestamp da resposta da operacao invalido",
            {"timestamp_esperado": timestamp_esperado, "resposta": resposta},
        )
        raise ValueError("Timestamp da resposta da operacao invalido.")

    if resposta.get("nonce_autenticador") != nonce_esperado:
        log_erro(
            "CLIENTE WEB",
            "Nonce da resposta da operacao invalido",
            {"nonce_esperado": nonce_esperado, "resposta": resposta},
        )
        raise ValueError("Nonce da resposta da operacao invalido.")

    if resposta.get("status") != "operacao_concluida":
        log_erro(
            "CLIENTE WEB",
            "Portal nao confirmou conclusao da operacao",
            resposta,
        )
        raise ValueError("Operacao nao foi confirmada pelo Portal.")

    log_ok(
        "CLIENTE WEB",
        "Resposta da operacao validada",
        resposta,
    )
    return resposta
