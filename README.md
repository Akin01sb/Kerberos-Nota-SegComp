# Portal de Notas Escolares com Kerberos

Projeto acadêmico da disciplina de Segurança Computacional. Ele implementa uma
versão simplificada do protocolo Kerberos, usando somente criptografia
simétrica, para proteger um Portal de Notas Escolares.

O foco é demonstrar:

- autenticação por senha sem armazená-la em texto puro;
- derivação de chave com PBKDF2-HMAC-SHA256;
- Authentication Server (AS) e Ticket Granting Server (TGS);
- Ticket Granting Ticket (TGT) e Service Ticket;
- autenticadores Cliente-TGS e Cliente-Serviço;
- autenticação mútua entre cliente e Portal de Notas;
- autorização dos perfis professor e aluno.

## Fluxo principal

```text
Cliente Web -> AS -> TGS -> Portal de Notas
```

1. O usuário informa nome e senha ao cliente.
2. O AS deriva uma chave da senha e valida o verificador armazenado.
3. O AS gera a chave Cliente-TGS e um TGT criptografado com a chave do TGS.
4. O cliente envia TGT e autenticador Cliente-TGS ao TGS.
5. O TGS emite um Service Ticket para `notas` e uma chave Cliente-Serviço.
6. O cliente envia Service Ticket e autenticador Cliente-Serviço ao Portal.
7. O Portal valida os dois e devolve uma confirmação criptografada.
8. O cliente valida timestamp e nonce da confirmação antes de liberar o painel.

AS e TGS são módulos Python executados no mesmo processo. Essa simplificação
mantém o projeto didático sem alterar as etapas lógicas do protocolo.

## Perfis

**Professor**

- visualiza os alunos cadastrados;
- lança, lista, edita e exclui notas.

**Aluno**

- visualiza somente as próprias notas;
- não pode criar, editar ou excluir registros.

Os perfis ficam em `data/usuarios.json`. Os dados escolares ficam em
`data/notas.json`.

Usuários atualmente cadastrados:

| Usuário | Perfil |
|---|---|
| `kassio` | professor |
| `AkinGOD777` | aluno |
| `kassio12` | aluno |
| `SilvioSants` | professor |

As senhas não aparecem no repositório. Para criar um usuário com uma senha
conhecida, use `python scripts/criar_usuario.py`.

## Executar

Requer Python 3.10 ou superior.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:PYTHONPATH='src'
python run.py
```

Acesse `http://127.0.0.1:5000`.

O terminal e o painel exibem etapas didáticas do fluxo Kerberos. A senha nunca
é incluída nesses logs.

## Testes

```powershell
$env:PYTHONPATH='src'
python -m pytest -q
```

Resultado atual:

```text
34 passed
```

Os testes cobrem KDF, AES-GCM, adulteração, AS, TGS, tickets, autenticadores,
autenticação mútua, permissões e o fluxo web completo.

## Estrutura

```text
src/kerberos_notas/
  client/      cliente web e integração do fluxo
  crypto/      PBKDF2, AES-GCM e Base64
  kerberos/    AS, TGS, tickets e autenticadores
  notes/       Portal de Notas e persistência
data/          usuários e notas em JSON
tests/         testes automatizados
docs/          relatório e roteiro de apresentação
```

## Limitações acadêmicas

- AS, TGS, cliente e Portal não são processos de rede separados.
- As chaves dos serviços ficam fixas em `config.py`.
- Usuários e notas são armazenados em JSON.
- As sessões Kerberos ficam em memória e são perdidas ao reiniciar o Flask.
- Não há cache de replay persistente para autenticadores.
- A chave secreta padrão do Flask deve ser substituída por `FLASK_SECRET_KEY`
  fora da demonstração local.
