# Resumo rapido do projeto

Este projeto simula o Kerberos para proteger o acesso a um sistema de notas e a
um chat seguro.

O fluxo principal e:

```text
Cliente -> AS -> TGS -> Servico protegido
```

O AS valida usuario e senha, o TGS emite ticket de servico, e o chat usa esse
ticket para aceitar mensagens criptografadas.

## Como testar rapido

Na raiz do projeto:

```powershell
$env:PYTHONPATH='src'
python -m pytest -q
```

Se aparecer algo parecido com isto, esta funcionando:

```text
24 passed
```

## Como saber que funciona de verdade

- Login valido: o AS aceita usuario e senha corretos
- Login invalido: o AS rejeita usuario inexistente ou senha errada
- TGT: o AS gera um TGT criptografado para o TGS
- Ticket de servico: o TGS valida o TGT e emite um ticket para `notas` ou `chat`
- Chat seguro: a mensagem nao aparece em texto puro no pacote
- Integridade: se a mensagem for alterada, o HMAC detecta
- Autenticidade: se o remetente for diferente do usuario do ticket, o chat rejeita
- Autenticacao mutua: o servico responde com confirmacao criptografada

## Testes mais importantes

```powershell
python -m pytest tests/test_as_server.py -q
python -m pytest tests/test_tgs.py -q
python -m pytest tests/test_chat_seguro.py -q
```

## Demonstracao simples para o professor

1. Rode todos os testes e mostre `24 passed`.
2. Rode `python scripts/demo_chat_seguro.py`.
3. Mostre que aparece `Texto aparece no pacote? False`.
4. Mostre `as_server.py` gerando TGT e chave Cliente-TGS.
5. Mostre `tgs_server.py` validando TGT e emitindo ticket de servico.
6. Mostre `chat_seguro.py` criptografando mensagem e calculando HMAC.
7. Mostre a mensagem adulterada falhando com:

```text
Mensagem violada: integridade comprometida
```
