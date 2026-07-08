from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, session, url_for

from kerberos_notas.crypto.crypto_utils import base64_para_bytes, descriptografar_json
from kerberos_notas.crypto.kdf import derivar_chave_senha
from kerberos_notas.kerberos.as_server import autenticar_no_as, carregar_usuarios
from kerberos_notas.kerberos.authenticator import criar_autenticador
from kerberos_notas.kerberos.tgs_server import abrir_ticket_servico, emitir_ticket_servico
from kerberos_notas.notes.service import criar_nota, listar_notas


BASE_DIR = Path(__file__).resolve().parents[3]


def autenticar_com_kerberos(usuario, senha):
    resposta_as_criptografada = autenticar_no_as(usuario, senha)

    usuarios = carregar_usuarios().get("usuarios", {})
    salt = usuarios[usuario]["salt"]
    chave_cliente = derivar_chave_senha(senha, salt)

    resposta_as = descriptografar_json(chave_cliente, resposta_as_criptografada)
    chave_sessao_cliente_tgs = resposta_as["chave_sessao_cliente_tgs"]
    autenticador = criar_autenticador(usuario, chave_sessao_cliente_tgs)

    resposta_tgs = emitir_ticket_servico(
        usuario=usuario,
        servico="notas",
        tgt_criptografado=resposta_as["tgt"],
        autenticador_criptografado=autenticador,
    )

    dados_cliente = descriptografar_json(
        base64_para_bytes(chave_sessao_cliente_tgs),
        resposta_tgs["resposta_cliente"],
    )

    return {
        "ticket_servico": resposta_tgs["ticket_servico"],
        "chave_sessao_servico": dados_cliente["chave_sessao_cliente_servico"],
    }


def validar_ticket_notas(usuario, ticket_servico):
    if not ticket_servico:
        raise ValueError("Ticket de servico nao encontrado na sessao.")

    ticket = abrir_ticket_servico("notas", ticket_servico)

    if ticket.get("usuario") != usuario:
        raise ValueError("Ticket de servico pertence a outro usuario.")

    return ticket


def listar_notas_protegidas(usuario, ticket_servico):
    validar_ticket_notas(usuario, ticket_servico)
    return listar_notas(usuario)


def criar_nota_protegida(usuario, ticket_servico, titulo, conteudo):
    validar_ticket_notas(usuario, ticket_servico)
    return criar_nota(usuario, titulo, conteudo)


def create_app():
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
    )

    app.secret_key = "chave-dev-apenas-para-trabalho"

    @app.route("/")
    def index():
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "GET":
            return render_template("login.html")

        usuario = request.form.get("usuario")
        senha = request.form.get("senha")

        if not usuario or not senha:
            flash("Informe usuario e senha.")
            return redirect(url_for("login"))

        try:
            resultado = autenticar_com_kerberos(usuario, senha)

            session["usuario"] = usuario
            session["ticket_servico"] = resultado.get("ticket_servico")
            session["chave_sessao_servico"] = resultado.get("chave_sessao_servico")

            return redirect(url_for("notas"))

        except Exception as erro:
            return render_template(
                "erro.html",
                mensagem=f"Falha na autenticacao: {erro}",
            )

    @app.route("/notas", methods=["GET", "POST"])
    def notas():
        if "usuario" not in session:
            flash("Faca login para acessar o sistema de notas.")
            return redirect(url_for("login"))

        usuario = session["usuario"]
        ticket_servico = session.get("ticket_servico")

        try:
            if request.method == "POST":
                titulo = request.form.get("titulo")
                conteudo = request.form.get("conteudo")

                if titulo and conteudo:
                    criar_nota_protegida(usuario, ticket_servico, titulo, conteudo)
                    flash("Nota criada com sucesso.")
                else:
                    flash("Preencha titulo e conteudo.")

            lista_notas = listar_notas_protegidas(usuario, ticket_servico)

            return render_template(
                "notas.html",
                usuario=usuario,
                notas=lista_notas,
            )

        except Exception as erro:
            return render_template(
                "erro.html",
                mensagem=f"Erro ao acessar notas: {erro}",
            )

    @app.route("/logout")
    def logout():
        session.clear()
        flash("Voce saiu do sistema.")
        return redirect(url_for("login"))

    return app
