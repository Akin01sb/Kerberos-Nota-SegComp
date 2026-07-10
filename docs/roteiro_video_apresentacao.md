# Roteiro atualizado para o video

Tempo sugerido: 14 a 18 minutos.

Formato sugerido: quatro apresentadores. Cada pessoa pode ler a propria parte
quase literalmente. As instrucoes "mostrar na tela" servem para orientar a
gravacao, mas nao precisam ser lidas em voz alta.

## Preparacao antes de gravar

Antes de iniciar a gravacao, abra a raiz do projeto no terminal:

```powershell
cd <pasta-do-projeto>
```

Se o ambiente ainda nao estiver instalado:

```powershell
python -m pip install -e .
```

Para a demonstracao, use uma conta de professor e uma conta de aluno cujas
senhas sejam conhecidas. No projeto atual, os perfis cadastrados em
`data/usuarios.json` incluem:

- `SilvioSants`, perfil `professor`;
- `AkinGOD777`, perfil `aluno`;
- `kassio`, perfil `professor`;
- `kassio12` e `malululu10`, perfil `aluno`.

As senhas nao ficam salvas em texto claro. Se a senha de alguma conta nao for
conhecida, crie contas temporarias antes de gravar:

```powershell
python scripts/criar_usuario.py
```

Para rodar o sistema durante a gravacao:

Terminal 1:

```powershell
python scripts/iniciar_servidores.py
```

Terminal 2:

```powershell
python run.py
```

Depois acesse:

```text
http://127.0.0.1:5000
```

## Divisao geral

| Parte | Apresentador | Tema | Tempo aproximado |
|---|---|---|---|
| 1 | Apresentador 1 | Objetivo, requisitos e arquitetura | 3 a 4 min |
| 2 | Apresentador 2 | KDF, AS e emissao do TGT | 4 a 5 min |
| 3 | Apresentador 3 | TGS, Service Ticket e Portal de Notas | 4 a 5 min |
| 4 | Apresentador 4 | Demonstracao, testes, limitacoes e conclusao | 4 a 5 min |

## Mapa de requisitos e evidencias

Esta parte pode ser usada como cola tecnica antes da gravacao. A recomendacao e
citar estes pontos no video, porque eles mostram claramente que os requisitos
do trabalho foram cobertos.

| Requisito | Onde esta atendido | Evidencia para mostrar/falar |
|---|---|---|
| Implementar Kerberos usando exclusivamente criptografia de chave simetrica | `crypto/crypto_utils.py`, `config.py`, `kerberos/as_server.py`, `kerberos/tgs_server.py`, `notes/portal_notas.py` | O projeto usa AES-GCM com chaves compartilhadas de 32 bytes, HMAC-SHA256, PBKDF2-HMAC-SHA256, nonces e timestamps. Nao ha RSA, chave publica ou biblioteca pronta de Kerberos. |
| Implementar o Servidor de Autenticacao, AS | `servidores/servidor_as.py` e `kerberos/as_server.py` | O AS roda em socket TCP na porta 9001, entrega salt/desafio, valida a prova HMAC e emite o TGT. |
| Implementar o Ticket Granting Server, TGS | `servidores/servidor_tgs.py` e `kerberos/tgs_server.py` | O TGS roda em socket TCP na porta 9002, abre o TGT com a chave secreta do TGS, valida autenticador e emite Service Ticket. |
| Implementar pelo menos um servico protegido por Kerberos | `servidores/servidor_notas.py`, `notes/portal_notas.py`, `notes/service.py` | O servico protegido e o Portal de Notas, rodando na porta 9003. Ele exige Service Ticket e autenticador para autenticar e executar operacoes. |
| Permitir autenticacao por senha | `client/routes.py`, `crypto/kdf.py`, `data/usuarios.json` | O usuario informa senha no login. A senha e usada localmente para derivar chave. O arquivo de usuarios guarda salt, verificador e perfil, nao senha em texto claro. |
| Derivar a chave do cliente usando KDF | `crypto/kdf.py` | A funcao `derivar_chave_senha` usa PBKDF2-HMAC-SHA256, salt de 16 bytes, chave de 32 bytes e 200 mil iteracoes. |
| Emitir, distribuir e validar tickets | `kerberos/tickets.py`, `kerberos/as_server.py`, `kerberos/tgs_server.py`, `notes/portal_notas.py` | O AS emite TGT, o TGS valida TGT e emite Service Ticket, e o Portal valida o Service Ticket antes de qualquer operacao. |
| Implementar autenticacao mutua entre cliente e servico | `client/routes.py` e `notes/portal_notas.py` | O cliente envia Service Ticket e autenticador; o Portal responde cifrado com timestamp + 1 e nonce; o cliente valida essa confirmacao. |
| Seguir o fluxo Cliente, AS, TGS e Servico apresentado em sala | `client/routes.py`, `rede/cliente_tcp.py`, `servidores/*`, `tests/test_rede.py` | O fluxo real passa por AS na 9001, TGS na 9002 e Portal na 9003. O teste de rede sobe os tres sockets reais e valida o fluxo completo. |

