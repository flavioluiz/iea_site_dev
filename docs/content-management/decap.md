# Guia do editor — sem terminal e sem Git

Endereço do piloto: <https://flavioluiz.github.io/iea_site/admin/>.

## Primeiro acesso

1. Crie ou use sua conta em <https://github.com/> e informe o seu **nome de usuário GitHub** ao mantenedor.
2. Aguarde a inclusão desse nome na lista autorizada do login.
3. Abra o painel, clique em **Entrar com GitHub** e autorize o aplicativo IEA CMS.
4. Se aparecer “conta não autorizada”, envie ao mantenedor o nome exibido no seu perfil GitHub; não envie senha nem código de autenticação.

A autorização dá acesso ao formulário, não permissão para publicar. Cada mudança é enviada para revisão e só um publicador incorpora o pull request.

## Fazer uma atualização básica

1. Escolha uma área numerada no menu esquerdo.
2. Abra o registro pelo nome.
3. Altere apenas os campos necessários; leia as dicas abaixo de cada campo.
4. Clique em **Salvar** e escreva um resumo curto, por exemplo “Atualizar sala da disciplina X”.
5. Confira a prévia indicada no pull request.
6. Mova para **Pronto para revisão**. O mantenedor recebe o pedido e pode aprovar ou solicitar correção.

## Trocar ou adicionar foto

1. Entre em **2. Pessoas e professores** e abra a pessoa.
2. No campo **Foto**, escolha JPEG, PNG ou WebP de até 2 MB.
3. Use retrato institucional autorizado, entre 80 e 4096 pixels, e nome simples como `nome-sobrenome.jpg`.
4. Salve e confira corte, orientação e legenda na prévia.

Arquivos disfarçados de imagem, formatos inesperados e dimensões fora do limite são bloqueados automaticamente.

## Publicar horário, salas ou outro PDF

1. Entre em **4. Documentos, horários e salas**.
2. Abra **Horários de aulas e salas** e clique para adicionar um arquivo.
3. Preencha nome em português, nome em inglês quando houver e data de referência.
4. Envie PDF de até 10 MB, com nome simples. Se o documento já estiver em outro site institucional, use o campo de link externo em vez do upload.
5. Na prévia, abra o PDF e confirme que é a versão correta e pública.

O servidor confere a assinatura real do PDF; mudar a extensão de outro arquivo para `.pdf` não funciona.

## Pessoas que saíram e documentos vencidos

- Para uma pessoa, desligue **Ativo no site**; não apague o registro. A página histórica permanece fora da lista atual e sem indexação.
- Para um horário vencido, acrescente primeiro o novo arquivo, confira a prévia e só então remova a referência antiga.

## Regras simples

- Nunca altere um **identificador técnico** existente.
- Nunca cole senha, token, chave de API, CPF ou documento restrito.
- Publique foto, e-mail e dados pessoais somente com autorização.
- Se estiver em dúvida, salve como rascunho e explique a dúvida no resumo.
- Campos PT e EN devem ser revisados juntos quando existirem.

O próprio painel contém um guia resumido em `/admin/guia.html`.
