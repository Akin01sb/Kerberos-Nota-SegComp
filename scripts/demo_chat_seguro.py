import copy
import json
import tempfile
from pathlib import Path

import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from kerberos_notas.crypto.crypto_utils import base64_para_bytes, descriptografar_json
from kerberos_notas.crypto.kdf import (
    derivar_chave_senha,
    gerar_salt,
    gerar_verificador_chave,
)
from kerberos_notas.kerberos import as_server
from kerberos_notas.kerberos.as_server import autenticar_no_as
from kerberos_notas.kerberos.authenticator import criar_autenticador
from kerberos_notas.kerberos.tgs_server import emitir_ticket_servico
from kerberos_notas.notes.chat_client import montar_pacote_chat, validar_resposta_chat
from kerberos_notas.notes.chat_server import processar_pacote_chat


def preparar_usuario_temporario() -> tuple[str, str]:
    usuario = "ana"
    senha = "senha123"
    salt = gerar_salt()
    chave = derivar_chave_senha(senha, salt)
    verificador = gerar_verificador_chave(chave)

    dados = {
        "usuarios": {
            usuario: {
                "salt": salt,
                "verificador": verificador
            }
        }
    }

    arquivo = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".json",
        delete=False
    )
    json.dump(dados, arquivo, indent=4)
    arquivo.close()

    as_server.CAMINHO_USUARIOS = Path(arquivo.name)

    return usuario, senha


def main() -> None:
    usuario, senha = preparar_usuario_temporario()
    print("1. Usuario temporario criado")

    resposta_as_criptografada = autenticar_no_as(usuario, senha)
    chave_cliente = derivar_chave_senha(
        senha,
        as_server.carregar_usuarios()["usuarios"][usuario]["salt"]
    )
    resposta_as = descriptografar_json(chave_cliente, resposta_as_criptografada)
    print("2. AS validou senha e emitiu TGT")

    autenticador_tgs = criar_autenticador(
        usuario,
        resposta_as["chave_sessao_cliente_tgs"]
    )
    resposta_tgs = emitir_ticket_servico(
        usuario=usuario,
        servico="chat",
        tgt_criptografado=resposta_as["tgt"],
        autenticador_criptografado=autenticador_tgs
    )
    dados_tgs = descriptografar_json(
        base64_para_bytes(resposta_as["chave_sessao_cliente_tgs"]),
        resposta_tgs["resposta_cliente"]
    )
    chave_chat = dados_tgs["chave_sessao_cliente_servico"]
    print("3. TGS emitiu ticket de servico para o chat")

    pacote = montar_pacote_chat(
        remetente=usuario,
        destinatario="bia",
        conteudo="mensagem secreta para demonstracao",
        ticket_servico_criptografado=resposta_tgs["ticket_servico"],
        chave_sessao_cliente_servico_base64=chave_chat,
        nonce_autenticador="nonce-demo"
    )
    print("4. Cliente criou mensagem criptografada")
    print("Texto aparece no pacote?", "mensagem secreta" in str(pacote))

    resposta_chat = processar_pacote_chat(pacote)
    validar_resposta_chat(chave_chat, resposta_chat, "nonce-demo")
    print("5. Servico validou ticket, autenticador, HMAC e abriu mensagem")
    print("Mensagem recebida:", resposta_chat["mensagem"]["conteudo"])

    pacote_adulterado = copy.deepcopy(pacote)
    pacote_adulterado["mensagem"]["destinatario"] = "carla"
    resposta_adulterada = processar_pacote_chat(pacote_adulterado)
    print("6. Mensagem adulterada foi aceita?", resposta_adulterada["ok"])
    print("Alerta:", resposta_adulterada["erro"])


if __name__ == "__main__":
    main()
