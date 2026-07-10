# Roteiro completo para apresentacao - Portal de Notas com Kerberos

Este roteiro foi escrito para ser lido durante a apresentacao. A ideia e que
voce consiga seguir com tranquilidade, sem precisar improvisar muito.

Como usar:

- O texto entre parenteses indica o que mostrar na tela.
- A frase depois de `Frase para ler:` e o que deve ser falado.
- As instrucoes entre parenteses nao precisam ser lidas em voz alta.
- O tom deve ser calmo, natural e explicativo.

Tempo sugerido: 16 a 22 minutos.

Divisao:

- Apresentador 1: Kerberos, arquitetura, senha, KDF, AS e TGT.
- Apresentador 2: TGS, Service Ticket, autenticadores, replay e autenticacao
  mutua.
- Apresentador 3: Portal de Notas, professor, aluno, interface e logs.
- Apresentador 4: execucao, testes, Doxygen, limitacoes e conclusao.

Mensagem central da apresentacao:

> O projeto implementa uma simulacao academica do Kerberos para proteger um
> Portal de Notas. A senha e usada apenas no inicio, o AS emite o TGT, o TGS
> emite o Service Ticket, o Portal valida o acesso e cada operacao de notas
> continua protegida.

---

## Preparacao antes de gravar

(Abra dois terminais na raiz do projeto.)

Frase para ler:

> Antes de comecar a demonstracao, o projeto precisa estar rodando em dois
> terminais. Em um terminal ficam os servidores Kerberos, e no outro fica a
> aplicacao Flask, que e o cliente web.

(No primeiro terminal, mostre o comando abaixo.)

```powershell
python scripts/iniciar_servidores.py
```

Frase para ler:

> Neste primeiro terminal, a gente inicia os tres servidores do fluxo Kerberos:
> o AS, o TGS e o Portal de Notas. Eles rodam separados, cada um com sua porta.

(No segundo terminal, mostre o comando abaixo.)

```powershell
python run.py
```

Frase para ler:

> Neste segundo terminal, a gente inicia o Flask. Ele e a parte web que o usuario
> acessa pelo navegador, mas por tras ele conversa com AS, TGS e Portal usando
> sockets TCP.

(Mostre no navegador o endereco.)

```text
http://127.0.0.1:5000
```

Frase para ler:

> Com os dois terminais abertos, a aplicacao fica disponivel em
> `http://127.0.0.1:5000`.

Observacao para quem vai gravar: nao mostrar senhas durante a apresentacao.

---

# Apresentador 1 - Kerberos, arquitetura, senha, KDF, AS e TGT

## 1. Abertura

(Mostre o `README.md`, de preferencia o titulo e a parte de arquitetura.)

Frase para ler:

> O nosso projeto e um Portal de Notas Escolares protegido por uma simulacao
> academica do protocolo Kerberos. A ideia e mostrar, de forma pratica, como um
> usuario pode se autenticar uma vez e depois acessar um servico protegido
> usando tickets, chaves de sessao e autenticadores.

(Mostre ainda o `README.md`, na parte que fala que o projeto nao usa biblioteca pronta de Kerberos.)

Frase para ler:

> Um ponto importante do trabalho e que a gente nao usa uma implementacao pronta
> de Kerberos. O protocolo foi montado no codigo usando primitivas basicas de
> criptografia, como PBKDF2, HMAC, AES-GCM, timestamps e nonces.

(Mostre rapidamente a estrutura da pasta `src/kerberos_notas` no VS Code.)

Frase para ler:

> O projeto esta separado por responsabilidade. Temos a parte do cliente web,
> a parte de criptografia, os modulos do Kerberos, a camada de rede, os
> servidores TCP e o servico de notas. Essa separacao ajuda a deixar claro onde
> cada etapa do protocolo acontece.

## 2. Arquitetura geral

(Mostre `README.md`, na arquitetura com as portas 5000, 9001, 9002 e 9003.)

Frase para ler:

> A arquitetura principal fica assim: o navegador acessa o Flask na porta 5000.
> O Flask atua como Cliente Kerberos. Ele conversa com o AS na porta 9001, com o
> TGS na porta 9002 e com o Portal de Notas na porta 9003.

(Mostre `scripts/iniciar_servidores.py`, destacando os `multiprocessing.Process`.)

Frase para ler:

> Aqui no arquivo `scripts/iniciar_servidores.py`, da para ver que AS, TGS e
> Portal de Notas sao iniciados como processos separados. Isso e importante
> porque o nosso projeto nao deixa tudo misturado em uma unica funcao. Cada
> servidor tem seu proprio papel dentro do fluxo.