Fala curta recomendada para antes da demonstracao:

> Antes de demonstrar a tela, vamos mapear os requisitos. O projeto tem AS,
> TGS e servico de notas como processos separados por sockets TCP. A
> autenticacao com senha passa por KDF, a senha nao atravessa a rede, o AS
> emite o TGT, o TGS emite o Service Ticket e o Portal de Notas exige ticket,
> autenticador, nonce, timestamp e requisicao criptografada em cada operacao.
> Toda a criptografia usada e baseada em chaves simetricas e primitivas basicas:
> AES-GCM, HMAC-SHA256, PBKDF2-HMAC-SHA256 e geracao segura de numeros
> aleatorios.

## Guia de tela com linhas atuais

Use esta parte como roteiro de gravacao do codigo. As linhas abaixo sao as
linhas atuais do projeto; se alguma edicao futura mudar a numeracao, procure
pelo nome do arquivo e da funcao indicada.

### Cena 1: processos separados e sockets TCP

Mostrar:

- `scripts/iniciar_servidores.py`, linhas 16, 20 e 24;
- `src/kerberos_notas/rede/servidor.py`, linhas 6, 19 e 31;
- `src/kerberos_notas/rede/protocolo.py`, linhas 24 e 37;
- `src/kerberos_notas/rede/cliente_tcp.py`, linhas 13, 35, 36, 50, 67 e 95;
- `run.py`, linha 11.

Fala para ler:

> Aqui mostramos que AS, TGS e Portal de Notas nao estao apenas separados em
> funcoes. O script `iniciar_servidores.py` cria tres processos diferentes. O
> servidor TCP usa `ThreadingTCPServer`, recebe uma mensagem JSON pelo socket,
> processa a acao e responde pelo mesmo canal. O Flask e iniciado com
> `usar_rede=True`, entao o cliente web chama AS, TGS e Notas pela rede local,
> nao por chamada direta de funcao.

O que destacar na tela:

- `multiprocessing.Process` para AS, TGS e Notas;
- `ThreadingTCPServer`;
- `enviar_mensagem` e `receber_mensagem`;
- metodos `solicitar_parametros_as`, `solicitar_ticket_servico` e
  `executar_operacao`.

### Cena 2: criptografia simetrica e primitivas permitidas

Mostrar:

- `src/kerberos_notas/config.py`, linhas 6, 10, 15 e 16;
- `src/kerberos_notas/crypto/crypto_utils.py`, linhas 4, 26, 33, 38, 50, 55 e
  59.

Fala para ler:

> Este ponto atende ao requisito de usar criptografia de chave simetrica. As
> chaves compartilhadas do TGS e do Portal ficam em `config.py`, e os pacotes
> protegidos sao cifrados com AES-GCM. O AES-GCM e simetrico: a mesma chave e
> usada para cifrar e decifrar. Ele tambem autentica o ciphertext, entao uma
> mensagem adulterada falha na descriptografia.

O que destacar na tela:

- `CHAVE_SECRETA_TGS`;
- `CHAVE_SECRETA_SERVICO_NOTAS`;
- `AESGCM`;
- `criptografar_json`;
- `descriptografar_json`.

### Cena 3: senha do usuario, KDF e prova HMAC

Mostrar:

- `src/kerberos_notas/crypto/kdf.py`, linhas 8, 37, 41 e 71;
- `src/kerberos_notas/client/routes.py`, linhas 53, 54, 59 e 83;
- `data/usuarios.json`, mostrando apenas `salt`, `verificador` e `perfil`.

Fala para ler:

> A senha e usada para autenticar o usuario, mas nao atravessa a rede. O
> cliente recebe do AS o salt e o desafio, deriva a chave com
> PBKDF2-HMAC-SHA256 em 200 mil iteracoes e cria uma prova HMAC do desafio.
> No arquivo de usuarios nao existe senha em texto claro; existem salt,
> verificador e perfil.

O que destacar na tela:

