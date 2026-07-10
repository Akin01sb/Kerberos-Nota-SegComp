"""
@file gerar_chaves.py
@brief Gera chaves simetricas para variaveis de ambiente.

@details
Imprime comandos PowerShell com chaves aleatorias para TGS, servico de notas e
secret key do Flask, substituindo os valores didaticos padrao.
"""

import base64
import secrets


def gerar_chave_base64():
    """@brief Gera chave AES-256 aleatoria codificada em Base64."""
    return base64.b64encode(secrets.token_bytes(32)).decode("ascii")


def main():
    """@brief Imprime comandos PowerShell para configurar segredos."""
    print("# PowerShell")
    print(f"$env:KERBEROS_CHAVE_TGS='{gerar_chave_base64()}'")
    print(f"$env:KERBEROS_CHAVE_NOTAS='{gerar_chave_base64()}'")
    print(f"$env:FLASK_SECRET_KEY='{secrets.token_urlsafe(32)}'")


if __name__ == "__main__":
    main()
