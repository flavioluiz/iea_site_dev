# Gerenciamento de Conteúdo

Esta seção explica como atualizar os diferentes tipos de conteúdo do site.

## Visão Geral

| Tipo de Conteúdo | Localização | Formato |
|------------------|-------------|---------|
| Páginas de texto | `content/` | Markdown (.md) |
| Dados de professores | `data/professores/` | YAML + JSON |
| Laboratórios | `data/laboratorios.yaml` | YAML |
| Projetos de pesquisa | `data/projetos.yaml` | YAML |
| Documentos (PDFs) | `static/documents/` + `data/documentos.yaml` | PDF + YAML |
| Menus de navegação | `config/_default/menus*.yaml` | YAML |

## Guias Específicos

- [Páginas de Conteúdo](pages.md) - Criar e editar páginas em Markdown
- [Professores](professors.md) - Gerenciar dados dos docentes
- [Laboratórios](laboratories.md) - Adicionar e editar laboratórios
- [Projetos de Pesquisa](projects.md) - Gerenciar projetos ativos
- [Documentos](documents.md) - Adicionar PDFs e documentos
- [Menus](menus.md) - Configurar navegação do site

## Bilinguismo

O site é bilíngue (PT/EN). Para cada conteúdo, existem duas versões:
- `.md` ou `.pt.md` - Versão em português
- `.en.md` - Versão em inglês

**Sempre edite ambas as versões** para manter o site consistente.

## Fluxo Básico

```bash
# 1. Iniciar servidor de desenvolvimento
hugo server -D

# 2. Editar arquivos (markdown ou yaml)
# 3. Verificar mudanças no navegador (http://localhost:1313)

# 4. Quando satisfeito, fazer deploy
./scripts/deploy.sh
```