- `ITERACOES_PBKDF2 = 200_000`;
- `hashlib.pbkdf2_hmac`;
- `gerar_prova_as`;
- no JSON, a ausencia de campo `senha`.

### Cena 4: AS, desafio e emissao do TGT

Mostrar:

- `src/kerberos_notas/servidores/servidor_as.py`, linhas 14 e 17;
- `src/kerberos_notas/kerberos/as_server.py`, linhas 66, 87, 105, 115, 118, 134
  e 157;
- `src/kerberos_notas/kerberos/tickets.py`, linha 20.

Fala para ler:

> O AS implementa a primeira etapa do Kerberos. Na acao `obter_parametros`, ele
> cria um desafio e devolve salt, iteracoes da KDF e desafio. Na acao
> `autenticar`, ele valida a prova HMAC. Se a prova estiver correta, o AS emite
> o TGT. O TGT e cifrado com a chave secreta do TGS, entao o cliente carrega o
> ticket, mas nao consegue abrir seu conteudo.

O que destacar na tela:

- `criar_desafio_as`;
- retorno com `iteracoes_kdf`;
- `autenticar_no_as_com_prova`;
- `prova_esperada = gerar_prova_as`;
- `tgt_criptografado = criptografar_json(CHAVE_SECRETA_TGS, tgt)`;
- `return criptografar_json(chave_cliente, resposta_para_cliente)`;
- `criar_tgt`.

### Cena 5: TGS e Service Ticket

Mostrar:

- `src/kerberos_notas/servidores/servidor_tgs.py`, linha 10;
- `src/kerberos_notas/kerberos/tgs_server.py`, linhas 27, 59, 64, 109, 116,
  122, 128, 131 e 154;
- `src/kerberos_notas/kerberos/tickets.py`, linha 41.

Fala para ler:

> O TGS recebe o TGT e um autenticador Cliente-TGS. Primeiro ele abre o TGT com
> a chave secreta do TGS. Depois valida usuario, validade e autenticador. Se
> estiver tudo correto, ele cria uma chave Cliente-Servico e emite um Service
> Ticket para o servico `notas`. Esse Service Ticket e cifrado com a chave
> secreta do Portal de Notas.

O que destacar na tela:

- `CHAVES_SERVICOS = {"notas": CHAVE_SECRETA_SERVICO_NOTAS}`;
- `validar_tgt`;
- `descriptografar_json(CHAVE_SECRETA_TGS, tgt_criptografado)`;
- `emitir_ticket_servico`;
- `criar_ticket_servico`;
- `ticket_servico_criptografado`;
- `resposta_cliente`.

### Cena 6: autenticadores, timestamp, nonce e replay

Mostrar:

- `src/kerberos_notas/kerberos/authenticator.py`, linhas 11, 32 e 37;
- `src/kerberos_notas/kerberos/tgs_server.py`, linhas 23, 42, 53 e 54;
- `src/kerberos_notas/notes/portal_notas.py`, linhas 28, 53, 64 e 65.

Fala para ler:

> Os autenticadores impedem que alguem use apenas um ticket capturado. Eles sao
> cifrados com a chave de sessao e carregam usuario, timestamp e nonce. O TGS e
> o Portal guardam nonces ja utilizados; se o mesmo nonce aparecer novamente, a
> requisicao e tratada como possivel replay.

O que destacar na tela:

- `criar_autenticador`;
- campos `usuario`, `timestamp` e `nonce`;
- caches `NONCES_TGS_UTILIZADOS` e `NONCES_UTILIZADOS`;
- mensagens de erro de replay.

### Cena 7: autenticacao mutua cliente-servico

Mostrar:

- `src/kerberos_notas/client/routes.py`, linhas 112, 129 e 136;
- `src/kerberos_notas/notes/portal_notas.py`, linhas 98, 119, 122 e 131.

Fala para ler:

> Aqui esta a autenticacao mutua entre cliente e servico. O cliente envia o
> Service Ticket e um autenticador para o Portal. O Portal abre o ticket, valida
> o autenticador e responde com uma confirmacao criptografada contendo o
> timestamp incrementado e o nonce recebido. O cliente valida essa confirmacao,
> entao ele sabe que esta falando com o servico correto.

O que destacar na tela:

- criacao do `autenticador_portal`;
- chamada `autenticar_portal`;
- `validar_confirmacao_portal`;
- `timestamp_resposta = autenticador["timestamp"] + 1`;
- `nonce_autenticador`.

### Cena 8: operacoes do Portal protegidas por Kerberos

Mostrar:

