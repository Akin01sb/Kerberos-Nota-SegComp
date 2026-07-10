"""
@file routes.py
@brief Aplicacao Flask que atua como cliente Kerberos.

@details
As rotas web recebem usuario e senha, coordenam o fluxo Cliente-AS-TGS-Servico
e mantem no servidor Flask os tickets e chaves de sessao. Cada acao do Portal
de Notas cria novo autenticador, cifra a requisicao e valida a resposta cifrada
do servico.
"""

import os
import secrets
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, session, url_for

from kerberos_notas.crypto.crypto_utils import (
    base64_para_bytes,
    criptografar_json,
    descriptografar_json,
)
from kerberos_notas.crypto.kdf import derivar_chave_senha
from kerberos_notas.crypto.kdf import (
    ITERACOES_PBKDF2,
    gerar_prova_as,
    obter_chave_autenticacao_as,
)
from kerberos_notas.kerberos.as_server import (
    autenticar_no_as_com_prova,
    criar_desafio_as,
)
from kerberos_notas.kerberos.authenticator import abrir_autenticador, criar_autenticador
from kerberos_notas.kerberos.tgs_server import emitir_ticket_servico
from kerberos_notas.logs import log_evento, log_ok, log_titulo, registrar_log_interface
from kerberos_notas.notes.portal_notas import (
    autenticar_portal_notas,
    calcular_hash_requisicao,
    processar_operacao_portal,
    validar_confirmacao_portal,
    validar_resposta_operacao,
    validar_ticket_portal,
)
from kerberos_notas.notes.service import obter_perfil_usuario
from kerberos_notas.rede.cliente_tcp import ClienteKerberosTCP


BASE_DIR = Path(__file__).resolve().parents[3]


def _normalizar_componente(mensagem, componente):
    if componente:
        return componente, mensagem

    if mensagem.startswith("[") and "]" in mensagem:
        marcador, texto = mensagem.split("]", 1)
        marcador = marcador.strip("[]")
        componentes = {
            "CLIENTE": "CLIENTE WEB",
            "AS": "AS",
            "TGS": "TGS",
            "PORTAL": "PORTAL NOTAS",
        }
        return componentes.get(marcador, marcador), texto.strip()

    return "CLIENTE WEB", mensagem


def registrar_etapa(logs, mensagem, componente=None, status=None, dados=None):
    """
    @brief Registra uma etapa do fluxo para exibicao e depuracao.

    @param logs Lista de mensagens da sessao.
    @param mensagem Texto a ser registrado.
    """
    componente, mensagem = _normalizar_componente(mensagem, componente)
    registrar_log_interface(
        logs,
        componente,
        mensagem,
        status=status,
        dados=dados,
    )
    log_evento(componente, mensagem, dados=dados, nivel=status)


