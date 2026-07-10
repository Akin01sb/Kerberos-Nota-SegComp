import base64
import secrets


def gerar_chave_base64():
    return base64.b64encode(secrets.token_bytes(32)).decode("ascii")


def main():
    print("# PowerShell")
    print(f"$env:KERBEROS_CHAVE_TGS='{gerar_chave_base64()}'")
    print(f"$env:KERBEROS_CHAVE_NOTAS='{gerar_chave_base64()}'")
    print(f"$env:FLASK_SECRET_KEY='{secrets.token_urlsafe(32)}'")


if __name__ == "__main__":
    main()