- `src/kerberos_notas/client/routes.py`, linhas 189, 200, 204, 219, 360, 375,
  404 e 434;
- `src/kerberos_notas/notes/portal_notas.py`, linhas 197, 211, 229, 248, 261,
  160, 170, 178 e 188;
- `src/kerberos_notas/notes/service.py`, linhas 48, 63, 94, 128 e 153.

Fala para ler:

> O Kerberos nao protege apenas o login. Cada operacao do sistema de notas passa
> por `executar_operacao_kerberos`. A requisicao e cifrada com AES-GCM, recebe
> um nonce, uma acao e um hash. No Portal, a funcao
> `processar_operacao_portal` valida ticket, autenticador, usuario, nonce, acao
> e hash antes de chamar a regra de negocio. Professor pode criar, editar e
> excluir notas. Aluno pode apenas consultar as proprias notas.

O que destacar na tela:

- `requisicao_criptografada`;
- `hash_requisicao`;
- `cliente_tcp.executar_operacao`;
- `processar_operacao_portal`;
- comparacao do hash com `hmac.compare_digest`;
- acoes `criar_nota`, `criar_notas`, `editar_nota` e `excluir_nota`;
- `PermissionError("Acesso negado: aluno nao pode alterar notas.")`.

### Cena 9: testes que comprovam o fluxo

Mostrar:

- `tests/test_rede.py`, linhas 92, 101, 111, 121, 140, 154, 162, 187, 216 e
  222;
- terminal executando `python -m pytest -q`.

Fala para ler:

> Para evidenciar que o fluxo nao e apenas teorico, o teste de rede sobe AS,
> TGS e Notas em sockets TCP reais. Ele autentica professor, cria nota, edita,
> cria lote, carrega painel, autentica aluno, bloqueia operacao proibida e
> tambem verifica que a senha nao aparece nas requisicoes enviadas ao AS. O
> resultado atual da suite e 48 testes passando.

O que destacar na tela:

- `test_fluxo_completo_passa_por_tres_servidores_tcp`;
- chamadas de `executar_operacao_kerberos`;
- `test_senha_nao_atravessa_a_rede`;
- saida `48 passed`.

---

# Apresentador 1: objetivo, requisitos e arquitetura

## Mostrar na tela

Mostre rapidamente:

- `README.md`;
- estrutura `src/kerberos_notas/`;
- `scripts/iniciar_servidores.py`;
- `src/kerberos_notas/config.py`;
- `src/kerberos_notas/rede/protocolo.py`;
- `src/kerberos_notas/rede/servidor.py`.

## Fala para ler

O nosso projeto e um Portal de Notas Escolares protegido por uma implementacao
academica do protocolo Kerberos.

A ideia principal e que o usuario nao acesse diretamente o servico de notas
apenas com usuario e senha. Em vez disso, ele passa por um fluxo de
autenticacao baseado em tickets. Primeiro ele se autentica no servidor de
autenticacao, depois solicita um ticket de servico ao TGS, e somente depois
consegue acessar o Portal de Notas.

Um ponto importante do requisito do trabalho e que nao poderiamos usar uma
implementacao pronta de Kerberos. Entao o projeto nao usa biblioteca que
automatize o protocolo. O que usamos sao primitivas criptograficas basicas:
PBKDF2 com SHA-256 para derivacao de chave, HMAC-SHA256 para prova de posse da
senha, AES-GCM para confidencialidade e integridade das mensagens, geracao de
bytes aleatorios pelo sistema operacional, timestamps e nonces para reduzir
risco de replay.

A arquitetura atual foi separada em quatro processos principais:

```text
Navegador -> Cliente Flask :5000
                    |
                    +-> AS    :9001
                    +-> TGS   :9002
                    +-> Notas :9003
```

O Flask, que roda na porta 5000, e a interface web e tambem atua como cliente
Kerberos. Ele recebe o login pelo navegador, mas os servidores Kerberos ficam
separados. O AS roda na porta 9001, o TGS na porta 9002 e o Portal de Notas na
porta 9003.

Essa separacao e feita de verdade por sockets TCP. O arquivo
`scripts/iniciar_servidores.py` inicia tres processos separados: um processo
para o AS, um para o TGS e um para o servidor de Notas. Cada processo abre uma
porta TCP e fica aguardando requisicoes.

No arquivo `src/kerberos_notas/rede/protocolo.py`, o protocolo de rede envia
mensagens JSON com um cabecalho de 4 bytes informando o tamanho da mensagem.
Isso evita depender de uma quebra de linha ou de uma leitura parcial do socket.
O limite de mensagem tambem e controlado para evitar mensagens grandes demais.