def autenticar_com_kerberos(
        usuario,
        senha,
        usar_rede=True,
        cliente_tcp=None
):
    """
    @brief Executa o fluxo completo Cliente-AS-TGS-Portal.

    @param usuario Usuario informado no login.
    @param senha Senha usada localmente para derivar a chave do cliente.
    @param usar_rede Define se AS, TGS e Notas serao chamados por TCP.
    @param cliente_tcp Cliente TCP injetavel para testes.
    @return Dados de sessao Kerberos mantidos no servidor Flask.
    @throws ValueError Quando qualquer validacao Kerberos falha.
    """
    logs = []
    log_titulo("CLIENTE WEB", "Iniciando fluxo Kerberos completo")
    log_evento(
        "CLIENTE WEB",
        "ETAPA 1 - Usuario informou login e senha",
        {
            "usuario": usuario,
            "senha_informada": bool(senha),
            "usar_rede": usar_rede,
        },
    )
    registrar_etapa(
        logs,
        "Login recebido pelo Cliente Web",
        componente="CLIENTE WEB",
        status="ETAPA 1",
        dados={
            "usuario": usuario,
            "senha_informada": bool(senha),
            "usar_rede": usar_rede,
        },
    )
    registrar_etapa(logs, "[CLIENTE] Senha informada localmente pelo usuario.")
    registrar_etapa(logs, "[CLIENTE] Solicitando autenticacao ao AS.")

    cliente_tcp = cliente_tcp or ClienteKerberosTCP()
    if usar_rede:
        parametros_as = cliente_tcp.solicitar_parametros_as(usuario)
    else:
        parametros_as = criar_desafio_as(usuario)
    log_evento(
        "CLIENTE WEB",
        "ETAPA 2 - Parametros do AS recebidos",
        {
            "usuario": parametros_as.get("usuario"),
            "salt": parametros_as.get("salt"),
            "iteracoes_kdf": parametros_as.get("iteracoes_kdf"),
            "desafio": parametros_as.get("desafio"),
        },
    )
    registrar_etapa(
        logs,
        "Parametros de desafio recebidos do AS",
        componente="AS",
        status="OK",
        dados={
            "usuario": parametros_as.get("usuario"),
            "salt": parametros_as.get("salt"),
            "iteracoes_kdf": parametros_as.get("iteracoes_kdf"),
            "desafio": parametros_as.get("desafio"),
        },
    )

    if parametros_as.get("iteracoes_kdf") != ITERACOES_PBKDF2:
        raise ValueError("Parametros KDF recebidos do AS sao invalidos.")

    chave_derivada = derivar_chave_senha(senha, parametros_as["salt"])
    chave_cliente = obter_chave_autenticacao_as(chave_derivada)
    log_ok(
        "CLIENTE WEB",
        "Chave do cliente derivada localmente com PBKDF2-HMAC-SHA256",
        {
            "usuario": usuario,
            "tamanho_chave_derivada_bytes": len(chave_derivada),
            "tamanho_chave_as_bytes": len(chave_cliente),
        },
    )
    registrar_etapa(
        logs,
        "KDF executada localmente para obter a chave do cliente",
        componente="CLIENTE WEB",
        status="OK",
        dados={
            "algoritmo": "PBKDF2-HMAC-SHA256",
            "iteracoes": ITERACOES_PBKDF2,
            "tamanho_chave_derivada_bytes": len(chave_derivada),
            "tamanho_chave_as_bytes": len(chave_cliente),
        },
    )
    prova = gerar_prova_as(
        chave_cliente,
        usuario,
        parametros_as["desafio"],
    )
    log_evento(
        "CLIENTE WEB",
        "ETAPA 3 - Prova HMAC criada para o desafio do AS",
        {
            "usuario": usuario,
            "desafio": parametros_as["desafio"],
            "prova": prova,
        },
    )
    registrar_etapa(
        logs,
        "Prova HMAC preparada para envio ao AS",
        componente="CLIENTE WEB",
        status="OK",
        dados={
            "usuario": usuario,
            "desafio": parametros_as["desafio"],
            "prova": prova,
        },
    )
    if usar_rede:
        resposta_as_criptografada = cliente_tcp.enviar_prova_as(
            usuario,
            parametros_as["desafio"],
            prova,
        )
    else:
        resposta_as_criptografada = autenticar_no_as_com_prova(
            usuario,
            parametros_as["desafio"],
            prova,
        )
    log_evento(
        "CLIENTE WEB",
        "AS-REP cifrado recebido",
        {"resposta_as_criptografada": resposta_as_criptografada},
    )
    registrar_etapa(
        logs,
        "AS validou a prova e devolveu AS-REP cifrado",
        componente="AS",
        status="OK",
        dados={"resposta_as_criptografada": resposta_as_criptografada},
    )
    registrar_etapa(
        logs,
        "[AS] Prova criptografica do usuario validada.",
    )

    registrar_etapa(logs, "[AS] TGT emitido com sucesso.")
    registrar_etapa(logs, "[CLIENTE] Chave derivada com PBKDF2-HMAC-SHA256.")

    resposta_as = descriptografar_json(chave_cliente, resposta_as_criptografada)
    log_evento(
        "CLIENTE WEB",
        "AS-REP descriptografado pelo cliente",
        {
            "id_tgs": resposta_as.get("id_tgs"),
            "chave_sessao_cliente_tgs": resposta_as.get(
                "chave_sessao_cliente_tgs"
            ),
            "tgt": resposta_as.get("tgt"),
            "timestamp_emissao": resposta_as.get("timestamp_emissao"),
            "timestamp_expiracao": resposta_as.get("timestamp_expiracao"),
            "validade_segundos": resposta_as.get("validade_segundos"),
            "nonce_tgt": resposta_as.get("nonce_tgt"),
        },
    )
    registrar_etapa(
        logs,
        "Cliente abriu AS-REP e recebeu TGT transportavel",
        componente="CLIENTE WEB",
        status="OK",
        dados={
            "id_tgs": resposta_as.get("id_tgs"),
            "chave_sessao_cliente_tgs": resposta_as.get(
                "chave_sessao_cliente_tgs"
            ),
            "tgt": resposta_as.get("tgt"),
            "timestamp_expiracao": resposta_as.get("timestamp_expiracao"),
        },
    )
    chave_sessao_cliente_tgs = resposta_as["chave_sessao_cliente_tgs"]
    autenticador_tgs = criar_autenticador(usuario, chave_sessao_cliente_tgs)
    log_evento(
        "CLIENTE WEB",
        "ETAPA 4 - Autenticador Cliente-TGS criado",
        {"autenticador_tgs": autenticador_tgs},
    )
    registrar_etapa(
        logs,
        "TGT e autenticador Cliente-TGS preparados para o TGS",
        componente="CLIENTE WEB",
        status="ETAPA 4",
        dados={
            "usuario": usuario,
            "servico_destino": "notas",
            "tgt": resposta_as["tgt"],
            "autenticador_tgs": autenticador_tgs,
        },
    )
    registrar_etapa(logs, "[CLIENTE] Autenticador Cliente-TGS criado.")

    if usar_rede:
        resposta_tgs = cliente_tcp.solicitar_ticket_servico(
            usuario,
            "notas",
            resposta_as["tgt"],
            autenticador_tgs,
        )
    else:
        resposta_tgs = emitir_ticket_servico(
            usuario=usuario,
            servico="notas",
            tgt_criptografado=resposta_as["tgt"],
            autenticador_criptografado=autenticador_tgs,
        )
    log_evento(
        "CLIENTE WEB",
        "TGS-REP recebido",
        {
            "servico": resposta_tgs.get("servico"),
            "ticket_servico": resposta_tgs.get("ticket_servico"),
            "resposta_cliente": resposta_tgs.get("resposta_cliente"),
        },
    )
    registrar_etapa(
        logs,
        "TGS validou TGT/autenticador e emitiu Service Ticket",
        componente="TGS",
        status="OK",
        dados={
            "servico": resposta_tgs.get("servico"),
            "ticket_servico": resposta_tgs.get("ticket_servico"),
            "resposta_cliente": resposta_tgs.get("resposta_cliente"),
        },
    )
    registrar_etapa(logs, "[TGS] TGT e autenticador Cliente-TGS validados.")
    registrar_etapa(logs, "[TGS] Service Ticket para o Portal de Notas emitido.")

    dados_cliente = descriptografar_json(
        base64_para_bytes(chave_sessao_cliente_tgs),
        resposta_tgs["resposta_cliente"],
    )
    log_evento(
        "CLIENTE WEB",
        "Resposta do TGS aberta pelo cliente",
        {
            "usuario": dados_cliente.get("usuario"),
            "servico": dados_cliente.get("servico"),
            "chave_sessao_cliente_servico": dados_cliente.get(
                "chave_sessao_cliente_servico"
            ),
            "timestamp_emissao": dados_cliente.get("timestamp_emissao"),
            "timestamp_expiracao": dados_cliente.get("timestamp_expiracao"),
            "nonce_ticket": dados_cliente.get("nonce_ticket"),
        },
    )
    registrar_etapa(
        logs,
        "Cliente abriu resposta do TGS e obteve chave Cliente-Servico",
        componente="CLIENTE WEB",
        status="OK",
        dados={
            "usuario": dados_cliente.get("usuario"),
            "servico": dados_cliente.get("servico"),
            "chave_sessao_cliente_servico": dados_cliente.get(
                "chave_sessao_cliente_servico"
            ),
            "timestamp_expiracao": dados_cliente.get("timestamp_expiracao"),
            "nonce_ticket": dados_cliente.get("nonce_ticket"),
        },
    )
    chave_sessao_servico = dados_cliente["chave_sessao_cliente_servico"]

    nonce_portal = secrets.token_hex(16)
    autenticador_portal = criar_autenticador(
        usuario,
        chave_sessao_servico,
        nonce=nonce_portal,
    )
    dados_autenticador = abrir_autenticador(
        chave_sessao_servico,
        autenticador_portal,
    )
    log_evento(
        "CLIENTE WEB",
        "ETAPA 5 - Service Ticket e autenticador preparados para o Portal",
        {
            "ticket_servico": resposta_tgs["ticket_servico"],
            "autenticador_portal": autenticador_portal,
            "dados_autenticador": dados_autenticador,
        },
    )
    registrar_etapa(
        logs,
        "Service Ticket e autenticador Cliente-Servico preparados para o Portal",
        componente="CLIENTE WEB",
        status="ETAPA 5",
        dados={
            "ticket_servico": resposta_tgs["ticket_servico"],
            "autenticador_portal": autenticador_portal,
            "timestamp_autenticador": dados_autenticador.get("timestamp"),
            "nonce_portal": nonce_portal,
        },
    )
    registrar_etapa(logs, "[CLIENTE] Service Ticket e autenticador enviados ao Portal.")

    if usar_rede:
        confirmacao_portal = cliente_tcp.autenticar_portal(
            resposta_tgs["ticket_servico"],
            autenticador_portal,
        )
    else:
        confirmacao_portal = autenticar_portal_notas(
            resposta_tgs["ticket_servico"],
            autenticador_portal,
        )
    log_evento(
        "CLIENTE WEB",
        "Confirmacao cifrada do Portal recebida",
        {"confirmacao_portal": confirmacao_portal},
    )
    registrar_etapa(
        logs,
        "Portal recebeu Service Ticket e devolveu confirmacao cifrada",
        componente="PORTAL NOTAS",
        status="OK",
        dados={"confirmacao_portal": confirmacao_portal},
    )
    registrar_etapa(logs, "[PORTAL] Service Ticket validado.")
    registrar_etapa(logs, "[PORTAL] Autenticador Cliente-Servico validado.")

    validar_confirmacao_portal(
        chave_sessao_servico,
        confirmacao_portal,
        dados_autenticador["timestamp"],
        nonce_portal,
    )
    log_ok(
        "CLIENTE WEB",
        "Autenticacao mutua com o Portal confirmada",
        {
            "usuario": usuario,
            "servico": "notas",
            "timestamp_validado": dados_autenticador["timestamp"],
            "nonce_validado": nonce_portal,
        },
    )
    registrar_etapa(
        logs,
        "Cliente validou timestamp e nonce da autenticacao mutua",
        componente="CLIENTE WEB",
        status="OK",
        dados={
            "usuario": usuario,
            "servico": "notas",
            "timestamp_validado": dados_autenticador["timestamp"],
            "nonce_validado": nonce_portal,
        },
    )
    registrar_etapa(logs, "[PORTAL] Autenticacao mutua concluida.")

    perfil = obter_perfil_usuario(usuario) if not usar_rede else None
    resultado = {
        "usuario": usuario,
        "perfil": perfil,
        "ticket_servico": resposta_tgs["ticket_servico"],
        "chave_sessao_servico": chave_sessao_servico,
        "portal_autenticado": True,
        "usar_rede": usar_rede,
        "cliente_tcp": cliente_tcp,
        "logs": logs,
    }

    if usar_rede:
        painel = executar_operacao_kerberos(resultado, "carregar_painel")
        perfil = painel["perfil"]
        resultado["perfil"] = perfil

    registrar_etapa(logs, f"[PORTAL] Acesso autorizado para perfil {perfil}.")
    log_ok(
        "CLIENTE WEB",
        "Fluxo Kerberos completo finalizado",
        {
            "usuario": usuario,
            "perfil": perfil,
            "portal_autenticado": resultado["portal_autenticado"],
        },
    )
    return resultado


