import json
import hmac
import secrets
import uuid
from pathlib import Path
from threading import RLock

from kerberos_notas.config import CHAVE_SECRETA_TGS
from kerberos_notas.crypto.crypto_utils import (
    base64_para_bytes,
    bytes_para_base64,
    criptografar_json,
    gerar_chave_simetrica,
)
from kerberos_notas.crypto.kdf import (
    ITERACOES_PBKDF2,
    derivar_chave_senha,
    gerar_prova_as,
    gerar_verificador_chave,
)
from kerberos_notas.kerberos.tickets import criar_tgt, timestamp_atual


CAMINHO_USUARIOS = Path(__file__).resolve().parents[3] / "data" / "usuarios.json"
TEMPO_VALIDADE_TGT = 60 * 10
TEMPO_VALIDADE_DESAFIO = 60
DESAFIOS_AS = {}
BLOQUEIO_DESAFIOS_AS = RLock()


def carregar_usuarios() -> dict:
    if not CAMINHO_USUARIOS.exists():
        return {"usuarios": {}}

    with open(CAMINHO_USUARIOS, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def validar_usuario_no_as(nome_usuario: str, senha: str) -> bytes:
    dados_usuarios = carregar_usuarios()
    usuarios = dados_usuarios.get("usuarios", {})

    if nome_usuario not in usuarios:
        raise ValueError("Usuario nao encontrado.")

    dados_usuario = usuarios[nome_usuario]
    salt = dados_usuario["salt"]
    verificador_salvo = dados_usuario["verificador"]

    chave_cliente = derivar_chave_senha(senha, salt)
    verificador_calculado = gerar_verificador_chave(chave_cliente)

    if verificador_calculado != verificador_salvo:
        raise ValueError("Senha invalida.")

    return chave_cliente


def obter_dados_usuario(nome_usuario: str) -> dict:
    usuarios = carregar_usuarios().get("usuarios", {})
    if nome_usuario not in usuarios:
        raise ValueError("Usuario nao encontrado.")
    return usuarios[nome_usuario]


def criar_desafio_as(nome_usuario: str) -> dict:
    dados_usuario = obter_dados_usuario(nome_usuario)
    agora = timestamp_atual()

    with BLOQUEIO_DESAFIOS_AS:
        expirados = [
            desafio
            for desafio, dados in DESAFIOS_AS.items()
            if dados["timestamp"] < agora - TEMPO_VALIDADE_DESAFIO
        ]
        for desafio in expirados:
            DESAFIOS_AS.pop(desafio, None)

        desafio = secrets.token_hex(32)
        DESAFIOS_AS[desafio] = {
            "usuario": nome_usuario,
            "timestamp": agora,
        }
    return {
        "usuario": nome_usuario,
        "salt": dados_usuario["salt"],
        "iteracoes_kdf": ITERACOES_PBKDF2,
        "desafio": desafio,
    }


def _emitir_resposta_as(
        nome_usuario: str,
        chave_cliente: bytes,
        validade_segundos: int
) -> dict:
    chave_sessao_cliente_tgs = gerar_chave_simetrica()
    chave_sessao_cliente_tgs_base64 = bytes_para_base64(chave_sessao_cliente_tgs)

    tgt = gerar_tgt(
        nome_usuario=nome_usuario,
        chave_sessao_cliente_tgs_base64=chave_sessao_cliente_tgs_base64,
        validade_segundos=validade_segundos,
    )
    tgt_criptografado = criptografar_json(CHAVE_SECRETA_TGS, tgt)
    resposta_para_cliente = {
        "id_tgs": "tgs",
        "chave_sessao_cliente_tgs": chave_sessao_cliente_tgs_base64,
        "tgt": tgt_criptografado,
        "timestamp_emissao": tgt["timestamp_emissao"],
        "timestamp_expiracao": tgt["timestamp_expiracao"],
        "validade_segundos": tgt["validade_segundos"],
        "nonce_tgt": tgt["nonce"],
    }
    return criptografar_json(chave_cliente, resposta_para_cliente)


def autenticar_no_as_com_prova(
        nome_usuario: str,
        desafio: str,
        prova: str,
        validade_segundos: int = TEMPO_VALIDADE_TGT
) -> dict:
    with BLOQUEIO_DESAFIOS_AS:
        dados_desafio = DESAFIOS_AS.pop(desafio, None)
    if not dados_desafio or dados_desafio["usuario"] != nome_usuario:
        raise ValueError("Desafio de autenticacao invalido.")

    if dados_desafio["timestamp"] < timestamp_atual() - TEMPO_VALIDADE_DESAFIO:
        raise ValueError("Desafio de autenticacao expirado.")

    dados_usuario = obter_dados_usuario(nome_usuario)
    chave_autenticacao = base64_para_bytes(dados_usuario["verificador"])
    prova_esperada = gerar_prova_as(
        chave_autenticacao,
        nome_usuario,
        desafio,
    )
    if not hmac.compare_digest(prova_esperada, prova):
        raise ValueError("Senha invalida.")

    return _emitir_resposta_as(
        nome_usuario,
        chave_autenticacao,
        validade_segundos,
    )


def gerar_tgt(
        nome_usuario: str,
        chave_sessao_cliente_tgs_base64: str,
        validade_segundos: int = TEMPO_VALIDADE_TGT
) -> dict:
    if validade_segundos <= 0:
        raise ValueError("Validade do TGT invalida.")

    tgt = criar_tgt(
        id_cliente=nome_usuario,
        chave_sessao_cliente_tgs_base64=chave_sessao_cliente_tgs_base64,
        id_tgs="tgs"
    )

    # campos extras para deixar o TGT mais claro no AS
    tgt["usuario"] = nome_usuario
    tgt["validade_segundos"] = validade_segundos
    tgt["timestamp_expiracao"] = tgt["timestamp_emissao"] + validade_segundos
    tgt["nonce"] = uuid.uuid4().hex

    return tgt


def autenticar_no_as(
        nome_usuario: str,
        senha: str,
        validade_segundos: int = TEMPO_VALIDADE_TGT
) -> dict:
    # valida usuario e senha usando a chave derivada pela KDF
    chave_cliente = validar_usuario_no_as(nome_usuario, senha)
    return _emitir_resposta_as(
        nome_usuario,
        chave_cliente,
        validade_segundos,
    )
