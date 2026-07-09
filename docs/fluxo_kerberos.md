# Fluxo Kerberos do Portal de Notas

```text
1. Cliente -> AS :9001
   - usuário
   - solicitação de parâmetros e desafio

2. Cliente
   - deriva a chave com PBKDF2-HMAC-SHA256
   - cria uma prova HMAC do desafio

3. Cliente -> AS :9001
   - usuário, desafio e prova
   - a senha não atravessa a rede

4. AS -> Cliente
   resposta AES-GCM:
   - chave de sessão Cliente-TGS
   - TGT cifrado com a chave secreta do TGS

5. Cliente -> TGS :9002
   - TGT
   - autenticador Cliente-TGS
   - serviço solicitado: notas

6. TGS -> Cliente
   - Service Ticket cifrado com a chave do Portal
   - chave Cliente-Serviço cifrada com a chave Cliente-TGS

7. Cliente -> Portal :9003
   - Service Ticket
   - autenticador Cliente-Serviço

8. Portal -> Cliente
   confirmação AES-GCM com timestamp incrementado e nonce recebido

9. Para cada operação
   Cliente -> Portal :9003:
   - Service Ticket ainda válido
   - autenticador novo com ação, timestamp, nonce e hash
   - requisição cifrada com AES-GCM

10. Portal -> Cliente
    - valida ticket, autenticador, nonce, ação e hash
    - executa a operação autorizada
    - devolve confirmação e resultado cifrados
```

AS, TGS e Portal são processos TCP separados. O AS armazena salt e um
verificador que representa a chave de longo prazo. O cliente usa a senha
somente para reproduzir essa chave localmente e responder ao desafio.

As operações `carregar_painel`, `criar_nota`, `criar_notas`, `editar_nota` e
`excluir_nota` seguem os passos 9 e 10. AS e TGS não são chamados novamente
enquanto o Service Ticket estiver válido.