No arquivo `src/kerberos_notas/rede/servidor.py`, temos um servidor TCP baseado
em `socketserver.ThreadingTCPServer`. Para cada conexao, ele recebe a mensagem,
identifica a acao solicitada, chama a funcao de processamento daquele servidor
e devolve uma resposta padronizada com sucesso ou erro.

Aqui e importante destacar a divisao de responsabilidades:

- o AS valida a identidade inicial e emite o TGT;
- o TGS valida o TGT e emite o Service Ticket;
- o Portal de Notas valida o Service Ticket e executa as operacoes protegidas;
- o Flask apenas coordena o fluxo e renderiza a interface para o navegador.

Com isso, o Kerberos nao esta sendo usado apenas no login. Ele tambem protege
as operacoes do servico. No projeto atual, acoes como carregar painel, criar
nota, criar varias notas, editar nota e excluir nota passam por uma requisicao
criptografada e por um autenticador novo.

Transicao:

Agora vamos entrar na primeira etapa tecnica do fluxo: a derivacao de chave,
o desafio do AS e a emissao do Ticket Granting Ticket.

---

# Apresentador 2: KDF, AS e emissao do TGT

## Mostrar na tela

Mostre:

- `src/kerberos_notas/crypto/kdf.py`;
- `src/kerberos_notas/crypto/crypto_utils.py`;
- `src/kerberos_notas/kerberos/as_server.py`;
- `src/kerberos_notas/servidores/servidor_as.py`;
- `data/usuarios.json`, sem mostrar ou falar senhas.

## Fala para ler

Agora vamos explicar a parte do AS, que e o Authentication Server, ou Servidor
de Autenticacao.

O primeiro cuidado do projeto e que a senha nao deve trafegar pela rede. No
login, o usuario digita a senha no navegador, o Flask recebe essa senha e usa
ela localmente para derivar uma chave. O AS nao recebe a senha em texto claro.

O arquivo principal dessa etapa e `src/kerberos_notas/crypto/kdf.py`. Nele,
a funcao `derivar_chave_senha` usa PBKDF2-HMAC-SHA256. Os parametros atuais
sao:

- salt de 16 bytes;
- chave final de 32 bytes;
- 200 mil iteracoes;
- algoritmo SHA-256.

O salt fica salvo em `data/usuarios.json`, junto com um verificador da chave.
Esse arquivo nao guarda senha. Ele guarda, para cada usuario, o salt, o
verificador e o perfil, que pode ser `professor` ou `aluno`.

O fluxo com o AS funciona em duas chamadas de rede. A primeira chamada e para
pedir os parametros de autenticacao. O cliente manda o nome do usuario para o
AS, e o AS devolve o salt, a quantidade de iteracoes da KDF e um desafio
aleatorio.

No codigo, essa etapa aparece em `servidor_as.py`, na acao
`obter_parametros`, que chama `criar_desafio_as` em `as_server.py`.

Depois disso, o cliente deriva a chave localmente usando a senha digitada e o
salt recebido. A partir dessa chave derivada, o projeto calcula uma chave de
autenticacao para o AS usando SHA-256. Com essa chave, o cliente cria uma
prova HMAC-SHA256 sobre uma mensagem formada pelo usuario e pelo desafio.

Em outras palavras, o cliente prova que conhece a senha sem enviar a senha.
Ele envia apenas:

- o usuario;
- o desafio recebido;
- a prova HMAC.

O AS pega o verificador salvo do usuario, calcula qual prova seria esperada e
compara usando `hmac.compare_digest`. Essa comparacao evita problemas de
timing em comparacoes de strings.

O desafio tambem tem protecao contra reutilizacao. Em `as_server.py`, existe
um dicionario chamado `DESAFIOS_AS`, protegido por `RLock`. Quando o desafio e
usado, ele e removido da memoria. Alem disso, ele expira em 60 segundos. Assim,
se alguem capturar uma prova antiga e tentar reutilizar, o AS rejeita.

Se a prova for valida, o AS emite o TGT, que e o Ticket Granting Ticket. O AS
tambem gera uma chave de sessao chamada chave Cliente-TGS. Essa chave sera
usada pelo cliente para conversar com o TGS.

O TGT possui informacoes como:

- usuario;
- identificador do TGS;
- chave de sessao Cliente-TGS;
- timestamp de emissao;
- tempo de validade;
- timestamp de expiracao;
- nonce.