def validar_ticket_notas(usuario, ticket_servico):
    """
    @brief Valida se o Service Ticket pertence ao usuario da sessao.

    @param usuario Usuario esperado.
    @param ticket_servico Ticket recebido do TGS.
    @return Ticket aberto.
    """
    ticket = validar_ticket_portal(ticket_servico)

    if ticket.get("usuario") != usuario:
        raise ValueError("Service Ticket pertence a outro usuario.")

    return ticket


def validar_sessao_portal(dados_sessao):
    """
    @brief Confere se a sessao Flask concluiu autenticacao mutua no Portal.

    @param dados_sessao Dados Kerberos guardados no servidor Flask.
    @return Ticket aberto no modo local ou None no modo TCP.
    @throws ValueError Quando a sessao nao esta autenticada.
    """
    if not dados_sessao or not dados_sessao.get("portal_autenticado"):
        raise ValueError("Autenticacao mutua com o Portal nao foi concluida.")

    if dados_sessao.get("usar_rede"):
        if not dados_sessao.get("ticket_servico"):
            raise ValueError("Service Ticket nao encontrado na sessao.")
        return

    return validar_ticket_notas(
        dados_sessao["usuario"],
        dados_sessao.get("ticket_servico"),
    )


def executar_operacao_kerberos(dados_sessao, acao, dados=None):
    """
    @brief Executa uma operacao do Portal usando Kerberos fim a fim.

    @param dados_sessao Sessao Kerberos criada no login.
    @param acao Operacao do Portal de Notas.
    @param dados Dados especificos da operacao.
    @return Resultado validado enviado pelo servico.

    A funcao cria uma requisicao cifrada, calcula seu hash, prende esse hash no
    autenticador e valida a resposta do Portal com timestamp e nonce esperados.
    """
    usuario = dados_sessao["usuario"]
    chave_sessao = dados_sessao["chave_sessao_servico"]
    nonce_operacao = secrets.token_hex(16)
    log_titulo(
        "CLIENTE WEB",
        f"Iniciando operacao protegida no Portal: {acao}",
    )
    requisicao = {
        "usuario": usuario,
        "acao": acao,
        "dados": dados or {},
        "nonce": nonce_operacao,
    }
    log_evento(
        "CLIENTE WEB",
        "Entrada da operacao Kerberos",
        requisicao,
    )
    registrar_etapa(
        dados_sessao["logs"],
        "Operacao protegida iniciada no Cliente Web",
        componente="CLIENTE WEB",
        status="ETAPA OPERACAO",
        dados={
            "usuario": usuario,
            "acao": acao,
            "dados": dados or {},
            "nonce_operacao": nonce_operacao,
        },
    )
    hash_requisicao = calcular_hash_requisicao(requisicao)
    requisicao_criptografada = criptografar_json(
        base64_para_bytes(chave_sessao),
        requisicao,
    )
    autenticador = criar_autenticador(
        usuario,
        chave_sessao,
        nonce=nonce_operacao,
        acao=acao,
        hash_requisicao=hash_requisicao,
    )
    dados_autenticador = abrir_autenticador(chave_sessao, autenticador)
    log_evento(
        "CLIENTE WEB",
        "Requisicao protegida e autenticador da operacao criados",
        {
            "acao": acao,
            "hash_requisicao": hash_requisicao,
            "requisicao_criptografada": requisicao_criptografada,
            "autenticador": autenticador,
            "dados_autenticador": dados_autenticador,
        },
    )
    registrar_etapa(
        dados_sessao["logs"],
        "Requisicao foi cifrada e amarrada ao autenticador",
        componente="CLIENTE WEB",
        status="OK",
        dados={
            "acao": acao,
            "hash_requisicao": hash_requisicao,
            "requisicao_criptografada": requisicao_criptografada,
            "autenticador": autenticador,
        },
    )

    registrar_etapa(
        dados_sessao["logs"],
        f"[CLIENTE] Autenticador criado para a operacao {acao}.",
    )
    if dados_sessao.get("usar_rede"):
        cliente_tcp = dados_sessao.get("cliente_tcp") or ClienteKerberosTCP()
        resposta_criptografada = cliente_tcp.executar_operacao(
            dados_sessao["ticket_servico"],
            autenticador,
            requisicao_criptografada,
        )
    else:
        resposta_criptografada = processar_operacao_portal(
            dados_sessao["ticket_servico"],
            autenticador,
            requisicao_criptografada,
        )
    log_evento(
        "CLIENTE WEB",
        "Resposta cifrada da operacao recebida",
        {
            "acao": acao,
            "resposta_criptografada": resposta_criptografada,
        },
    )
    registrar_etapa(
        dados_sessao["logs"],
        "Portal respondeu a operacao protegida",
        componente="PORTAL NOTAS",
        status="OK",
        dados={
            "acao": acao,
            "resposta_criptografada": resposta_criptografada,
        },
    )
    registrar_etapa(
        dados_sessao["logs"],
        f"[PORTAL] Ticket, autenticador e requisicao {acao} validados.",
    )

    resposta = validar_resposta_operacao(
        chave_sessao,
        resposta_criptografada,
        acao,
        dados_autenticador["timestamp"],
        nonce_operacao,
    )
    log_ok(
        "CLIENTE WEB",
        "Resposta do Portal validada pelo cliente",
        {
            "acao": resposta.get("acao"),
            "status": resposta.get("status"),
            "timestamp_resposta": resposta.get("timestamp_resposta"),
            "nonce_autenticador": resposta.get("nonce_autenticador"),
            "resultado": resposta.get("resultado"),
        },
    )
    registrar_etapa(
        dados_sessao["logs"],
        "Cliente validou resposta cifrada da operacao",
        componente="CLIENTE WEB",
        status="OK",
        dados={
            "acao": resposta.get("acao"),
            "status": resposta.get("status"),
            "timestamp_resposta": resposta.get("timestamp_resposta"),
            "nonce_autenticador": resposta.get("nonce_autenticador"),
            "resultado": resposta.get("resultado"),
        },
    )
    registrar_etapa(
        dados_sessao["logs"],
        f"[CLIENTE] Autenticacao mutua concluida para {acao}.",
    )
    return resposta["resultado"]


