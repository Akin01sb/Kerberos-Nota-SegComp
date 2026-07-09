# Fontes dos algoritmos e bibliotecas

Referências usadas para justificar as escolhas do projeto:

- Python `hashlib`: documentação de `pbkdf2_hmac`, incluindo uso de salt,
  iterações e tamanho da chave:
  https://docs.python.org/3/library/hashlib.html#hashlib.pbkdf2_hmac
- Cryptography: documentação oficial de criptografia autenticada e `AESGCM`:
  https://cryptography.io/en/stable/hazmat/primitives/aead/
- Flask: documentação oficial sobre sessões assinadas:
  https://flask.palletsprojects.com/en/stable/quickstart/#sessions

No projeto:

- PBKDF2-HMAC-SHA256 está em `src/kerberos_notas/crypto/kdf.py`;
- AES-GCM está em `src/kerberos_notas/crypto/crypto_utils.py`;
- a sessão Flask guarda apenas um identificador; tickets e chaves ficam em
  memória no servidor, conforme `src/kerberos_notas/client/routes.py`.
