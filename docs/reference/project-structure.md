# Estrutura principal

```text
content/                     páginas editoriais e Content Adapters
data/pessoal/                cadastro humano de pessoas e aliases
data/generated/scopus/       saída pública restrita do Scopus
data/generated/biblioteca/   saída da Biblioteca/BDITA
schemas/                     contratos validados pelo CI
static/admin/                painel Decap pedagógico
static/images/pessoal/       fotos com validação de assinatura/tamanho
static/documents/            PDFs públicos
infra/decap-worker/          proxy OAuth sem estado
infra/scopus-automation/     modelo para repositório privado
scripts/library/             coletor/normalizador Biblioteca
scripts/scopus/              coletor/normalizador Scopus
.github/workflows/           CI, previews, deploy e Biblioteca
```
