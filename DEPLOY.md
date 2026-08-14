# Publicação do site IEA/AER

O procedimento antigo de publicação manual do PG-EAM não se aplica a este
repositório. A publicação atual é feita pelos workflows versionados em
`.github/workflows/`, sempre depois da aprovação e dos checks obrigatórios.

- Piloto: `https://flavioluiz.github.io/iea_site/`
- Produção futura: `https://www.aer.ita.br/`
- Repositório fonte: `flavioluiz/iea_site_dev`
- Repositório estático do piloto: `flavioluiz/iea_site`

Para ativar ou operar a publicação, siga:

1. [Checklist de ativação](docs/operations/activation-checklist.md)
2. [GitHub Pages e prévias](docs/operations/github-pages.md)
3. [Credenciais e rollback](docs/operations/credentials-and-rollback.md)

Não gere nem edite manualmente uma pasta `deploy/`, não faça *force-push* no
repositório publicado e não coloque tokens em comandos, arquivos ou logs.