(Mostre `run.py`, destacando `app = create_app(usar_rede=True)`.)

Frase para ler:

> E aqui no `run.py`, o Flask e criado com `usar_rede=True`. Isso significa que
> a aplicacao web usa os servidores TCP reais. Entao, durante a execucao normal,
> o Cliente Web passa de fato por AS, TGS e Portal de Notas.

(Mostre `src/kerberos_notas/rede/cliente_tcp.py`.)

Frase para ler:

> A comunicacao entre o Flask e os servidores fica neste arquivo,
> `cliente_tcp.py`. Ele tem metodos para solicitar parametros ao AS, enviar a
> prova ao AS, pedir ticket ao TGS, autenticar no Portal e executar operacoes de
> notas. Isso mostra o caminho do Cliente ate cada componente.

## 3. Criptografia usada no projeto

(Mostre `src/kerberos_notas/crypto/crypto_utils.py`, destacando `AESGCM`.)

Frase para ler:

> Para proteger as mensagens, o projeto usa AES-GCM. Ele e um algoritmo de
> criptografia simetrica autenticada. Isso quer dizer que, alem de esconder o
> conteudo, ele tambem detecta adulteracao. Se alguem mudar o ciphertext, a
> descriptografia falha.

(Mostre no mesmo arquivo as funcoes `criptografar_json` e `descriptografar_json`.)

Frase para ler:

> Essas duas funcoes sao usadas em varias partes do projeto. Tickets,
> autenticadores, respostas do AS, respostas do TGS e respostas do Portal sao
> transportados como JSON cifrado com AES-GCM.

(Mostre `src/kerberos_notas/config.py`, destacando as chaves do TGS e do servico de notas.)

Frase para ler:

> As chaves compartilhadas dos servidores ficam centralizadas no `config.py`.
> Existe uma chave secreta para o TGS e uma chave secreta para o Portal de
> Notas. Elas tem valores didaticos padrao para facilitar a execucao local, mas
> tambem podem ser substituidas por variaveis de ambiente.

## 4. Senha e KDF

(Mostre a tela de login no navegador, sem digitar ou mostrar senha ainda.)

Frase para ler:

> Agora vamos falar da senha. O usuario informa usuario e senha no login, mas a
> senha nao e enviada diretamente para o AS, para o TGS ou para o Portal. Ela e
> usada localmente pelo cliente para derivar uma chave.

(Mostre `src/kerberos_notas/crypto/kdf.py`, destacando `ITERACOES_PBKDF2 = 200_000`.)

Frase para ler:

> No arquivo `kdf.py`, a funcao principal de derivacao usa
> PBKDF2-HMAC-SHA256. O projeto usa 200 mil iteracoes, um salt de 16 bytes e
> gera uma chave de 32 bytes. Isso atende ao requisito de derivar a chave do
> cliente a partir da senha usando uma KDF.

(Mostre ainda `kdf.py`, destacando `derivar_chave_senha`.)

Frase para ler:

> A funcao `derivar_chave_senha` combina a senha informada pelo usuario com o
> salt salvo no cadastro. O resultado e uma chave derivada, que depois e usada
> para montar a prova criptografica enviada ao AS.

(Mostre `data/usuarios.json`, apenas os nomes dos campos `salt`, `verificador` e `perfil`. Nao mostrar senhas, porque elas nao existem no arquivo.)

Frase para ler:

> No arquivo de usuarios, nao existe senha em texto claro. O que fica salvo e o
> salt, o verificador e o perfil do usuario. Esse detalhe e importante, porque
> o sistema nao depende de armazenar a senha original para autenticar.

## 5. Authentication Server - AS

(Mostre `src/kerberos_notas/servidores/servidor_as.py`.)

Frase para ler:

> O AS, ou Authentication Server, e o primeiro servidor do fluxo Kerberos. Ele
> roda separado e recebe as primeiras requisicoes do Cliente.

(Mostre `src/kerberos_notas/kerberos/as_server.py`, destacando `criar_desafio_as`.)

Frase para ler:

> A primeira etapa no AS e a criacao do desafio. A funcao `criar_desafio_as`
> recebe o usuario, busca seus dados no arquivo de usuarios e devolve salt,
> quantidade de iteracoes da KDF e um desafio aleatorio.

(Mostre `src/kerberos_notas/client/routes.py`, na parte em que o cliente deriva a chave e gera a prova.)