Mas o cliente nao consegue abrir o TGT. O TGT e criptografado com a chave
secreta do TGS, configurada em `src/kerberos_notas/config.py` como
`CHAVE_SECRETA_TGS`. Isso segue a ideia do Kerberos: o cliente carrega o ticket,
mas quem consegue ler e validar esse ticket e o TGS.

A resposta do AS para o cliente tambem e protegida com AES-GCM. Ela contem a
chave Cliente-TGS e o TGT criptografado. O AES-GCM e usado porque oferece
confidencialidade e tambem autenticidade da mensagem: se alguem adulterar o
ciphertext, a descriptografia falha.

No arquivo `crypto_utils.py`, isso esta concentrado nas funcoes
`criptografar_json` e `descriptografar_json`. Cada pacote criptografado guarda
um `nonce` e um `ciphertext`, ambos em Base64 para facilitar trafego via JSON.

Resumindo esta etapa: o AS nao recebe senha em texto claro, valida uma prova
criptografica baseada em desafio, emite uma chave de sessao Cliente-TGS e
entrega um TGT que somente o TGS consegue abrir.

Transicao:

Com o TGT em maos, o cliente ainda nao acessa o Portal de Notas diretamente.
Ele precisa pedir ao TGS um ticket especifico para o servico de notas.

---

# Apresentador 3: TGS, Service Ticket e Portal de Notas

## Mostrar na tela

Mostre:

- `src/kerberos_notas/kerberos/tgs_server.py`;
- `src/kerberos_notas/kerberos/authenticator.py`;
- `src/kerberos_notas/kerberos/tickets.py`;
- `src/kerberos_notas/servidores/servidor_tgs.py`;
- `src/kerberos_notas/servidores/servidor_notas.py`;
- `src/kerberos_notas/notes/portal_notas.py`;
- `src/kerberos_notas/notes/service.py`;
- `src/kerberos_notas/client/routes.py`.

## Fala para ler

Depois que o cliente recebe o TGT do AS, ele chama o TGS, que e o Ticket
Granting Server. Essa etapa acontece pela porta 9002.

O cliente envia para o TGS tres informacoes principais:

- o usuario;
- o TGT emitido pelo AS;
- um autenticador Cliente-TGS.

O autenticador e criado no arquivo `authenticator.py`. Ele e um pequeno JSON
criptografado com a chave de sessao Cliente-TGS. Dentro dele ficam o usuario,
um timestamp e um nonce. Para operacoes no Portal, ele tambem pode carregar a
acao e o hash da requisicao.

No TGS, o arquivo `tgs_server.py` faz as validacoes. Primeiro, o TGS tenta abrir
o TGT usando a chave secreta do TGS. Se o TGT foi adulterado, ou se nao foi
criptografado com a chave correta, a abertura falha.

Depois, o TGS verifica se o TGT pertence ao mesmo usuario que fez a requisicao,
se existe chave de sessao Cliente-TGS, e se o ticket ainda esta dentro do prazo
de validade. O tempo de validade usado no projeto e de 10 minutos.

Em seguida, o TGS valida o autenticador. Ele abre o autenticador com a chave
Cliente-TGS que veio dentro do TGT. Isso prova que o cliente recebeu a resposta
do AS e conhece a chave de sessao correta.

O autenticador tambem tem timestamp e nonce. O timestamp precisa estar dentro
de uma janela maxima de 5 minutos, e o nonce e salvo em cache. Se o mesmo nonce
for usado de novo para o mesmo usuario, o TGS rejeita a requisicao como
possivel replay.

Se tudo estiver correto, o TGS emite duas coisas:

- uma chave de sessao Cliente-Servico;
- um Service Ticket para o servico `notas`.

O Service Ticket e criptografado com a chave secreta do Portal de Notas,
`CHAVE_SECRETA_SERVICO_NOTAS`. Assim como no TGT, o cliente carrega esse ticket,
mas nao precisa abrir esse conteudo. Quem abre e o servico de notas.

Ao mesmo tempo, o TGS envia ao cliente uma resposta criptografada com a chave
Cliente-TGS. Essa resposta contem a chave Cliente-Servico, que sera usada nas
mensagens com o Portal de Notas.

Agora entramos no servidor de Notas, que roda na porta 9003.

Antes de executar qualquer CRUD, o cliente faz uma autenticacao mutua com o
Portal. Ele envia o Service Ticket e um autenticador Cliente-Servico. O Portal
abre o Service Ticket com sua chave secreta, pega a chave Cliente-Servico que
esta dentro dele e usa essa chave para abrir o autenticador.

