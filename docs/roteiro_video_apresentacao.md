# Roteiro de apresentação

Tempo sugerido: 8 a 12 minutos.

## 1. Abertura

> Nosso projeto implementa uma versão simplificada do Kerberos usando
> criptografia simétrica. O serviço protegido é um Portal de Notas Escolares.

Apresente o fluxo:

```text
Cliente -> AS -> TGS -> Portal de Notas
```

## 2. KDF e AS

Mostre `crypto/kdf.py` e `kerberos/as_server.py`.

- PBKDF2-HMAC-SHA256, salt e 200.000 iterações;
- senha ausente dos arquivos e logs;
- validação do verificador;
- geração da chave Cliente-TGS;
- criação do TGT cifrado com a chave do TGS.

## 3. TGS

Mostre `kerberos/tgs_server.py`.

- entrada: TGT e autenticador Cliente-TGS;
- validação de identidade, timestamp e validade;
- geração da chave Cliente-Serviço;
- emissão do Service Ticket para `notas`.

## 4. Portal e autenticação mútua

Mostre `notes/portal_notas.py` e `client/routes.py`.

- validação do Service Ticket;
- abertura do autenticador Cliente-Serviço;
- conferência do usuário, timestamp e nonce;
- resposta cifrada com timestamp incrementado;
- validação da resposta pelo cliente;
- criação da sessão somente após essa confirmação.

## 5. Demonstração como professor

1. Execute `python run.py`.
2. Faça login com um usuário professor.
3. Abra a lista “Etapas da autenticação Kerberos”.
4. Mostre as mensagens do AS, TGS e Portal.
5. Lance uma nota para um aluno.
6. Edite a disciplina, valor ou observação.
7. Mostre a listagem geral.
8. Faça logout.

## 6. Demonstração como aluno

1. Entre com um usuário aluno.
2. Mostre que aparecem somente as notas desse aluno.
3. Mostre que não existe formulário de lançamento.
4. Explique que uma requisição direta de alteração recebe HTTP 403.
5. Faça logout.

## 7. Testes

```powershell
$env:PYTHONPATH='src'
python -m pytest -q
```

Resultado atual: `34 passed`.

Destaque `test_crypto.py`, `test_notas.py` e `test_fluxo.py`.

## 8. Limitações e encerramento

Explique que AS e TGS são módulos no mesmo processo, as chaves de serviço são
fixas e os dados ficam em JSON por decisão acadêmica.

> O usuário autentica com senha, o AS emite um TGT, o TGS emite um Service
> Ticket e o Portal valida ticket e autenticador antes da autenticação mútua.
> Professores administram notas e alunos consultam apenas seus registros.
