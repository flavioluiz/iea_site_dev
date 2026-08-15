# Guia do editor — sem terminal e sem Git

Endereço do piloto: <https://flavioluiz.github.io/iea_site/admin/>.

## Primeiro acesso

1. Crie ou use sua conta em <https://github.com/> e informe o seu **nome de usuário GitHub** ao mantenedor.
2. Aguarde a inclusão desse nome na lista autorizada do login.
3. Abra o painel, clique em **Entrar com GitHub** e autorize o aplicativo IEA CMS.
4. Se aparecer “conta não autorizada”, envie ao mantenedor o nome exibido no seu perfil GitHub; não envie senha nem código de autenticação.

Contas externas autorizadas podem preencher formulários e enviar para revisão, mas não publicam. Contas mantenedoras do repositório também veem os estados **Pronto** e o comando **Publicar**.

Os estados não fazem a mesma coisa: **Rascunho** ainda está sendo preparado; **Em revisão** pede conferência; **Pronto** indica revisão concluída; **Ver pré-visualização** apenas abre o site de teste; somente **Publicar** mescla a proposta e inicia a atualização do site.

## Fazer uma atualização básica

1. Escolha uma área numerada no menu esquerdo.
2. Abra o registro pelo nome.
3. Altere apenas os campos necessários; leia as dicas abaixo de cada campo.
4. Clique em **Salvar** e escreva um resumo curto, por exemplo “Atualizar sala da disciplina X”.
5. Mude para **Em revisão**.
6. Confira a prévia indicada no pull request. O mantenedor pode pedir correção ou marcar como **Pronto** e publicar.

Se **Publicar** der erro, aguarde os testes e a prévia terminarem e tente novamente. Trocar o estado para Rascunho e de volta para Pronto não corrige a proposta.

## Organizar páginas e o menu

Comece pelo botão **Mapa do site**, fixado no rodapé do painel. A árvore abre e fecha as seções e mostra duas informações diferentes: a função do item no menu e a origem do conteúdo. As etiquetas de conteúdo significam:

- **📝 Markdown completo**: o conteúdo principal está em um único editor, como Graduação e Pós-Graduação;
- **📝 Markdown + páginas filhas**: o texto é Markdown e uma lista padrão aparece abaixo;
- **🗂 Markdown + dados estruturados**: o texto introdutório é Markdown e as fichas geram listas ou cartões;
- **🧱 Template especial + Markdown**: o texto é editável, mas a composição visual depende de código;
- **⚙️ Markdown + dados importados**: a introdução é editável, mas os registros vêm de uma integração.

O botão principal de cada item abre diretamente seu Markdown ou cadastro. **Ajustar no menu** abre a ficha técnica, usada somente para:

- renomear o rótulo exibido em português e inglês;
- mudar a ordem numérica;
- mover um item para outra seção;
- ocultar um item em um dos idiomas;
- criar, editar ou excluir páginas textuais comuns.

Itens automáticos e grupos essenciais são protegidos: podem ser renomeados, movidos ou ocultados, mas a validação bloqueia sua exclusão. O campo **Endereço permanente** de uma página textual deve ser definido na criação e mantido depois de publicado.

Pós-Graduação e Graduação são páginas Markdown completas e não usam template próprio. Home usa template especial; Pessoas, Laboratórios e páginas semelhantes combinam Markdown com dados. Use o atalho **Como as páginas são montadas** para comparar os formatos ou solicitar uma mudança maior de HTML/Hugo sem precisar conhecer o arquivo técnico.

## Trocar ou adicionar foto

1. Entre em **3. Pessoas e professores** e abra a pessoa.
2. Use **Filtrar por** para situação, departamento ou categoria. Em **Visualizar como**, escolha cartões para ver as fotos na lista.
3. No campo **Foto**, escolha JPEG, PNG ou WebP de até 2 MB.
4. Use retrato institucional autorizado, entre 80 e 4096 pixels, e nome simples como `nome-sobrenome.jpg`.
5. Salve e confira corte, orientação e legenda na prévia.

Arquivos disfarçados de imagem, formatos inesperados e dimensões fora do limite são bloqueados automaticamente.

## Publicar horário, salas ou outro PDF

1. Entre em **6. Documentos, horários e salas**.
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

A classificação e a política para reduzir templates fixos estão documentadas em [Arquitetura editorial das páginas](page-architecture.md).

Para vários registros de uma só vez, um mantenedor usa o [importador JSON em lote](bulk-json.md), que mostra uma prévia e bloqueia sobrescritas até a confirmação.
