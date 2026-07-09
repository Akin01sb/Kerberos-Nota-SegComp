# Testes e demonstração rápida

O serviço principal deste projeto é o Portal de Notas Escolares protegido por
Kerberos.

## Testes

Na raiz do projeto:

```powershell
$env:PYTHONPATH='src'
python -m pytest -q
```

Resultado atual:

```text
39 passed
```

Arquivos principais:

- `test_crypto.py`: KDF, AES-GCM, nonces e adulteração;
- `test_as_server.py`: senha, resposta do AS e TGT;
- `test_tgs.py`: TGT, autenticador Cliente-TGS e Service Ticket;
- `test_notas.py`: autenticação mútua por operação, replay, CRUD e permissões;
- `test_fluxo.py`: fluxo completo AS -> TGS -> Portal.

## Demonstração recomendada

1. Execute `python run.py`.
2. Entre com um usuário professor.
3. Abra “Etapas da autenticação Kerberos”.
4. Mostre a emissão do TGT e do Service Ticket.
5. Mostre a validação do autenticador e a autenticação mútua.
6. Lance e edite uma nota, mostrando os novos autenticadores nos logs.
7. Saia e entre com o aluno.
8. Mostre que o aluno vê apenas as próprias notas.
9. Mostre que o painel do aluno não oferece ações de alteração.
10. Execute a suíte automatizada.