def create_app(usar_rede=True, cliente_tcp=None):
    """
    @brief Cria a aplicacao Flask do Portal de Notas.

    @param usar_rede Define se as rotas usam os servidores TCP reais.
    @param cliente_tcp Cliente TCP opcional usado em testes automatizados.
    @return Instancia Flask configurada.
    """
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
    )
    app.secret_key = os.environ.get(
        "FLASK_SECRET_KEY",
    ) or secrets.token_hex(32)
    app.config["KERBEROS_USAR_REDE"] = usar_rede

    # O cookie recebe somente este identificador. Tickets e chaves ficam no servidor.
    sessoes_kerberos = {}
    app.extensions["sessoes_kerberos"] = sessoes_kerberos

    def obter_sessao_kerberos():
        """@brief Recupera a sessao Kerberos associada ao cookie Flask."""
        id_sessao = session.get("id_sessao_kerberos")
        if not id_sessao:
            return None
        return sessoes_kerberos.get(id_sessao)

    def exigir_sessao_kerberos():
        """@brief Recupera e valida a sessao Kerberos antes das rotas protegidas."""
        dados_sessao = obter_sessao_kerberos()
        if not dados_sessao:
            return None
        validar_sessao_portal(dados_sessao)
        return dados_sessao

    @app.route("/")
    def index():
        """@brief Redireciona o usuario para login ou painel de notas."""
        if obter_sessao_kerberos():
            return redirect(url_for("notas"))
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        """@brief Exibe o formulario de login e inicia autenticacao Kerberos."""
        if request.method == "GET":
            return render_template("login.html")

        usuario = (request.form.get("usuario") or "").strip()
        senha = request.form.get("senha") or ""

        if not usuario or not senha:
            flash("Informe usuario e senha.")
            return redirect(url_for("login"))

        try:
            resultado = autenticar_com_kerberos(
                usuario,
                senha,
                usar_rede=app.config["KERBEROS_USAR_REDE"],
                cliente_tcp=cliente_tcp,
            )
            id_sessao = secrets.token_urlsafe(32)
            sessoes_kerberos[id_sessao] = resultado
            session.clear()
            session["id_sessao_kerberos"] = id_sessao
            return redirect(url_for("notas"))
        except Exception as erro:
            return render_template(
                "erro.html",
                mensagem=f"Falha na autenticacao Kerberos: {erro}",
            ), 401

    @app.route("/notas", methods=["GET", "POST"])
    def notas():
        """@brief Lista notas ou cria novas notas via operacao Kerberos protegida."""
        try:
            dados_sessao = exigir_sessao_kerberos()
        except Exception as erro:
            session.clear()
            return render_template(
                "erro.html",
                mensagem=f"Acesso ao Portal negado: {erro}",
            ), 403

        if not dados_sessao:
            flash("Faca login pelo Kerberos para acessar o Portal de Notas.")
            return redirect(url_for("login"))

        usuario = dados_sessao["usuario"]

        try:
            if request.method == "POST":
                disciplinas = request.form.getlist("disciplina")
                valores = request.form.getlist("nota")
                observacoes = request.form.getlist("observacao")
                notas_formulario = [
                    {
                        "disciplina": disciplina,
                        "nota": valores[indice] if indice < len(valores) else "",
                        "observacao": (
                            observacoes[indice]
                            if indice < len(observacoes)
                            else ""
                        ),
                    }
                    for indice, disciplina in enumerate(disciplinas)
                ]
                acao = "criar_nota"
                dados = {
                    "aluno": request.form.get("aluno"),
                    **(notas_formulario[0] if notas_formulario else {}),
                }
                if len(notas_formulario) > 1:
                    acao = "criar_notas"
                    dados = {
                        "aluno": request.form.get("aluno"),
                        "notas": notas_formulario,
                    }

                registrar_etapa(
                    dados_sessao["logs"],
                    "Formulario de lancamento de nota recebido",
                    componente="CLIENTE WEB",
                    status="ENTRADA",
                    dados={
                        "usuario": usuario,
                        "acao": acao,
                        "aluno": request.form.get("aluno"),
                        "quantidade_notas": len(notas_formulario),
                        "notas": notas_formulario,
                    },
                )
                executar_operacao_kerberos(
                    dados_sessao,
                    acao,
                    dados,
                )
                registrar_etapa(
                    dados_sessao["logs"],
                    (
                        f"[PORTAL] Professor {usuario} lancou "
                        f"{len(notas_formulario)} nota(s)."
                    ),
                )
                flash("Nota(s) lancada(s) com sucesso.")
                return redirect(url_for("notas"))

            painel = executar_operacao_kerberos(
                dados_sessao,
                "carregar_painel",
            )
            dados_sessao["perfil"] = painel["perfil"]
            return render_template(
                "notas.html",
                usuario=usuario,
                perfil=painel["perfil"],
                notas=painel["notas"],
                alunos=painel["alunos"],
                logs=dados_sessao["logs"],
            )
        except PermissionError as erro:
            registrar_etapa(dados_sessao["logs"], f"[PORTAL] {erro}")
            return render_template("erro.html", mensagem=str(erro)), 403
        except Exception as erro:
            return render_template(
                "erro.html",
                mensagem=f"Erro ao acessar notas: {erro}",
            ), 400

    @app.post("/notas/<nota_id>/editar")
    def editar(nota_id):
        """@brief Edita uma nota usando uma operacao Kerberos protegida."""
        try:
            dados_sessao = exigir_sessao_kerberos()
            if not dados_sessao:
                return redirect(url_for("login"))

            registrar_etapa(
                dados_sessao["logs"],
                "Formulario de edicao de nota recebido",
                componente="CLIENTE WEB",
                status="ENTRADA",
                dados={
                    "nota_id": nota_id,
                    "disciplina": request.form.get("disciplina"),
                    "nota": request.form.get("nota"),
                    "observacao": request.form.get("observacao"),
                },
            )
            executar_operacao_kerberos(
                dados_sessao,
                "editar_nota",
                {
                    "nota_id": nota_id,
                    "disciplina": request.form.get("disciplina"),
                    "nota": request.form.get("nota"),
                    "observacao": request.form.get("observacao"),
                },
            )
            registrar_etapa(
                dados_sessao["logs"],
                f"[PORTAL] Nota {nota_id} atualizada.",
            )
            flash("Nota atualizada com sucesso.")
            return redirect(url_for("notas"))
        except PermissionError as erro:
            if dados_sessao:
                registrar_etapa(dados_sessao["logs"], f"[PORTAL] {erro}")
            return render_template("erro.html", mensagem=str(erro)), 403
        except Exception as erro:
            return render_template("erro.html", mensagem=str(erro)), 400

    @app.post("/notas/<nota_id>/excluir")
    def excluir(nota_id):
        """@brief Exclui uma nota usando uma operacao Kerberos protegida."""
        try:
            dados_sessao = exigir_sessao_kerberos()
            if not dados_sessao:
                return redirect(url_for("login"))

            registrar_etapa(
                dados_sessao["logs"],
                "Solicitacao de exclusao de nota recebida",
                componente="CLIENTE WEB",
                status="ENTRADA",
                dados={"nota_id": nota_id},
            )
            executar_operacao_kerberos(
                dados_sessao,
                "excluir_nota",
                {"nota_id": nota_id},
            )
            registrar_etapa(
                dados_sessao["logs"],
                f"[PORTAL] Nota {nota_id} excluida.",
            )
            flash("Nota excluida com sucesso.")
            return redirect(url_for("notas"))
        except PermissionError as erro:
            if dados_sessao:
                registrar_etapa(dados_sessao["logs"], f"[PORTAL] {erro}")
            return render_template("erro.html", mensagem=str(erro)), 403
        except Exception as erro:
            return render_template("erro.html", mensagem=str(erro)), 400

    @app.route("/logout")
    def logout():
        """@brief Remove a sessao Kerberos do servidor Flask e encerra o acesso."""
        id_sessao = session.pop("id_sessao_kerberos", None)
        dados_sessao = sessoes_kerberos.get(id_sessao) if id_sessao else None
        if dados_sessao:
            registrar_etapa(
                dados_sessao["logs"],
                "Logout solicitado pelo usuario",
                componente="CLIENTE WEB",
                status="OK",
                dados={
                    "usuario": dados_sessao.get("usuario"),
                    "perfil": dados_sessao.get("perfil"),
                    "portal_autenticado": dados_sessao.get("portal_autenticado"),
                    "id_sessao": id_sessao,
                },
            )
        else:
            log_ok(
                "CLIENTE WEB",
                "Logout solicitado sem sessao Kerberos ativa",
                {"id_sessao": id_sessao},
            )
        if id_sessao:
            sessoes_kerberos.pop(id_sessao, None)
        session.clear()
        flash("Voce saiu do Portal de Notas.")
        return redirect(url_for("login"))

    return app
