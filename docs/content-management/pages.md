# Gerenciamento de Páginas

## Estrutura de Páginas

As páginas de conteúdo ficam em `content/`. Cada página tem duas versões:
- `.md` ou `.pt.md` - Português (idioma padrão)
- `.en.md` - Inglês

## Editar uma Página Existente

1. Localize o arquivo em `content/`
2. Edite o conteúdo em Markdown
3. Edite também a versão em inglês (`.en.md`)

### Estrutura de um arquivo Markdown

```markdown
---
title: "Título da Página"
description: "Descrição para SEO"
date: 2025-01-21
draft: false
---

Conteúdo em Markdown aqui...

## Seção

Texto com **negrito**, *itálico*, [links](https://exemplo.com).
```

## Criar uma Nova Página Simples

```bash
# Criar arquivos
touch content/minha-pagina.md
touch content/minha-pagina.en.md
```

A página estará disponível em:
- PT: `/pt/minha-pagina/`
- EN: `/en/minha-pagina/`

## Criar uma Seção (com subpáginas)

```bash
mkdir -p content/minha-secao
touch content/minha-secao/_index.md
touch content/minha-secao/_index.en.md
```

Para adicionar subpáginas:
```bash
touch content/minha-secao/pagina1.md
touch content/minha-secao/pagina1.en.md
```

## Links Internos

### Link simples
```markdown
[Texto do Link](/contato/)
```

### Link com verificação do Hugo (recomendado)
```markdown
[Contato]({{< ref "/contato" >}})
```

### Link para âncora
```markdown
[Ver Seção](#nome-da-secao)
```

### Link para arquivo estático
```markdown
[Baixar PDF](/documents/regulamento.pdf)
```

## Página Inicial (Home)

A página inicial **não usa Markdown**. É controlada pelo template `layouts/index.html`.

Para editar a home:
1. Abra `layouts/index.html`
2. Edite o HTML/template
3. Use condicionais para textos bilíngues:

```html
{{ if eq .Site.Language.Lang "pt" }}
  Texto em português
{{ else }}
  Text in English
{{ end }}
```

## Rascunhos

Use `draft: true` no front matter para ocultar páginas incompletas:

```markdown
---
title: "Página em Desenvolvimento"
draft: true
---
```

Visualize rascunhos com `hugo server -D` (flag `-D` inclui drafts).
