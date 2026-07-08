# Demonstracao do chat seguro com Wireshark

Este roteiro mostra como demonstrar que o chat usa Kerberos, criptografia e HMAC.

## Confidencialidade

1. Rode um pequeno script chamando `iniciar_servidor_chat` de `notes/chat_server.py`.
2. Em outro terminal, rode um cliente que use `montar_pacote_chat` e `enviar_pacote_chat`.
3. O cliente deve pedir um ticket de servico para o servico `chat`.
4. O cliente deve enviar uma mensagem usando o pacote montado pelo modulo `chat_client.py`.
5. O servico deve receber a mensagem usando o modulo `chat_server.py`.
6. Abra o Wireshark e comece a captura na interface de rede usada.
7. Envie uma mensagem com um texto facil de reconhecer, por exemplo `mensagem secreta`.
8. Use o filtro da porta usada pelo chat, por exemplo `tcp.port == 5050`.
9. Procure o texto `mensagem secreta` nos pacotes capturados.

O texto da mensagem nao deve aparecer em texto puro. O pacote leva apenas o campo
`conteudo_criptografado`, que possui `nonce` e `ciphertext`.

## Integridade

Para demonstrar integridade, altere manualmente algum campo da mensagem depois que
ela for criada, por exemplo `destinatario` ou `conteudo_criptografado`.

Quando o servico receber a mensagem alterada, a validacao de HMAC deve falhar com:

```text
Mensagem violada: integridade comprometida
```

Isso mostra que o receptor consegue detectar adulteracao.

## Autenticidade

Para demonstrar autenticidade, envie uma mensagem com `remetente` diferente do
usuario presente no ticket de servico.

O servico deve rejeitar a mensagem com:

```text
Identidade invalida: usuario nao corresponde ao ticket
```

Isso mostra que o chat confere se quem envia a mensagem e o mesmo usuario do ticket.
