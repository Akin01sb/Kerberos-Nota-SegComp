import os

from kerberos_notas.crypto.crypto_utils import base64_para_bytes


CHAVE_SECRETA_TGS_PADRAO_BASE64 = "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA="
CHAVE_SECRETA_SERVICO_NOTAS_PADRAO_BASE64 = "MTExMTExMTExMTExMTExMTExMTExMTExMTExMTExMTE="


def _carregar_chave_base64(nome_variavel, valor_padrao):
    valor = os.environ.get(nome_variavel, valor_padrao)
    chave = base64_para_bytes(valor)
    if len(chave) != 32:
        raise ValueError(
            f"{nome_variavel} deve ser Base64 de uma chave com 32 bytes."
        )
    return valor, chave


CHAVE_SECRETA_TGS_BASE64, CHAVE_SECRETA_TGS = _carregar_chave_base64(
    "KERBEROS_CHAVE_TGS",
    CHAVE_SECRETA_TGS_PADRAO_BASE64,
)
(
    CHAVE_SECRETA_SERVICO_NOTAS_BASE64,
    CHAVE_SECRETA_SERVICO_NOTAS,
) = _carregar_chave_base64(
    "KERBEROS_CHAVE_NOTAS",
    CHAVE_SECRETA_SERVICO_NOTAS_PADRAO_BASE64,
)

USANDO_CHAVES_PADRAO_DIDATICAS = (
    "KERBEROS_CHAVE_TGS" not in os.environ
    or "KERBEROS_CHAVE_NOTAS" not in os.environ
)

HOST_KERBEROS = os.environ.get("KERBEROS_HOST", "127.0.0.1")
PORTA_AS = int(os.environ.get("KERBEROS_PORTA_AS", "9001"))
PORTA_TGS = int(os.environ.get("KERBEROS_PORTA_TGS", "9002"))
PORTA_NOTAS = int(os.environ.get("KERBEROS_PORTA_NOTAS", "9003"))
TIMEOUT_REDE = float(os.environ.get("KERBEROS_TIMEOUT_REDE", "5"))
