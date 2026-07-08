from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, session, flash

from kerberos_notas.crypto.crypto_utils import base64_para_bytes, descriptografar_json
from kerberos_notas.crypto.kdf import derivar_chave_senha
from kerberos_notas.kerberos.as_server import autenticar_no_as, carregar_usuarios
from kerberos_notas.kerberos.authenticator import criar_autenticador
from kerberos_notas.kerberos.tgs_server import emitir_ticket_servico


BASE_DIR = Path(__file__).resolve().parents[3]


def autenticar_com_kerberos(usuario, senha):
    """
    Esta função deve usar o que já foi feito pela Pessoa 1 e Pessoa 2.

    Fluxo esperado:
    1. Cliente envia usuário e senha.
    2. AS valida o usuário.
    3. AS gera TGT.
    4. Cliente usa TGT para pedir ticket ao TGS.
    5. TGS gera ticket de serviço para acessar o sistema de notas.
    """

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
        autenticador_criptografado=autenticador
    )

    dados_cliente = descriptografar_json(
        base64_para_bytes(chave_sessao_cliente_tgs),
        resposta_tgs["resposta_cliente"]
    )

    return {
        "ticket_servico": resposta_tgs["ticket_servico"],
        "chave_sessao_servico": dados_cliente["chave_sessao_cliente_servico"],
    }


def listar_notas_protegidas(usuario):
    """
    Esta função deve usar o serviço de notas feito pela Pessoa 3.
    """

    # Exemplo conceitual:
    #
    # from kerberos_notas.notes.service import listar_notas
    # return listar_notas(usuario)

    raise NotImplementedError(
        "Conecte esta função com o serviço real de notas."
    )


def criar_nota_protegida(usuario, titulo, conteudo):
    """
    Esta função deve criar uma nota usando o serviço já existente.
    """

    # Exemplo conceitual:
    #
    # from kerberos_notas.notes.service import criar_nota
    # criar_nota(usuario, titulo, conteudo)

    raise NotImplementedError(
        "Conecte esta função com o serviço real de notas."
    )










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
            flash("Informe usuário e senha.")
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
                mensagem=f"Falha na autenticação: {erro}",
            )

    @app.route("/notas", methods=["GET", "POST"])
    def notas():
        if "usuario" not in session:
            flash("Faça login para acessar o sistema de notas.")
            return redirect(url_for("login"))

        usuario = session["usuario"]

        try:
            if request.method == "POST":
                titulo = request.form.get("titulo")
                conteudo = request.form.get("conteudo")

                if titulo and conteudo:
                    #criar_nota_protegida(usuario, titulo, conteudo)
                    flash("Nota criada com sucesso.")
                else:
                    flash("Preencha título e conteúdo.")

            #lista_notas = listar_notas_protegidas(usuario)

            return render_template(
                "notas.html",
                usuario=usuario,
                #notas=lista_notas,
            )

        except Exception as erro:
            return render_template(
                "erro.html",
                mensagem=f"Erro ao acessar notas: {erro}",
            )

    @app.route("/logout")
    def logout():
        session.clear()
        flash("Você saiu do sistema.")
        return redirect(url_for("login"))

    return app
