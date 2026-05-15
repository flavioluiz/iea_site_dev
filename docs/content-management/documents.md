# Gerenciamento de Documentos

Os documentos aparecem na página `/pt/documentos/`, organizados por categorias.

## Adicionar um Documento

### Passo 1: Upload do PDF

Coloque o arquivo em `static/documents/`:

```bash
cp meu_documento.pdf static/documents/
```

### Passo 2: Registrar no YAML

Edite `data/documentos.yaml` e adicione na categoria apropriada:

```yaml
categorias:
  - id: "regulamentos"
    nome_pt: "Regulamentos e Normas"
    nome_en: "Regulations and Standards"
    documentos:
      # Documento com PDF local
      - nome_pt: "Novo Regulamento 2025"
        nome_en: "New Regulation 2025"
        arquivo: "novo_regulamento_2025.pdf"    # Em static/documents/
        tamanho: "200 KB"
        data: "2025-01-15"
        descricao_pt: "Descrição do documento"
        descricao_en: "Document description"
```

### Documento com Link Externo

Para documentos hospedados externamente:

```yaml
      - nome_pt: "Formulário Online"
        nome_en: "Online Form"
        descricao_pt: "Formulário disponível no site do ITA"
        descricao_en: "Form available on ITA website"
        link_externo: "http://www.ita.br/posgrad/documentos"
```

## Categorias Disponíveis

| ID | Descrição |
|----|-----------|
| `regulamentos` | Regulamentos e Normas |
| `produtividade` | Produtividade Científica |
| `formularios` | Formulários e Modelos |
| `calendario` | Calendário Acadêmico |
| `chamadas` | Editais e Chamadas |

## Campos do Documento

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `nome_pt` | string | Nome em português |
| `nome_en` | string | Nome em inglês |
| `arquivo` | string | Nome do arquivo em `static/documents/` |
| `link_externo` | string | URL externa (alternativa a arquivo) |
| `tamanho` | string | Tamanho do arquivo (ex: "200 KB") |
| `data` | string | Data do documento (YYYY-MM-DD) |
| `descricao_pt` | string | Descrição em português |
| `descricao_en` | string | Descrição em inglês |

## Criar Nova Categoria

Adicione ao início de `data/documentos.yaml`:

```yaml
categorias:
  - id: "nova-categoria"
    nome_pt: "Nova Categoria"
    nome_en: "New Category"
    documentos: []
```
