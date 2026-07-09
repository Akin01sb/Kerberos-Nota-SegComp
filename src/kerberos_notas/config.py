import os

from kerberos_notas.crypto.crypto_utils import base64_para_bytes


CHAVE_SECRETA_TGS_BASE64 = os.environ.get(
    "KERBEROS_CHAVE_TGS",
    "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA=",
)
CHAVE_SECRETA_SERVICO_NOTAS_BASE64 = os.environ.get(
    "KERBEROS_CHAVE_NOTAS",
    "MTExMTExMTExMTExMTExMTExMTExMTExMTExMTExMTE=",
)

CHAVE_SECRETA_TGS = base64_para_bytes(CHAVE_SECRETA_TGS_BASE64)
CHAVE_SECRETA_SERVICO_NOTAS = base64_para_bytes(CHAVE_SECRETA_SERVICO_NOTAS_BASE64)

HOST_KERBEROS = os.environ.get("KERBEROS_HOST", "127.0.0.1")
PORTA_AS = int(os.environ.get("KERBEROS_PORTA_AS", "9001"))
PORTA_TGS = int(os.environ.get("KERBEROS_PORTA_TGS", "9002"))
PORTA_NOTAS = int(os.environ.get("KERBEROS_PORTA_NOTAS", "9003"))
TIMEOUT_REDE = float(os.environ.get("KERBEROS_TIMEOUT_REDE", "5"))