Frase para ler:

> Com esse desafio, o Cliente deriva a chave localmente e cria uma prova HMAC.
> A ideia e simples: o Cliente mostra que conhece a senha correta, mas sem
> enviar a senha pela rede.

(Volte para `as_server.py`, destacando `autenticar_no_as_com_prova`.)

Frase para ler:

> Aqui em `autenticar_no_as_com_prova`, o AS valida essa prova. Ele confere se o
> desafio existe, se pertence ao usuario correto, se ainda esta dentro do tempo
> de validade e se a prova HMAC bate com o que era esperado.

(Mostre no mesmo arquivo o uso de `DESAFIOS_AS.pop` ou a logica de consumir o desafio.)

Frase para ler:

> O desafio e consumido quando e usado. Isso ajuda a evitar reutilizacao de uma
> prova antiga. Se alguem tentar usar o mesmo desafio novamente, o AS rejeita.

## 6. TGT

(Mostre `src/kerberos_notas/kerberos/as_server.py`, destacando `_emitir_resposta_as`.)

Frase para ler:

> Se a prova estiver correta, o AS gera uma chave de sessao Cliente-TGS. Essa
> chave vai ser usada depois para o Cliente conversar com o TGS.

(Mostre `src/kerberos_notas/kerberos/tickets.py`, destacando `criar_tgt`.)

Frase para ler:

> O AS tambem cria o TGT, que significa Ticket Granting Ticket. Esse ticket
> contem a identidade do usuario, a chave Cliente-TGS, o identificador do TGS e
> informacoes de validade.

(Volte para `as_server.py`, destacando a linha onde o TGT e cifrado com `CHAVE_SECRETA_TGS`.)

Frase para ler:

> O ponto principal e que o TGT e cifrado com a chave secreta do TGS. Entao o
> Cliente carrega esse ticket, mas nao consegue abrir nem alterar o conteudo. O
> unico que consegue validar esse TGT e o TGS.

(Mostre logs do terminal, se houver uma autenticacao acontecendo.)

Frase para ler:

> Nos logs, essa etapa aparece como a validacao da prova pelo AS e a emissao do
> TGT. Os dados sensiveis aparecem mascarados, entao a apresentacao consegue
> mostrar o fluxo sem expor chaves, tickets ou senha.

## Fechamento do Apresentador 1

(Mostre rapidamente o diagrama ou o README novamente.)

Frase para ler:

> Resumindo esta primeira parte: o usuario usa senha, mas a senha nao atravessa
> a rede. O Cliente deriva uma chave com PBKDF2, responde a um desafio com HMAC,
> o AS valida essa prova e emite o TGT. Agora, com o TGT em maos, o Cliente pode
> falar com o TGS para pedir acesso ao servico de notas.

---

# Apresentador 2 - TGS, Service Ticket, autenticadores, replay e autenticacao mutua

## 1. Entrada no TGS

(Mostre `src/kerberos_notas/servidores/servidor_tgs.py`.)

Frase para ler:

> Agora a gente entra na segunda parte do Kerberos, que e o TGS, ou Ticket
> Granting Server. O papel dele e receber um TGT valido e emitir um ticket
> especifico para um servico.

(Mostre `src/kerberos_notas/kerberos/tgs_server.py`, destacando `emitir_ticket_servico`.)

Frase para ler:

> No nosso projeto, a funcao principal dessa etapa e `emitir_ticket_servico`.
> Ela recebe o usuario, o servico solicitado, o TGT e um autenticador.

(Mostre no mesmo arquivo o dicionario `CHAVES_SERVICOS`.)

Frase para ler:

> O servico protegido cadastrado no TGS e o servico `notas`. Isso significa que
> o TGS sabe qual chave usar para criar um ticket destinado ao Portal de Notas.

## 2. Autenticador Cliente-TGS

(Mostre `src/kerberos_notas/kerberos/authenticator.py`, destacando `criar_autenticador`.)

Frase para ler:

> Antes de chamar o TGS, o Cliente cria um autenticador. O autenticador e uma
> mensagem cifrada com uma chave de sessao. Para falar com o TGS, ele e cifrado
> com a chave Cliente-TGS que veio da resposta do AS.

(Mostre os campos `usuario`, `timestamp` e `nonce` em `authenticator.py`.)

Frase para ler:

> Dentro do autenticador ficam usuario, timestamp e nonce. O timestamp mostra
> que aquela mensagem e recente, e o nonce ajuda a impedir que a mesma mensagem
> seja reutilizada depois.

