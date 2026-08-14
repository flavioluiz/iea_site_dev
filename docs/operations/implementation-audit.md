# Auditoria de implementação do plano Decap/CMS/automações

Estado conferido em 14/08/2026. “Implementado localmente” significa que o código e seus testes existem nesta branch; não significa que a integração externa já foi aceita em produção.

## Resultado por fase

| Fase | Evidência principal | Estado comprovado | Pendência externa ou de aceite |
|---|---|---|---|
| 0 — Segurança e governança | `scripts/security_check.py`, backup privado verificado, `main` refeito como commit-raiz, chave removida da árvore atual | Parcial | Revogar a antiga chave Scopus e eliminar a referência retida pelo PR nº 1 antes da abertura pública; MFA, dois mantenedores, política de metadados e ruleset |
| 1 — Dados/professores | `data/pessoal/professores.json`, schemas, migração, relatório, Content Adapters | Implementado localmente | Revisão institucional final dos 57 ativos e 33 inativos |
| 2 — CI/proteção editorial | `ci.yml`, validação cruzada, segurança, links, diff semântico, `CODEOWNERS` | Implementado e executado no GitHub | Ativar checks/ruleset, secret scanning e política de revisores no GitHub |
| 3 — Decap CMS | `/admin/`, coleções pedagógicas, uploads, Open Authoring e workflow editorial | Implementado localmente | Publicar o painel e testar conta externa/editor/publicador após saneamento e visibilidade pública |
| 4 — Worker OAuth | Worker ao vivo, allowlist, state assinado, PKCE, origem estrita e oito testes | Ativado parcialmente | Testar callback humano permitido/negado, cancelamento, expiração e revogação no painel publicado |
| 5 — Preview/deploy | Projeto Pages Direct Upload, workflows isolados, environment de prévia e repositório público de saída | Ativado parcialmente | Validar o primeiro preview; gravar o token de produção; ensaiar merge e revert |
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

## Definição de concluído

| Requisito final do plano | Estado |
|---|---|
| Conta GitHub externa propõe alteração pelo Decap | Pendente de publicação, repositório público saneado e teste humano |
| Externo não publica diretamente | Implementado no desenho; pendente ruleset/teste real |
| Professor alterado/adicionado/desativado por formulário | Implementado localmente; pendente aceite ao vivo |
| Lista completa substituída e validada | Implementado e testado localmente |
| Fotos/documentos com controles reais | Implementado e testado, inclusive negativos |
| Dados manuais não sobrescritos pelos robôs | Contratos separados e testes implementados |
| Biblioteca e Scopus abrem PRs e preservam última versão boa | Código implementado; ciclos externos ainda pendentes |
| Nenhum secret no repositório público | Árvore atual passa; histórico Scopus ainda impede tornar a fonte pública |
| Runner Scopus isolado de PRs públicos | Workflow modelo correto; infraestrutura privada ainda pendente |
| Todo PR tem CI, preview e revisão | CI do primeiro PR aprovada; preview isolado ainda pendente de ensaio no histórico limpo |
| Rollback, rotação e reexecução documentados | Implementado |
| Dois usuários não técnicos concluem roteiro | Pendente |

Conclusão da auditoria: a entrega não deve ser marcada como concluída antes das pendências externas acima. A ordem segura é: validar a prévia no repositório ainda privado, eliminar a referência histórica retida pelo PR nº 1, tornar a fonte pública, ativar produção com token mínimo e executar os ciclos humanos/robôs.
