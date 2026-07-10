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


def registrar_etapa(logs, mensagem):
    logs.append(mensagem)
    print(mensagem)


def autenticar_com_kerberos(
        usuario,
        senha,
        usar_rede=True,
        cliente_tcp=None
):
    logs = []
    registrar_etapa(logs, "[CLIENTE] Senha informada localmente pelo usuario.")
    registrar_etapa(logs, "[CLIENTE] Solicitando autenticacao ao AS.")

    cliente_tcp = cliente_tcp or ClienteKerberosTCP()
    if usar_rede:
        parametros_as = cliente_tcp.solicitar_parametros_as(usuario)
    else:
        parametros_as = criar_desafio_as(usuario)

    if parametros_as.get("iteracoes_kdf") != ITERACOES_PBKDF2:
        raise ValueError("Parametros KDF recebidos do AS sao invalidos.")

    chave_derivada = derivar_chave_senha(senha, parametros_as["salt"])
    chave_cliente = obter_chave_autenticacao_as(chave_derivada)
    prova = gerar_prova_as(
        chave_cliente,
        usuario,
        parametros_as["desafio"],
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
    registrar_etapa(
        logs,
        "[AS] Prova criptografica do usuario validada.",
    )

    registrar_etapa(logs, "[AS] TGT emitido com sucesso.")
    registrar_etapa(logs, "[CLIENTE] Chave derivada com PBKDF2-HMAC-SHA256.")

    resposta_as = descriptografar_json(chave_cliente, resposta_as_criptografada)
    chave_sessao_cliente_tgs = resposta_as["chave_sessao_cliente_tgs"]
    autenticador_tgs = criar_autenticador(usuario, chave_sessao_cliente_tgs)
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
    registrar_etapa(logs, "[TGS] TGT e autenticador Cliente-TGS validados.")
    registrar_etapa(logs, "[TGS] Service Ticket para o Portal de Notas emitido.")

    dados_cliente = descriptografar_json(
        base64_para_bytes(chave_sessao_cliente_tgs),
        resposta_tgs["resposta_cliente"],
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
    registrar_etapa(logs, "[PORTAL] Service Ticket validado.")
    registrar_etapa(logs, "[PORTAL] Autenticador Cliente-Servico validado.")

    validar_confirmacao_portal(
        chave_sessao_servico,
        confirmacao_portal,
        dados_autenticador["timestamp"],
        nonce_portal,
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
    return resultado


def validar_ticket_notas(usuario, ticket_servico):
    ticket = validar_ticket_portal(ticket_servico)

    if ticket.get("usuario") != usuario:
        raise ValueError("Service Ticket pertence a outro usuario.")

    return ticket


def validar_sessao_portal(dados_sessao):
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
    usuario = dados_sessao["usuario"]
    chave_sessao = dados_sessao["chave_sessao_servico"]
    nonce_operacao = secrets.token_hex(16)
    requisicao = {
        "usuario": usuario,
        "acao": acao,
        "dados": dados or {},
        "nonce": nonce_operacao,
    }
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
    registrar_etapa(
        dados_sessao["logs"],
        f"[CLIENTE] Autenticacao mutua concluida para {acao}.",
    )
    return resposta["resultado"]


def create_app(usar_rede=True, cliente_tcp=None):
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
        id_sessao = session.get("id_sessao_kerberos")
        if not id_sessao:
            return None
        return sessoes_kerberos.get(id_sessao)

    def exigir_sessao_kerberos():
        dados_sessao = obter_sessao_kerberos()
        if not dados_sessao:
            return None
        validar_sessao_portal(dados_sessao)
        return dados_sessao

    @app.route("/")
    def index():
        if obter_sessao_kerberos():
            return redirect(url_for("notas"))
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
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
        try:
            dados_sessao = exigir_sessao_kerberos()
            if not dados_sessao:
                return redirect(url_for("login"))

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
        try:
            dados_sessao = exigir_sessao_kerberos()
            if not dados_sessao:
                return redirect(url_for("login"))

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
        id_sessao = session.pop("id_sessao_kerberos", None)
        if id_sessao:
            sessoes_kerberos.pop(id_sessao, None)
        session.clear()
        flash("Voce saiu do Portal de Notas.")
        return redirect(url_for("login"))

    return app
