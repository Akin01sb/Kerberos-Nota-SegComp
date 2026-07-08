# Relatorio tecnico base

## 1. Introducao

Este projeto implementa uma versao academica e simplificada do protocolo
Kerberos. O objetivo e autenticar usuarios e proteger servicos usando tickets,
chaves de sessao e criptografia simetrica.

O sistema foi organizado em quatro partes principais: cliente com login e KDF,
Authentication Server, Ticket Granting Server e servico de chat seguro.

## 2. Arquitetura desenvolvida

O fluxo principal segue a ideia:

```text
Cliente -> AS -> TGS -> Servico protegido
```

O cliente inicia informando usuario e senha. O AS valida essas credenciais e
emite um TGT. Em seguida, o cliente usa o TGT para pedir ao TGS um ticket de
servico. Com esse ticket, o cliente acessa o servico protegido.

Pastas principais:

- `crypto`: funcoes de KDF e criptografia simetrica
- `kerberos`: AS, TGS, tickets e autenticadores
- `client`: fluxo de login e integracao com a aplicacao web
- `notes`: servicos protegidos, incluindo o chat seguro
- `tests`: testes automatizados

## 3. Authentication Server, AS

O AS esta em `src/kerberos_notas/kerberos/as_server.py`.

Ele recebe usuario e senha, carrega os usuarios cadastrados e verifica se o
usuario existe. Depois deriva uma chave a partir da senha informada e compara o
verificador calculado com o verificador salvo.

Se a validacao for correta, o AS gera uma chave de sessao Cliente-TGS. Essa
chave sera usada pelo cliente para se comunicar com o TGS. O AS tambem cria um
Ticket Granting Ticket, TGT, contendo usuario, chave de sessao, timestamps,
validade e nonce.

O TGT e criptografado com a chave secreta do TGS. Assim, o cliente recebe o TGT,
mas nao consegue ler ou alterar seu conteudo.

## 4. Ticket Granting Server, TGS

O TGS esta em `src/kerberos_notas/kerberos/tgs_server.py`.

Ele recebe o TGT criptografado e um autenticador do cliente. Primeiro, tenta
descriptografar o TGT usando a chave secreta do TGS. Depois verifica se o TGT
pertence ao usuario correto, se possui chave de sessao Cliente-TGS e se ainda
esta dentro da validade.

O autenticador e criptografado com a chave Cliente-TGS. Isso prova que o cliente
conhece a chave de sessao que veio na resposta do AS.

Se tudo estiver valido, o TGS gera uma chave de sessao Cliente-Servico e emite
um ticket de servico. Esse ticket e criptografado com a chave secreta do servico
destino, como `notas` ou `chat`.

## 5. KDF e senha do usuario

A derivacao de chave esta em `src/kerberos_notas/crypto/kdf.py`.

Foi usada PBKDF2-HMAC-SHA256. Essa funcao recebe a senha e um salt salvo no
cadastro do usuario. A saida e uma chave de 32 bytes.

O uso da KDF evita usar a senha diretamente como chave criptografica. O salt
tambem impede que senhas iguais gerem o mesmo resultado armazenado.

No cadastro, nao e salva a senha em texto puro. E salvo apenas um verificador
gerado a partir da chave derivada.

## 6. Obtencao e uso dos tickets

Primeiro o cliente chama o AS. O AS devolve uma resposta criptografada com a
chave derivada da senha do usuario. Dentro dessa resposta existem a chave
Cliente-TGS e o TGT criptografado.

Depois o cliente envia ao TGS o TGT e um autenticador. O TGS valida o TGT e
emite um ticket de servico. Esse ticket e entregue ao servico protegido, que
consegue descriptografa-lo usando sua chave secreta.

Com isso, a senha do usuario e usada apenas no inicio do processo.

## 7. Autenticacao mutua

No chat seguro, o cliente envia ao servico um ticket de servico e um
autenticador criptografado com a chave Cliente-Servico.

O servico valida o ticket, abre o autenticador e verifica se o usuario do
autenticador corresponde ao usuario do ticket. Em seguida, responde com uma
confirmacao criptografada usando a mesma chave de sessao.

O cliente valida essa confirmacao. Se o nonce esperado estiver correto, o cliente
tem evidencia de que o servico tambem conhece a chave correta.

## 8. Chat seguro

O chat seguro esta em `src/kerberos_notas/notes/chat_seguro.py`.

Cada mensagem possui:

- remetente
- destinatario
- conteudo_criptografado
- timestamp
- nonce
- hmac

O conteudo e criptografado usando a chave de sessao Cliente-Servico. O HMAC e
calculado sobre remetente, destinatario, conteudo criptografado, timestamp e
nonce. Se qualquer campo for alterado, o HMAC calculado pelo servico nao bate
com o HMAC recebido.

Quando isso acontece, o sistema rejeita a mensagem com:

```text
Mensagem violada: integridade comprometida
```

## 9. Algoritmos criptograficos

Foram usados:

- PBKDF2-HMAC-SHA256 para derivar chave a partir da senha
- AES-GCM para criptografar pacotes JSON
- HMAC-SHA256 para verificar integridade das mensagens do chat

PBKDF2 foi escolhido por ser simples, conhecido e adequado para derivar chave a
partir de senha. AES-GCM foi escolhido por oferecer criptografia autenticada.
HMAC-SHA256 foi usado porque e uma forma direta e segura de verificar se uma
mensagem foi alterada.

## 10. Testes

Os testes estao na pasta `tests`.

Para executar:

```powershell
$env:PYTHONPATH='src'
python -m pytest -q
```

Os testes verificam:

- AS aceita usuario valido
- AS rejeita usuario inexistente e senha invalida
- AS gera TGT criptografado
- TGS valida TGT e autenticador
- TGS emite ticket de servico
- Chat valida ticket de servico
- Chat criptografa mensagem
- HMAC detecta adulteracao
- Usuario diferente do ticket e rejeitado
- Autenticacao mutua funciona com chave correta

## 11. Dificuldades e aprendizados

Uma dificuldade importante foi manter a compatibilidade entre os campos gerados
por AS, TGS e servicos. Por exemplo, o TGS espera campos especificos dentro do
TGT, como `id_cliente`, `chave_sessao_cliente_tgs` e `validade_segundos`.

Outro ponto importante foi separar confidencialidade, autenticidade e
integridade. A criptografia protege o conteudo da mensagem. O ticket e o
autenticador ajudam a provar a identidade. O HMAC detecta alteracoes na
mensagem.

O principal aprendizado foi entender que o Kerberos reduz o uso direto da senha.
Depois da autenticacao inicial, o sistema passa a trabalhar com tickets e chaves
de sessao temporarias.

## 12. Conclusao

O projeto demonstra o funcionamento basico do Kerberos com AS, TGS, tickets,
KDF, criptografia simetrica, autenticacao mutua e verificacao de integridade. Os
testes automatizados mostram que o fluxo principal funciona e que ataques simples
de adulteracao sao detectados.
