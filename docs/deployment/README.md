# Deploy e Desenvolvimento

Esta seção cobre como rodar o site localmente e publicá-lo.

## Guias

- [Desenvolvimento Local](local-development.md) - Configurar ambiente de desenvolvimento
- [GitHub Pages](github-pages.md) - Publicar o site

## Visão Geral

O site usa dois repositórios:

| Repositório | Conteúdo | URL |
|-------------|----------|-----|
| **pgeam_dev** | Código fonte Hugo | github.com/flavioluiz/pgeam_dev |
| **pgeam** | Site estático gerado | github.com/flavioluiz/pgeam |

**URL de Produção**: https://flavioluiz.github.io/pgeam/

## Fluxo de Deploy

```
pgeam_dev/           pgeam_dev/deploy/        flavioluiz.github.io/pgeam/
(código fonte)  ──►  (build produção)    ──►  (site público)

hugo build           git push                 GitHub Pages serve
```
