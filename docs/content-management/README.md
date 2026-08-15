# Gerenciamento de conteúdo

Para editores sem conhecimento técnico, use o [painel Decap CMS](decap.md). Ele oferece formulários, upload de fotos e PDFs e envia tudo para revisão.

| Conteúdo | Fonte canônica |
|---|---|
| Mapa do site e páginas textuais comuns | uma ficha por item em `data/paginas/` |
| Textos de páginas automáticas | `content/` |
| Pessoas e professores | uma ficha por pessoa em `data/pessoal/professores/` |
| Laboratórios | uma ficha por laboratório em `data/laboratorios/` |
| Departamentos, projetos e linhas | arquivos JSON em `data/` |
| Horários, salas e documentos | `data/documentos.json` + `static/documents/` |
| Fotos de pessoas | `static/images/pessoal/` |
| Aliases da Biblioteca | `data/pessoal/aliases_biblioteca.json` |

Publicações, teses e TGs em `data/generated/` não aparecem no CMS: são derivados dos pipelines e não devem ser editados manualmente.

- [Guia passo a passo do CMS](decap.md)
- [Importação JSON em lote](bulk-json.md)
- [Relatório da migração de professores](migration-report.md)