(Mostre `tgs_server.py`, destacando `validar_tgt`.)

Frase para ler:

> O TGS primeiro valida o TGT. Ele abre o ticket com a chave secreta do TGS,
> confere se o usuario bate, se existe chave Cliente-TGS e se o ticket ainda
> esta dentro do prazo de validade.

(Mostre `tgs_server.py`, destacando `validar_autenticador`.)

Frase para ler:

> Depois o TGS valida o autenticador. Ele abre o autenticador com a chave
> Cliente-TGS e confere novamente o usuario, o timestamp e o nonce.

## 3. Protecao contra replay no TGS

(Mostre `tgs_server.py`, destacando `NONCES_TGS_UTILIZADOS` e `_registrar_nonce_tgs`.)

Frase para ler:

> Aqui aparece a protecao contra replay no TGS. Quando um autenticador e aceito,
> o nonce usado fica registrado em memoria. Se o mesmo usuario tentar usar o
> mesmo nonce novamente, o TGS entende isso como uma reutilizacao suspeita e
> rejeita.

(Mostre rapidamente `tests/test_tgs.py`, destacando `test_tgs_rejeita_autenticador_reutilizado`.)

Frase para ler:

> Essa parte tambem tem teste automatizado. O teste de autenticador reutilizado
> confirma que o TGS nao aceita o mesmo autenticador duas vezes.

## 4. Service Ticket e chave Cliente-Servico

(Mostre `tgs_server.py`, em `emitir_ticket_servico`, destacando a geracao da chave Cliente-Servico.)

Frase para ler:

> Se o TGT e o autenticador estiverem corretos, o TGS gera uma nova chave de
> sessao: a chave Cliente-Servico. Essa chave vai proteger a comunicacao entre
> o Cliente e o Portal de Notas.

(Mostre `src/kerberos_notas/kerberos/tickets.py`, destacando `criar_ticket_servico`.)

Frase para ler:

> Em seguida, o TGS cria o Service Ticket. Esse ticket e especifico para o
> servico `notas`. Ele contem o usuario, o nome do servico, a chave
> Cliente-Servico, timestamps de validade e um nonce.

(Volte para `tgs_server.py`, destacando a cifragem do ticket com a chave do servico.)

Frase para ler:

> O Service Ticket e cifrado com a chave secreta do Portal de Notas. Entao, do
> mesmo jeito que acontecia com o TGT, o Cliente carrega o ticket, mas quem
> consegue abrir e validar o conteudo e o servidor correto, que neste caso e o
> Portal.

(Mostre no mesmo trecho a resposta cifrada para o cliente.)

Frase para ler:

> A chave Cliente-Servico tambem precisa chegar ao Cliente. Para isso, o TGS
> envia essa chave em uma resposta cifrada com a chave Cliente-TGS. Assim, so o
> Cliente que passou corretamente pelo AS consegue recuperar essa chave.

## 5. Portal de Notas e autenticacao mutua

(Mostre `src/kerberos_notas/servidores/servidor_notas.py`.)

Frase para ler:

> Agora chegamos no servico protegido, que e o Portal de Notas. Ele tambem roda
> como servidor TCP separado, na porta 9003.

(Mostre `src/kerberos_notas/notes/portal_notas.py`, destacando `autenticar_portal_notas`.)

Frase para ler:

> A primeira funcao importante no Portal e `autenticar_portal_notas`. Ela recebe
> o Service Ticket e o autenticador Cliente-Servico.

(Mostre `validar_ticket_portal` e `abrir_ticket_servico`.)

Frase para ler:

> O Portal abre o Service Ticket usando sua chave secreta. Se o ticket foi
> adulterado, se foi criado para outro servico ou se expirou, a validacao falha.

(Mostre `_validar_autenticador_portal`.)

Frase para ler:

> Depois o Portal valida o autenticador. Ele usa a chave Cliente-Servico que
> veio dentro do ticket para abrir o autenticador, e confere usuario, timestamp
> e nonce.

(Mostre a montagem da `confirmacao` com `timestamp_resposta` e `nonce_autenticador`.)

Frase para ler:

> Para completar a autenticacao mutua, o Portal responde com uma confirmacao
> cifrada. Essa confirmacao traz o timestamp incrementado em 1 e o mesmo nonce
> recebido no autenticador. O Cliente valida esses valores e, com isso, confirma
> que esta falando com o Portal correto.

