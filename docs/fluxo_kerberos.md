# Fluxo Kerberos do Portal de Notas

```text
1. Cliente -> AS
   usuario
   solicitacao de autenticacao

2. AS -> Cliente
   resposta cifrada com a chave derivada da senha:
   - chave de sessao Cliente-TGS
   - TGT cifrado com a chave secreta do TGS

3. Cliente -> TGS
   - TGT
   - autenticador Cliente-TGS
   - servico solicitado: notas
   - TGS rejeita nonce Cliente-TGS reutilizado

4. TGS -> Cliente
   - Service Ticket cifrado com a chave do Portal
   - chave Cliente-Servico cifrada com a chave Cliente-TGS

5. Cliente -> Portal de Notas
   - Service Ticket
   - autenticador Cliente-Servico com usuario, timestamp e nonce

6. Portal -> Cliente
   confirmacao cifrada com a chave Cliente-Servico:
   - timestamp do autenticador incrementado
   - nonce recebido

7. Cliente
   valida a confirmacao e libera o painel conforme o perfil

8. Para cada operacao do Portal
   Cliente -> Portal:
   - o mesmo Service Ticket ainda valido
   - novo autenticador com acao, timestamp, nonce e hash
   - requisicao cifrada com AES-GCM

9. Portal -> Cliente
   - valida ticket, autenticador, nonce, acao e hash
   - rejeita reutilizacao do nonce
   - executa a operacao autorizada
   - devolve confirmacao e resultado cifrados

10. Cliente
    valida timestamp, nonce e acao antes de aceitar o resultado
```

O AS é o único componente que participa da validação inicial da senha. O TGS
recebe TGT e autenticador, sem receber a senha. O Portal recebe apenas o Service
Ticket e o autenticador Cliente-Serviço.

O ticket comprova que o TGS autorizou o acesso ao serviço `notas`. O
autenticador comprova que o cliente conhece a chave de sessão presente no
ticket. A resposta cifrada do Portal permite ao cliente confirmar que o serviço
também conhece essa chave, concluindo a autenticação mútua.

As operações `carregar_painel`, `criar_nota`, `editar_nota` e `excluir_nota`
seguem os passos 8 a 10. O AS e o TGS não são chamados novamente enquanto o
Service Ticket estiver válido.
