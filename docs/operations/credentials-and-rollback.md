# Credenciais, incidentes e rollback

## Credencial Scopus anteriormente exposta

A chave presente em versões anteriores deve ser considerada comprometida mesmo após removida dos arquivos atuais.

1. Revogue-a no provedor e emita outra somente no repositório privado/runner.
2. Procure outros usos e logs; não reutilize o valor.
3. Decida com os mantenedores se o histórico público será reescrito. Se sim, use uma ferramenta apropriada, coordene janela, force push excepcional e renovação de todos os clones/forks.
4. Ative secret scanning e push protection.
5. Registre incidente, rotação e responsáveis sem registrar o segredo.

Reescrever histórico é destrutivo e não deve ser feito automaticamente por estes scripts.

## Onde cada secret fica

| Secret | Local |
|---|---|
| OAuth Client Secret | Cloudflare Worker Secret |
| Token de deploy do piloto | GitHub environments de Pages |
| Token e Account ID das prévias | environment `cloudflare-pages-preview`; token limitado ao Cloudflare Pages |
| Chave e institutional token Scopus | repositório privado/ambiente do runner ITA |
| Token/App do robô Scopus | somente repositório privado |
| SFTP futuro | environment de produção protegido |

## Resposta rápida

- OAuth suspeito: revogue secret no GitHub, substitua na Cloudflare e retire usuários da allowlist.
- Token Pages suspeito: revogue o token fino, crie outro e substitua em `github-pages-production`.
- Token Cloudflare Pages suspeito: revogue-o, gere outro com o mesmo escopo mínimo e atualize `cloudflare-pages-preview`.
- Scopus suspeito: pare o runner/workflow privado, revogue a chave e preserve logs sem dados sensíveis.
- Conteúdo incorreto: reverta o PR na fonte; não edite só o repositório de HTML.

Falhas dos pipelines não removem dados: toda coleta ocorre em staging e só vira PR após thresholds e validação.