Se tudo estiver correto, o Portal responde com uma confirmacao criptografada.
Essa confirmacao inclui o timestamp do autenticador incrementado em 1 e o mesmo
nonce recebido. O cliente valida essa resposta. Esse detalhe mostra
autenticacao mutua: o cliente sabe que falou com alguem que realmente conseguiu
abrir o Service Ticket e usar a chave de sessao correta.

Depois dessa autenticacao inicial, cada operacao do Portal continua protegida.
No arquivo `routes.py`, a funcao `executar_operacao_kerberos` cria uma nova
requisicao para cada acao. Por exemplo:

- `carregar_painel`;
- `criar_nota`;
- `criar_notas`;
- `editar_nota`;
- `excluir_nota`.

Essa funcao monta uma requisicao com usuario, acao, dados e nonce. Depois
calcula um hash SHA-256 da requisicao e cria um autenticador novo contendo a
acao e o hash. A requisicao em si e criptografada com AES-GCM usando a chave
Cliente-Servico.

No Portal, o arquivo `portal_notas.py` valida tudo de novo:

- valida o Service Ticket;
- valida o autenticador;
- confere se o usuario da requisicao e o mesmo usuario do ticket;
- confere se o nonce da requisicao e o mesmo nonce do autenticador;
- confere se a acao da requisicao e a mesma acao do autenticador;
- recalcula o hash da requisicao e compara com o hash informado no
  autenticador;
- verifica timestamp e replay por nonce.

Somente depois dessas validacoes o Portal chama as regras de negocio em
`notes/service.py`.

Na regra de negocio, o perfil do usuario define a autorizacao. Professor pode
listar alunos, criar notas, criar varias notas de uma vez, editar notas e
excluir notas. Aluno pode apenas consultar as proprias notas. Se um aluno tentar
alterar nota, a funcao levanta `PermissionError`.

O armazenamento das notas fica em `data/notas.json`, e o repositorio usa
bloqueio e escrita atomica para reduzir risco de corrupcao do arquivo durante
gravacoes.

Com isso, o fluxo atual atende ao objetivo principal: o Kerberos protege nao so
o login, mas tambem a utilizacao do servico de notas.

Transicao:

Agora vamos demonstrar o sistema rodando, mostrar os logs do fluxo e fechar com
os testes automatizados.

---

# Apresentador 4: demonstracao, testes e conclusao

## Mostrar na tela

Mostre:

- dois terminais, um para os servidores e outro para o Flask;
- navegador em `http://127.0.0.1:5000`;
- login como professor;
- tela de notas;
- bloco "Etapas da autenticacao Kerberos";
- login como aluno;
- execucao dos testes;
- `tests/test_rede.py`.

## Fala para ler

Agora vamos executar o projeto.

No primeiro terminal, iniciamos os tres servidores Kerberos:

```powershell
python scripts/iniciar_servidores.py
```

Esse comando sobe o AS, o TGS e o Portal de Notas como processos separados.
Cada um abre sua propria porta TCP. O AS escuta em 9001, o TGS em 9002, e o
Portal de Notas em 9003.

No segundo terminal, iniciamos o cliente Flask:

```powershell
python run.py
```

O `run.py` cria a aplicacao com `usar_rede=True`. Isso e importante porque,
nesse modo, o Flask nao chama as funcoes do AS, TGS e Portal diretamente em
memoria. Ele usa o cliente TCP definido em `rede/cliente_tcp.py`, ou seja, passa
pelas portas de rede.

Agora acessamos `http://127.0.0.1:5000`.

Primeiro vamos entrar com uma conta de professor. Na demonstracao, podemos usar
`SilvioSants` se a senha for conhecida. Caso a senha nao seja conhecida, usamos
uma conta temporaria criada antes com `scripts/criar_usuario.py`. Durante a
gravacao, nao mostramos a senha.

Ao fazer login, o sistema executa o fluxo completo:

1. o cliente pede parametros ao AS;
2. deriva a chave da senha com PBKDF2-HMAC-SHA256;
3. envia uma prova HMAC ao AS;
4. recebe o TGT e a chave Cliente-TGS;
5. solicita ao TGS o Service Ticket para `notas`;
6. faz autenticacao mutua com o Portal;
7. carrega o painel usando uma operacao Kerberos protegida.

Na tela do professor, conseguimos lancar nota. Vamos selecionar um aluno, por
exemplo `AkinGOD777`, escolher uma disciplina, informar uma nota e salvar. O
formulario tambem permite adicionar mais linhas, entao o professor consegue
lancar varias notas no mesmo envio.