(Mostre `validar_confirmacao_portal`.)

Frase para ler:

> Essa validacao do lado do Cliente fica em `validar_confirmacao_portal`. Ela
> abre a resposta do Portal e confere se o servico, o timestamp e o nonce estao
> corretos.

## 6. Operacoes protegidas depois do login

(Mostre `src/kerberos_notas/client/routes.py`, destacando `executar_operacao_kerberos`.)

Frase para ler:

> Um ponto muito importante e que o Kerberos nao protege apenas o login. Depois
> do login, cada operacao do Portal tambem passa por uma protecao propria. Isso
> acontece em `executar_operacao_kerberos`.

(Mostre na funcao a criacao da `requisicao` com `usuario`, `acao`, `dados` e `nonce`.)

Frase para ler:

> Para cada operacao, o Cliente monta uma requisicao com usuario, acao, dados e
> nonce. Essa requisicao representa exatamente aquilo que o usuario quer fazer,
> por exemplo carregar o painel, criar uma nota, editar ou excluir.

(Mostre `calcular_hash_requisicao` e a criacao do autenticador com `acao` e `hash_requisicao`.)

Frase para ler:

> Depois o Cliente calcula um hash da requisicao e cria um autenticador novo,
> incluindo a acao e esse hash. Isso amarra o autenticador a uma operacao
> especifica.

(Mostre `src/kerberos_notas/notes/portal_notas.py`, destacando `processar_operacao_portal`.)

Frase para ler:

> No Portal, a funcao `processar_operacao_portal` valida tudo de novo: o ticket,
> o autenticador, o usuario, o nonce, a acao e o hash da requisicao. So depois
> dessas verificacoes a regra de negocio e executada.

(Mostre em `portal_notas.py` a comparacao com `hmac.compare_digest`.)

Frase para ler:

> A comparacao do hash usa `hmac.compare_digest`, que e uma forma mais segura de
> comparar valores sensiveis. Se a requisicao for alterada, o hash nao bate e a
> operacao e rejeitada.

## Fechamento do Apresentador 2

(Mostre rapidamente `docs/fluxo_kerberos.md` ou o README com o fluxo.)

Frase para ler:

> Entao, fechando essa parte: o TGS valida o TGT e emite um Service Ticket para
> o Portal. O Portal valida esse ticket, valida o autenticador, responde com
> autenticacao mutua e continua exigindo protecao em cada operacao. Isso mostra
> que o Kerberos foi usado no fluxo completo do servico, e nao apenas na tela de
> login.

---

# Apresentador 3 - Portal de Notas, perfis, interface e logs

## 1. Entrada no sistema

(Mostre o navegador em `http://127.0.0.1:5000`.)

Frase para ler:

> Agora vamos mostrar a parte mais visual do projeto. O servico protegido que a
> gente escolheu foi um Portal de Notas Escolares. O usuario acessa pelo
> navegador, mas o acesso so acontece depois do fluxo Kerberos que foi explicado
> nas partes anteriores.

(Mostre a tela de login.)

Frase para ler:

> Essa e a tela de login. Aqui o usuario informa o nome e a senha. Durante a
> gravacao, a gente nao vai mostrar a senha, mas por baixo essa senha sera usada
> apenas para derivar a chave localmente.

## 2. Login como professor

(Faca login como um professor, por exemplo `SilvioSants`. Nao mostrar a senha.)

Frase para ler:

> Primeiro vamos entrar com um usuario professor. No nosso projeto, o professor
> tem permissao para visualizar alunos, lancar notas, editar notas e excluir
> notas.

(Mostre o painel carregado depois do login.)

Frase para ler:

> Depois do login, o sistema ja passou pelo AS, pelo TGS e pelo Portal de Notas.
> Quando o painel aparece, significa que a autenticacao foi concluida e que o
> Portal autorizou o acesso desse usuario.

(Mostre o formulario de lancamento de nota.)

Frase para ler:

> Como estamos usando um professor, aparece o formulario para lancar nota. Aqui
> a gente pode escolher um aluno, informar a disciplina, a nota e uma observacao.

(Preencha uma nota simples. Exemplo: aluno `AkinGOD777`, disciplina `Seguranca Computacional`, nota `9.0`, observacao `Demonstracao do fluxo Kerberos`.)

Frase para ler:

> Vou cadastrar uma nota de exemplo. Apesar de parecer um formulario comum, por
> tras essa acao vai ser enviada ao Portal como uma operacao protegida por
> Kerberos.

