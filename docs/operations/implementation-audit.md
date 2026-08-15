# Auditoria de implementação do plano Decap/CMS/automações

Estado conferido em 14/08/2026. “Implementado localmente” significa que o código e seus testes existem nesta branch; não significa que a integração externa já foi aceita em produção.

## Resultado por fase

| Fase | Evidência principal | Estado comprovado | Pendência externa ou de aceite |
|---|---|---|---|
| 0 — Segurança e governança | `scripts/security_check.py`, backup privado verificado, `main` refeito como commit-raiz, credencial Scopus revogada, fonte pública com aceite do risco residual | Ativado | MFA, dois mantenedores e política de metadados |
| 1 — Dados/professores | fichas em `data/pessoal/professores/`, schemas, migração, relatório, Content Adapters | Implementado localmente | Revisão institucional final dos 57 ativos e 33 inativos |
| 2 — CI/proteção editorial | `ci.yml`, validação cruzada, segurança, links, diff semântico, `CODEOWNERS`, ruleset, secret scanning e push protection ativos | Implementado e executado no GitHub | Definir segundo publicador e a credencial restrita para PRs automáticos |
| 3 — Decap CMS | `/admin/`, coleções pedagógicas, uploads, Open Authoring e workflow editorial; fonte pública | Implementado localmente | Publicar o painel e testar conta externa/editor/publicador |
| 4 — Worker OAuth | Worker ao vivo, allowlist, state assinado, PKCE, origem estrita e oito testes | Ativado parcialmente | Testar callback humano permitido/negado, cancelamento, expiração e revogação no painel publicado |
| 5 — Preview/deploy | Projeto Pages Direct Upload, workflows isolados, environment de prévia, repositório público de saída e deploy key exclusiva | Prévia ativada; produção credenciada | Ensaiar merge, deploy e revert |
| 6 — Biblioteca | fetch/parse/normalize/report, fixtures, thresholds, manifest e alerta agrupado | Implementado, desabilitado por gate | Consultar Biblioteca, confirmar fonte/termos/acesso externo e executar dois ciclos assistidos |
| 7 — Scopus | fetch mínimo, normalização/deduplicação, thresholds, relatório e workflow privado modelo | Implementado, não ativado | Repositório privado, runner ITA, credenciais novas, política de campos e dois ciclos assistidos |
| 8 — Operação/aceite | guias do editor, JSON, runbooks e roteiro de aceite | Preparado | Treinamento, três papéis, revisão de acessibilidade e duas pessoas não técnicas aprovadas |

## Evidência técnica executada

- dados e referências cruzadas: `Data validation passed`;
- segurança da árvore: `Security check passed`;
- upload disfarçado, script/handler, PDF falso e `target=_blank`: 5 testes negativos;
- Biblioteca: 7 testes, inclusive mudança de HTML e queda superior a 5%;
- Scopus: 15 testes, inclusive parcial/completo, `resume`/`force`, quedas, deduplicação e mudança apenas de citação;
- OAuth Worker: 8 testes de state, origem, provedor, callback e allowlist;
- Hugo 0.152.2: 4.949 páginas PT e 4.947 EN;
- links: 196.190 referências internas válidas;
- auditoria de dependências: zero vulnerabilidades conhecidas em Python e npm;
- endpoint público do Worker: `/health` retorna `ok`; `/auth` retorna redirecionamento GitHub com PKCE S256 e cookie seguro;
- Cloudflare Pages: projeto `iea-site-previews.pages.dev` criado como Direct Upload;
- GitHub Pages de saída: `https://flavioluiz.github.io/iea_site/`, branch `main`, raiz e HTTPS.
- backup histórico: repositório privado com `main` em `31afe4a` e branch da implementação em `34a9a61`;
- repositório fonte: única branch remota normal em `23b5bec`, commit-raiz sem pai; CI de `main` com cinco jobs aprovada;
- deploy piloto: gate funcionou e recusou publicar sem `PAGES_DEPLOY_TOKEN`.
- prévia do PR nº 2: deployment Cloudflare aprovado; rotas principais respondem 200, links passaram e a origem envia `X-Robots-Tag: noindex`.
- governança: `main` exige PR, histórico linear e cinco checks; aceita somente squash e bloqueia exclusão e force-push.
- abertura e proteção: `iea_site_dev` público; backup histórico privado; secret scanning e push protection ativos.
- publicação: deploy key verificada, com escrita somente em `flavioluiz/iea_site`; chave privada armazenada como `PAGES_DEPLOY_KEY` no environment protegido.
- manutenção da CI: checkout, setup-python e artefatos usam releases oficiais Node 24 fixados por SHA; PR técnico e CI de `main` aprovados sem anotação de runtime obsoleto.

## Definição de concluído

| Requisito final do plano | Estado |
|---|---|
| Conta GitHub externa propõe alteração pelo Decap | Fonte pública; pendente publicação do painel e teste humano |
| Externo não publica diretamente | Implementado no desenho; pendente ruleset/teste real |
| Professor alterado/adicionado/desativado por formulário | Implementado localmente; pendente aceite ao vivo |
| Lista completa substituída e validada | Implementado e testado localmente |
| Fotos/documentos com controles reais | Implementado e testado, inclusive negativos |
| Dados manuais não sobrescritos pelos robôs | Contratos separados e testes implementados |
| Biblioteca e Scopus abrem PRs e preservam última versão boa | Código implementado; ciclos externos ainda pendentes |
| Nenhum secret ativo no repositório público | Árvore atual passa; credencial Scopus histórica foi revogada e o proprietário aceitou a possível exposição residual da PR nº 1 |
| Runner Scopus isolado de PRs públicos | Workflow modelo correto; infraestrutura privada ainda pendente |
| Todo PR tem CI, preview e revisão | CI e preview isolado do PR nº 2 aprovados; pendem regras obrigatórias e revisão humana |
| Rollback, rotação e reexecução documentados | Implementado |
| Dois usuários não técnicos concluem roteiro | Pendente |

Conclusão da auditoria: a entrega não deve ser marcada como concluída antes das pendências externas acima. A ordem atual é: publicar a versão aprovada com a deploy key exclusiva, testar o CMS ao vivo e então executar os ciclos humanos/robôs.
