# Roteiro para video de apresentacao

Tempo sugerido: 8 a 12 minutos.

Todos os integrantes devem falar pelo menos uma parte.

## 1. Abertura

Fala sugerida:

```text
Nosso projeto implementa uma versao simplificada do protocolo Kerberos usando
criptografia de chave simetrica. O objetivo e autenticar usuarios, emitir tickets
e proteger um servico de notas e um chat seguro.
```

Mostrar rapidamente a estrutura:

```text
src/kerberos_notas/crypto
src/kerberos_notas/kerberos
src/kerberos_notas/client
src/kerberos_notas/notes
tests
docs
```

## 2. Arquitetura geral

Fala sugerida:

```text
O fluxo principal e Cliente -> AS -> TGS -> Servico protegido. O cliente usa
senha apenas no inicio. Depois disso, o sistema passa a usar chaves de sessao e
tickets criptografados.
```

Explicar:

- Cliente envia usuario e senha
- AS valida e emite TGT
- Cliente usa TGT para pedir ticket ao TGS
- TGS emite ticket de servico
- Servico protegido valida o ticket

## 3. Pessoa 1: cliente, login e KDF

Arquivos para mostrar:

- `src/kerberos_notas/client/routes.py`
- `src/kerberos_notas/crypto/kdf.py`

Fala sugerida:

```text
A senha nao e usada diretamente como chave. Primeiro ela passa por uma KDF,
implementada com PBKDF2-HMAC-SHA256. O salt fica salvo no cadastro do usuario e
a chave derivada e usada para proteger a resposta do AS ao cliente.
```

Pontos importantes:

- `derivar_chave_senha`
- `gerar_salt`
- `gerar_verificador_chave`
- `verificar_senha`

## 4. Pessoa 2: Authentication Server, AS

Arquivo para mostrar:

- `src/kerberos_notas/kerberos/as_server.py`

Fala sugerida:

```text
O AS recebe usuario e senha, verifica se o usuario existe, deriva a chave da
senha e compara o verificador salvo. Se estiver correto, ele gera a chave de
sessao Cliente-TGS e cria o TGT.
```

Mostrar:

- `validar_usuario_no_as`
- `gerar_tgt`
- `autenticar_no_as`

Explicar que o TGT contem:

- usuario
- id_cliente
- chave_sessao_cliente_tgs
- timestamp_emissao
- timestamp_expiracao
- validade_segundos
- nonce

## 5. Pessoa 3: TGS e tickets de servico

Arquivo para mostrar:

- `src/kerberos_notas/kerberos/tgs_server.py`
- `src/kerberos_notas/kerberos/tickets.py`
- `src/kerberos_notas/kerberos/authenticator.py`

Fala sugerida:

```text
O TGS recebe o TGT e um autenticador do cliente. Ele descriptografa o TGT com a
chave secreta do TGS, valida o usuario, verifica validade e autentica o cliente.
Depois emite um ticket de servico.
```

Mostrar:

- `validar_tgt`
- `validar_autenticador`
- `emitir_ticket_servico`
- `abrir_ticket_servico`

## 6. Pessoa 4: chat seguro

Arquivos para mostrar:

- `src/kerberos_notas/notes/chat_seguro.py`
- `src/kerberos_notas/notes/chat_client.py`
- `src/kerberos_notas/notes/chat_server.py`
- `tests/test_chat_seguro.py`

Fala sugerida:

```text
O chat seguro usa o ticket emitido pelo TGS para o servico chat. Depois de
validar o ticket, ele usa a chave de sessao Cliente-Servico para criptografar a
mensagem e tambem para calcular o HMAC.
```

Mostrar:

- `validar_ticket_chat`
- `autenticar_servico_chat`
- `criar_mensagem_segura`
- `receber_mensagem_segura`
- `calcular_hmac_mensagem`

## 7. Autenticacao mutua

Fala sugerida:

```text
Na autenticacao mutua, o cliente envia um autenticador criptografado com a chave
de sessao. O servico valida esse autenticador e responde com uma confirmacao
criptografada usando a mesma chave. Se o cliente consegue abrir essa resposta e
o nonce bate, ele sabe que o servico tambem possui a chave correta.
```

Mostrar no teste:

- `test_autenticacao_mutua_funciona_com_chave_correta`
- `test_autenticacao_mutua_falha_com_chave_incorreta`

## 8. Algoritmos criptograficos

Fala sugerida:

```text
Usamos PBKDF2-HMAC-SHA256 para derivar chaves de senha, AES-GCM para criptografar
dados JSON e HMAC-SHA256 para verificar integridade das mensagens do chat.
```

Justificativa:

- PBKDF2 dificulta ataque de forca bruta por usar salt e muitas iteracoes
- AES-GCM oferece criptografia autenticada para os pacotes JSON
- HMAC-SHA256 permite detectar adulteracao de campos da mensagem

## 9. Demonstracao pratica

Comandos:

```powershell
$env:PYTHONPATH='src'
python -m pytest -q
python scripts/demo_chat_seguro.py
```

Resultado esperado:

```text
24 passed
Texto aparece no pacote? False
Mensagem adulterada foi aceita? False
```

Mostrar testes:

- AS aceita usuario valido
- TGS emite ticket de servico
- Chat criptografa mensagem
- HMAC detecta mensagem adulterada
- Usuario diferente do ticket e rejeitado

## 10. Wireshark

Fala sugerida:

```text
Para demonstrar confidencialidade com Wireshark, capturamos os pacotes do chat e
procuramos o texto original da mensagem. O texto nao aparece em claro, porque o
pacote trafega como nonce e ciphertext.
```

Usar como apoio:

- `docs/wireshark_chat_seguro.md`

## 11. Dificuldades e aprendizados

Fala sugerida:

```text
A principal dificuldade foi integrar as partes sem quebrar o contrato entre AS,
TGS e servico. Tambem foi importante manter os nomes dos campos compativeis,
principalmente no TGT e no ticket de servico. O principal aprendizado foi
entender como Kerberos evita enviar senha repetidamente e passa a confiar em
tickets e chaves de sessao.
```

## 12. Encerramento

Fala sugerida:

```text
Com isso, o projeto demonstra autenticacao por senha, emissao de tickets,
validacao pelo TGS, autenticacao mutua, confidencialidade com criptografia e
integridade com HMAC.
```
