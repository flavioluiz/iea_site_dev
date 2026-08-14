# Gerenciamento de conteúdo

Para editores sem conhecimento técnico, use o [painel Decap CMS](decap.md). Ele oferece formulários, upload de fotos e PDFs e envia tudo para revisão.

| Conteúdo | Fonte canônica |
|---|---|
| Páginas institucionais | `content/` |
| Pessoas e professores | `data/pessoal/professores.json` |
| Departamentos, laboratórios, projetos e linhas | arquivos JSON em `data/` |
| Horários, salas e documentos | `data/documentos.json` + `static/documents/` |
| Fotos de pessoas | `static/images/pessoal/` |
| Aliases da Biblioteca | `data/pessoal/aliases_biblioteca.json` |

Publicações, teses e TGs em `data/generated/` não aparecem no CMS: são derivados dos pipelines e não devem ser editados manualmente.

- [Guia passo a passo do CMS](decap.md)
- [Edição JSON em massa](bulk-json.md)
- [Relatório da migração de professores](migration-report.md)
