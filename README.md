# Kerberos Notas / Chat Seguro

Projeto academico com uma implementacao simplificada do protocolo Kerberos usando
criptografia simetrica.

O sistema possui:

- Cliente com login por usuario e senha
- KDF para derivar chave a partir da senha
- Authentication Server, AS
- Ticket Granting Server, TGS
- Tickets criptografados
- Servico de chat seguro
- Mensagens criptografadas
- HMAC para detectar adulteracao
- Testes automatizados do fluxo

## Requisitos

- Python 3.10 ou superior
- Git

## Como preparar o ambiente

No PowerShell, dentro da pasta do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Se o PowerShell bloquear a ativacao do ambiente virtual, rode:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Como rodar os testes

```powershell
$env:PYTHONPATH='src'
python -m pytest -q
```

Resultado esperado:

```text
24 passed
```

Esse resultado mostra que AS, TGS, tickets, autenticadores, chat seguro,
criptografia e HMAC estao funcionando nos cenarios testados.

## Como rodar a aplicacao web

```powershell
$env:PYTHONPATH='src'
python run.py
```

Depois acesse no navegador:

```text
http://127.0.0.1:5000
```

Usuarios de exemplo ficam em:

```text
data/usuarios.json
```

Para criar um novo usuario:

```powershell
$env:PYTHONPATH='src'
python scripts/criar_usuario.py
```

## Como testar o chat seguro

O chat seguro e testado principalmente por testes automatizados:

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_chat_seguro.py -q
```

Esse teste verifica:

- Ticket de servico valido para o chat
- Rejeicao de ticket expirado ou invalido
- Mensagem criptografada
- HMAC valido
- Deteccao de mensagem adulterada
- Rejeicao de usuario diferente do ticket
- Autenticacao mutua com chave correta
- Falha de autenticacao mutua com chave incorreta

## Como rodar uma demonstracao completa

Este script executa AS -> TGS -> Chat, envia uma mensagem criptografada e depois
adultera uma mensagem para mostrar o alerta de integridade:

```powershell
python scripts/demo_chat_seguro.py
```

Resultado esperado:

```text
AS validou senha e emitiu TGT
TGS emitiu ticket de servico para o chat
Texto aparece no pacote? False
Servico validou ticket, autenticador, HMAC e abriu mensagem
Mensagem adulterada foi aceita? False
```

## Documentos uteis

- `docs/README_TESTES_E_DEMO.md`: explicacao curta do projeto e como saber se funciona
- `docs/roteiro_video_apresentacao.md`: roteiro para gravar o video
- `docs/relatorio_tecnico_base.md`: base para o relatorio tecnico
- `docs/wireshark_chat_seguro.md`: demonstracao de confidencialidade com Wireshark
