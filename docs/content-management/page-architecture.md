# Arquitetura editorial das páginas

O painel distingue duas coisas que antes apareciam misturadas:

1. **função no menu** — seção, página, link ou elemento de organização;
2. **origem do conteúdo** — Markdown, dados estruturados, dados importados ou template especial.

Uma seção do menu pode conter uma página Markdown. É o caso de **Pós-Graduação**: `posgraduacao` organiza o submenu, enquanto o item `pg-cursos` abre o conteúdo completo de `content/posgraduacao/_index.pt.md`. Essa página usa o layout padrão do Hugo; não é automática nem possui template próprio.

## Resultado da auditoria

| Formato editorial | Páginas | Decisão |
|---|---|---|
| Markdown completo, layout padrão | Graduação, Pós-Graduação, Sobre, Contato | Prioritário; edição integral no painel |
| Markdown com lista padrão de páginas filhas | Disciplinas | Manter; o texto continua sendo Markdown |
| Markdown + dados estruturados | Departamentos, Pessoas, Laboratórios, Linhas de pesquisa, Projetos, Documentos | Manter template somente para renderizar fichas, filtros e cartões |
| Markdown + dados institucionais importados | Publicações, TGs, Dissertações e Teses | Manter geração automática dos registros; liberar título e introdução em Markdown |
| Agregação especial + Markdown | Área Espacial | Manter enquanto combinar linhas, laboratórios e projetos de várias fontes |
| Template especial + Markdown | Home | Candidato principal da próxima simplificação; migrar textos e seções estáticas gradualmente sem perder destaques e navegação |

## Regra para novos desenvolvimentos

- Use **Markdown e o layout padrão** quando a página for predominantemente texto, imagens, links e documentos.
- Use **dados estruturados** quando muitos registros do mesmo tipo precisam de filtro, ordenação, validação ou reaproveitamento.
- Crie ou mantenha **template próprio** somente quando houver composição visual ou agregação que Markdown não representa com clareza.
- Não classifique uma página como automática apenas porque ela já existe no repositório ou aparece dentro de um submenu.

O arquivo `data/admin/paginas_edicao.yaml` registra a origem editorial e os destinos dos botões exibidos no Mapa do site. A validação deve garantir que todo item de página protegido tenha uma classificação conhecida.