Quando clicamos para salvar, o que acontece por baixo nao e apenas um POST
simples no Flask. O Flask cria uma requisicao criptografada, cria um
autenticador novo para a acao `criar_nota` ou `criar_notas`, envia tudo ao
Portal pela porta 9003 e valida a resposta criptografada do Portal.

Depois podemos editar uma nota. A edicao chama a acao `editar_nota`, tambem com
autenticador proprio, nonce novo, hash da requisicao e resposta AES-GCM. O mesmo
vale para excluir nota, usando a acao `excluir_nota`.

Agora vamos abrir o bloco "Etapas da autenticacao Kerberos". Ele mostra os logs
didaticos do fluxo, como TGT emitido, autenticador criado, Service Ticket
validado e autenticacao mutua concluida. Esses logs ajudam a demonstrar que o
processo nao ficou escondido apenas no codigo.

Em seguida, fazemos logout e entramos como aluno, por exemplo `AkinGOD777`, se
a senha for conhecida. Na tela do aluno, ele ve apenas as proprias notas. Ele
nao ve o formulario de lancamento, nem os botoes de salvar e excluir. Isso
mostra a parte de autorizacao por perfil.

Agora vamos mostrar os testes automatizados. Na raiz do projeto, executamos:

```powershell
python -m pytest -q
```

O resultado atual esperado e:

```text
48 passed
```

Os testes estao separados por responsabilidade:

- `test_crypto.py` verifica KDF, AES-GCM, nonces e adulteracao;
- `test_as_server.py` verifica autenticacao no AS, senha invalida, TGT e prova;
- `test_tgs.py` verifica TGT, autenticador, replay e Service Ticket;
- `test_notas.py` verifica autenticacao mutua, CRUD, permissoes e replay;
- `test_fluxo.py` verifica o fluxo completo integrado;
- `test_rede.py` e o mais importante para a separacao por sockets, porque ele
  sobe AS, TGS e Notas em portas TCP reais.

No `test_rede.py`, tambem existe um teste chamado
`test_senha_nao_atravessa_a_rede`. Ele registra as requisicoes enviadas ao AS e
confirma que a senha nao aparece nas mensagens. Isso reforca que a senha e
usada localmente para derivar chave, mas nao e enviada ao servidor.

Para finalizar, vamos falar das limitacoes. O projeto foi feito para fins
academicos, entao existem escolhas didaticas:

- as chaves padrao existem para facilitar a execucao, mas podem ser trocadas
  por variaveis de ambiente;
- os servidores usam TCP local, mas em um ambiente real entre maquinas seria
  recomendado usar TLS;
- o navegador conversa com o Flask por HTTP local, mas em producao seria
  necessario HTTPS;
- as sessoes e caches de replay ficam em memoria;
- as notas ficam em JSON, com bloqueio e escrita atomica, mas um banco de dados
  seria mais adequado em producao.

Mesmo com essas limitacoes, o projeto atende ao objetivo do trabalho: ele
implementa o fluxo Kerberos manualmente, usando apenas primitivas
criptograficas basicas, separa AS, TGS e servico de notas por sockets TCP, usa
KDF a partir da senha do usuario, emite TGT e Service Ticket, realiza
autenticacao mutua e protege as operacoes do sistema de notas com tickets,
autenticadores, nonces, timestamps, hash da requisicao e AES-GCM.

## Encerramento curto para ler

Com isso, nosso sistema demonstra uma versao simplificada, mas funcional, do
Kerberos aplicado a um Portal de Notas. O usuario se autentica sem enviar a
senha pela rede, recebe tickets temporarios, acessa o servico com autenticacao
mutua e cada operacao sensivel do Portal e validada criptograficamente antes de
ser executada.

---

# Ordem sugerida de gravacao

1. Apresentador 1 mostra a arquitetura e os arquivos de rede.
2. Apresentador 2 mostra KDF, AS, desafio, prova HMAC e TGT.
3. Apresentador 3 mostra TGS, Service Ticket, Portal e operacoes protegidas.
4. Apresentador 4 roda a demonstracao web e os testes.

# Checklist rapido antes de entregar o video

- AS, TGS e Portal aparecem rodando em portas separadas.
- O Flask foi iniciado com `python run.py`.
- A demonstracao mostra login de professor.
- A demonstracao mostra criacao ou edicao de nota.
- A demonstracao mostra login de aluno.
- O aluno nao consegue alterar notas.
- O bloco de etapas Kerberos aparece na interface.
- O comando `python -m pytest -q` mostra `48 passed`.
- Ninguem mostra senha na gravacao.
