# Testes e demonstração rápida

## Testes

Na raiz do projeto:

```powershell
python -m pytest -q
```

Resultado atual:

```text
48 passed
```

- `test_crypto.py`: KDF, AES-GCM, nonces e adulteração.
- `test_as_server.py`: autenticação, resposta do AS e TGT.
- `test_tgs.py`: TGT, replay Cliente-TGS e Service Ticket.
- `test_notas.py`: autenticação mútua, CRUD, replay e permissões.
- `test_fluxo.py`: fluxo lógico completo.
- `test_rede.py`: AS, TGS e Notas em sockets TCP reais.

## Demonstração recomendada

1. Execute `python scripts/iniciar_servidores.py`.
2. Em outro terminal, execute `python run.py`.
3. Entre com um professor e mostre os logs dos três servidores.
4. Lance, edite e exclua uma nota.
5. Entre com um aluno e mostre a restrição de acesso.
6. Execute `python -m pytest -q`.
