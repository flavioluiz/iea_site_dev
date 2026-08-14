# Scripts suportados

| Comando | Finalidade |
|---|---|
| `scripts/validate_data.py` | schemas, referências, uploads e mudança em massa |
| `scripts/security_check.py` | secrets, Markdown perigoso e arquivos disfarçados |
| `scripts/check_links.py` | links do HTML no subcaminho do GitHub Pages |
| `scripts/report_content_diff.py` | relatório semântico para revisão |
| `scripts/library/fetch.py` / `normalize.py` | pipeline da Biblioteca em staging |
| `scripts/scopus/fetch.py` / `normalize.py` | pipeline Scopus privado, sem abstracts |
| `scripts/migrate_professors.py` | migração idempotente a partir do commit legado fixado |

Os demais scripts históricos não devem ser agendados sem auditoria técnica.