(Clique para lancar a nota e mostre a mensagem de sucesso ou a nota na tabela.)

Frase para ler:

> A nota foi lancada com sucesso e apareceu na tabela. Isso confirma a parte
> funcional do Portal, mas tambem confirma que a operacao passou pelas
> validacoes do servico.

## 3. Edicao de nota

(Mostre uma nota na tabela e altere o valor ou observacao.)

Frase para ler:

> Agora vamos editar a nota. A edicao tambem nao e uma alteracao direta no
> arquivo JSON. Ela passa pela mesma camada protegida: ticket de servico,
> autenticador, requisicao cifrada, nonce, acao e hash.

(Clique em salvar e mostre a atualizacao.)

Frase para ler:

> Depois de salvar, o Portal valida a operacao e devolve uma resposta cifrada.
> O Cliente valida essa resposta antes de aceitar o resultado.

## 4. Logs didaticos

(Mostre o terminal dos servidores Kerberos.)

Frase para ler:

> No terminal dos servidores, os logs mostram o que esta acontecendo durante a
> execucao. A gente consegue ver quando o AS recebe a requisicao, quando o TGS
> emite o ticket e quando o Portal valida uma operacao.

(Mostre o terminal do Flask.)

Frase para ler:

> No terminal do Flask, aparecem as etapas do Cliente Web e do Cliente TCP. Isso
> ajuda bastante na apresentacao, porque deixa visivel o caminho que o sistema
> percorre.

(Mostre o bloco de etapas Kerberos na interface, se estiver disponivel na tela.)

Frase para ler:

> A interface tambem mostra um resumo das etapas da autenticacao. Ele nao mostra
> dados sensiveis, mas ajuda a explicar para quem esta assistindo que houve AS,
> TGS, Service Ticket e autenticacao com o Portal.

(Mostre `src/kerberos_notas/logs.py`, destacando a lista de campos sensiveis.)

Frase para ler:

> Os logs foram pensados para serem didaticos, mas seguros. Campos como senha,
> chave, ticket, TGT, autenticador, nonce, salt, prova, hash e ciphertext sao
> mascarados antes de aparecerem no terminal.

## 5. Login como aluno

(Clique em sair ou acesse `/logout`.)

Frase para ler:

> Agora vamos sair da conta do professor e entrar como aluno, para mostrar a
> diferenca de permissao.

(Entre com `AkinGOD777` ou outro usuario aluno. Nao mostrar a senha.)

Frase para ler:

> Agora estamos entrando com um usuario aluno. O aluno tambem passa pelo mesmo
> fluxo Kerberos, mas o perfil dele no Portal e diferente.

(Mostre o painel do aluno.)

Frase para ler:

> No painel do aluno, ele consegue ver apenas as proprias notas. Ele nao tem o
> formulario de lancamento e tambem nao tem botoes para editar ou excluir notas.

(Mostre a ausencia do formulario e dos botoes de edicao/exclusao.)

Frase para ler:

> Essa restricao acontece em duas camadas. A interface nao mostra os controles
> de professor, e a camada de servico tambem bloqueia qualquer tentativa direta
> de alteracao feita por aluno.

## 6. Regras de professor e aluno no codigo

(Mostre `src/kerberos_notas/notes/service.py`, destacando `PERFIL_PROFESSOR` e `PERFIL_ALUNO`.)

Frase para ler:

> As regras de perfil ficam em `notes/service.py`. O projeto trabalha com dois
> perfis principais: professor e aluno.

(Mostre `listar_notas`.)

Frase para ler:

> A funcao `listar_notas` mostra essa diferenca. Se o usuario for professor, ele
> pode ver todas as notas. Se for aluno, ele ve apenas as notas associadas ao
> proprio usuario.

(Mostre `_validar_professor`.)

Frase para ler:

> E aqui em `_validar_professor`, qualquer operacao de alteracao exige perfil
> de professor. Se um aluno tentar criar, editar ou excluir nota, o sistema gera
> erro de permissao.

(Mostre `criar_nota`, `editar_nota` e `excluir_nota` rapidamente.)

Frase para ler:

> As funcoes de criar, editar e excluir chamam essa validacao. Entao a regra de
> permissao nao depende apenas da tela; ela tambem esta aplicada na regra de
> negocio.

## 7. Persistencia das notas

(Mostre `src/kerberos_notas/notes/repository.py`.)

Frase para ler:

> As notas ficam persistidas em JSON. O repositorio cuida de listar, adicionar,
> atualizar e excluir notas no arquivo `data/notas.json`.

