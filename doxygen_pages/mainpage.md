# Kerberos Notas {#mainpage}

## Visao geral

O projeto e um Portal de Notas protegido por uma implementacao academica do
protocolo Kerberos. A aplicacao web Flask atua como cliente Kerberos, enquanto
AS, TGS e Servico de Notas rodam como processos separados e trocam mensagens
JSON por sockets TCP.

## Objetivo academico

O sistema demonstra autenticacao baseada em chaves simetricas, derivacao de
chaves a partir da senha, emissao de tickets, criacao de chaves de sessao,
autenticadores com timestamp e nonce, protecao contra replay e autenticacao
mutua entre cliente e servico.

## Arquitetura

Componentes existentes no codigo:

- Cliente Web Flask: rotas, sessao web e coordenacao do fluxo Kerberos.
- Servidor de Autenticacao AS: desafio inicial, validacao por prova HMAC e TGT.
- Ticket Granting Server TGS: validacao do TGT e emissao do Service Ticket.
- Servico de Notas: servico protegido por Kerberos e regras de professor/aluno.
- Camada de criptografia: PBKDF2-HMAC-SHA256, HMAC-SHA256, AES-GCM e Base64.
- Camada de rede TCP: envio e recebimento de mensagens JSON com tamanho
  prefixado.
- Persistencia em JSON: usuarios, perfis e notas.

## Fluxo Kerberos

1. Usuario informa login e senha no navegador.
2. Cliente Flask solicita salt, parametros da KDF e desafio ao AS.
3. Cliente deriva a chave localmente e envia uma prova HMAC do desafio.
4. AS valida a prova, emite uma chave Cliente-TGS e um TGT.
5. Cliente solicita ao TGS um ticket para o servico `notas`.
6. TGS valida TGT, autenticador, timestamp e nonce.
7. TGS emite o Service Ticket e a chave Cliente-Servico.
8. Cliente acessa o Servico de Notas com Service Ticket e autenticador.
9. Servico valida ticket, autenticador, permissao, nonce, timestamp e hash da
   requisicao.
10. Servico responde cifrado com timestamp incrementado e nonce, permitindo que
    o cliente valide a autenticacao mutua.

## Como navegar na documentacao

Use o menu lateral para acessar arquivos, classes, funcoes e codigo-fonte.
Os modulos mais importantes ficam em `src/kerberos_notas`: `client`, `crypto`,
`kerberos`, `notes`, `rede`, `servidores` e `storage`.

## Limitacoes academicas

As chaves padrao sao didaticas e podem ser substituidas por variaveis de
ambiente. O projeto usa TCP local, HTTP local, caches em memoria e persistencia
JSON. Esses pontos sao suficientes para a demonstracao academica, mas nao
substituem HTTPS/TLS, banco de dados e gestao robusta de segredos em producao.