(Mostre `src/kerberos_notas/storage/json_store.py`.)

Frase para ler:

> A escrita em JSON usa arquivo temporario e substituicao do arquivo final. Para
> o escopo academico, isso deixa a persistencia simples e suficiente para a
> demonstracao.

## Fechamento do Apresentador 3

(Mostre novamente a tela do Portal.)

Frase para ler:

> Entao, na parte visual, o sistema mostra um Portal de Notas funcionando, mas
> protegido pelo fluxo Kerberos. O professor consegue administrar notas, o aluno
> consulta apenas as proprias notas, e as operacoes importantes passam pelo
> servico protegido antes de serem executadas.

---

# Apresentador 4 - Execucao, testes, Doxygen, limitacoes e conclusao

## 1. Como executar o projeto

(Mostre o terminal com `python scripts/iniciar_servidores.py` rodando.)

Frase para ler:

> Para executar o projeto, usamos dois terminais. No primeiro, rodamos
> `python scripts/iniciar_servidores.py`. Esse comando inicia AS, TGS e Portal
> de Notas em processos separados.

(Mostre o terminal com `python run.py` rodando.)

Frase para ler:

> No segundo terminal, rodamos `python run.py`. Esse comando inicia o Flask, que
> e o Cliente Web. A partir dai, acessamos a aplicacao pelo navegador em
> `http://127.0.0.1:5000`.

(Mostre `README.md`, na parte de executar.)

Frase para ler:

> Esses comandos tambem estao documentados no README, para que outra pessoa
> consiga reproduzir a execucao do projeto.

## 2. Testes automatizados

(Mostre a pasta `tests` no VS Code.)

Frase para ler:

> O projeto tambem tem testes automatizados. Eles ajudam a comprovar que o fluxo
> nao funciona apenas na demonstracao manual, mas tambem em cenarios
> controlados.

(Mostre `tests/test_crypto.py`.)

Frase para ler:

> Em `test_crypto.py`, os testes verificam AES-GCM, KDF, nonces diferentes e
> deteccao de adulteracao.

(Mostre `tests/test_as_server.py`.)

Frase para ler:

> Em `test_as_server.py`, os testes cobrem o AS, incluindo usuario valido,
> senha invalida, emissao do TGT e integracao com o fluxo do TGS.

(Mostre `tests/test_tgs.py`.)

Frase para ler:

> Em `test_tgs.py`, os testes cobrem o TGS, o Service Ticket, autenticador
> invalido, TGT expirado e reutilizacao de autenticador.

(Mostre `tests/test_notas.py`.)

Frase para ler:

> Em `test_notas.py`, os testes cobrem o Portal de Notas, autenticacao mutua,
> replay, requisicao adulterada, permissao de professor e bloqueio de aluno.

(Mostre `tests/test_rede.py`.)

Frase para ler:

> Um dos testes mais importantes e `test_rede.py`, porque ele sobe AS, TGS e
> Portal em sockets TCP reais. Esse teste confirma que o fluxo passa pelos tres
> servidores separados.

(Mostre no terminal o comando.)

```powershell
python -m pytest -q
```

Frase para ler:

> Para rodar a suite, usamos `python -m pytest -q`. O resultado atual esperado e
> 48 testes passando.

## 3. Documentacao Doxygen

(Mostre `Doxyfile`.)

Frase para ler:

> O projeto tambem possui documentacao Doxygen. O `Doxyfile` configura quais
> arquivos entram na documentacao, a pagina principal, o diretorio de saida e o
> layout HTML.

(Mostre `DoxygenLayout.xml`.)

Frase para ler:

> O arquivo `DoxygenLayout.xml` ajusta a navegacao superior da documentacao.
> Nele existe uma aba para "Como executar o codigo", o que facilita durante a
> apresentacao.

(Mostre `docs/html/index.html` aberto no navegador, se possivel.)

Frase para ler:

> A documentacao gerada fica em `docs/html/index.html`. Por ela, e possivel
> navegar pelos arquivos, funcoes, classes e paginas explicativas do projeto.

## 4. Limitacoes academicas

(Mostre `README.md`, na secao de limitacoes academicas.)

Frase para ler:

> Como este e um projeto academico, algumas escolhas foram feitas para manter o
> sistema simples e demonstravel. A persistencia usa JSON, nao banco de dados.
> As sessoes, desafios e caches contra replay ficam em memoria. A execucao e
> local, e o navegador se comunica com o Flask por HTTP local.

(Mostre `scripts/gerar_chaves.py`.)

Frase para ler:

> Tambem existem chaves didaticas padrao para facilitar a execucao, mas o
> projeto permite trocar essas chaves por variaveis de ambiente. O script
> `gerar_chaves.py` ajuda a gerar valores novos para isso.

(Mostre novamente o README ou o relatorio tecnico.)

Frase para ler:

> Essas limitacoes nao invalidam o projeto, porque o objetivo aqui nao e criar
> uma solucao de producao. O objetivo e demonstrar o protocolo Kerberos e os
> conceitos de seguranca envolvidos.

## 5. Conclusao final

(Mostre `docs/fluxo_kerberos.md` ou o README com o fluxo geral.)

Frase para ler:

> Para concluir, o projeto demonstra o fluxo completo Cliente, AS, TGS e Portal
> de Notas. A senha e usada apenas no inicio e nao atravessa a rede. O AS emite
> o TGT, o TGS emite o Service Ticket e o Portal valida o ticket e o
> autenticador antes de permitir acesso.

(Mostre rapidamente os terminais com logs.)

Frase para ler:

> Os logs ajudam a visualizar esse caminho em tempo real, mostrando o que cada
> componente recebe, valida e devolve, sempre mascarando dados sensiveis.

(Mostre a tela do Portal de Notas.)

Frase para ler:

> Na parte funcional, o Portal permite que professores lancem e editem notas, e
> permite que alunos consultem apenas os proprios registros. Essas regras de
> permissao ficam na camada de servico e tambem sao testadas automaticamente.

(Mostre o terminal ou a pasta de testes.)

Frase para ler:

> Com os testes passando, a separacao por sockets, a KDF, os tickets, os
> autenticadores, a autenticacao mutua e a protecao contra replay ficam
> comprovados dentro do escopo do trabalho.

(Mostre o README ou uma tela limpa para finalizar.)

Frase para ler:

> Entao, de forma resumida, o nosso projeto atende aos principais requisitos:
> implementa AS, TGS e um servico protegido, usa criptografia simetrica,
> autentica por senha com KDF, emite e valida tickets, usa autenticadores,
> implementa autenticacao mutua e protege as operacoes do Portal de Notas.

---

# Checklist rapido para gravacao

Antes de gravar:

- Abrir dois terminais.
- Rodar `python scripts/iniciar_servidores.py`.
- Rodar `python run.py`.
- Abrir `http://127.0.0.1:5000`.
- Ter uma conta professor e uma conta aluno com senha conhecida.
- Nao mostrar senha.
- Deixar VS Code aberto com os arquivos principais.

Arquivos principais para deixar facil no VS Code:

- `README.md`;
- `run.py`;
- `scripts/iniciar_servidores.py`;
- `src/kerberos_notas/client/routes.py`;
- `src/kerberos_notas/rede/cliente_tcp.py`;
- `src/kerberos_notas/crypto/kdf.py`;
- `src/kerberos_notas/crypto/crypto_utils.py`;
- `src/kerberos_notas/kerberos/as_server.py`;
- `src/kerberos_notas/kerberos/tgs_server.py`;
- `src/kerberos_notas/kerberos/authenticator.py`;
- `src/kerberos_notas/notes/portal_notas.py`;
- `src/kerberos_notas/notes/service.py`;
- `tests/test_rede.py`;
- `Doxyfile`.

Coisas que devem aparecer na apresentacao:

- AS, TGS e Portal rodando separados.
- Login como professor.
- Lancamento ou edicao de nota.
- Logs didaticos no terminal.
- Login como aluno.
- Aluno sem botoes de alteracao.
- Testes com `python -m pytest -q`.
- Doxygen ou `Doxyfile`.

Coisas que nao devem ser ditas:

- Nao dizer que e Kerberos real de producao.
- Nao dizer que usa banco de dados.
- Nao dizer que a senha e enviada ao AS.
- Nao dizer que o Kerberos protege apenas o login.
- Nao dizer que existe HTTPS/TLS em producao.
- Nao mostrar senhas.

Frase curta para encerrar se sobrar pouco tempo:

> O ponto principal e que o projeto mostra o Kerberos funcionando de ponta a
> ponta em um servico real de notas. A senha fica restrita ao inicio, os tickets
> controlam o acesso, os autenticadores protegem as requisicoes, o Portal prova
> sua identidade na autenticacao mutua e as regras de professor e aluno garantem
> a autorizacao correta.
