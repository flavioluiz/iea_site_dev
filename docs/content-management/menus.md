# Menus de Navegação

## Arquivos de Configuração

Os menus são definidos em dois arquivos (um para cada idioma):
- **Português:** `config/_default/menus.yaml`
- **Inglês:** `config/_default/menus.en.yaml`

## Adicionar Item ao Menu

### Item simples

Em `menus.yaml` (português):
```yaml
main:
  - identifier: "nova-pagina"      # ID único (sem espaços/acentos)
    name: "Nova Página"            # Texto exibido no menu
    url: "/nova-pagina/"           # URL da página
    weight: 8                      # Ordem no menu (menor = mais à esquerda)
```

Em `menus.en.yaml` (inglês):
```yaml
main:
  - identifier: "nova-pagina"      # Mesmo identifier
    name: "New Page"               # Nome em inglês
    url: "/nova-pagina/"           # Mesma URL
    weight: 8                      # Mesmo weight
```

## Criar Menu Dropdown

### Item pai (dropdown)
```yaml
main:
  - identifier: "meu-dropdown"
    name: "Meu Menu"
    url: "#"                       # "#" = não clicável, apenas abre dropdown
    weight: 6
```

### Itens filhos
```yaml
  - identifier: "subitem1"
    name: "Subitem 1"
    parent: "meu-dropdown"         # Referência ao identifier do pai
    url: "/subitem1/"
    weight: 1                      # Ordem dentro do dropdown

  - identifier: "subitem2"
    name: "Subitem 2"
    parent: "meu-dropdown"
    url: "/subitem2/"
    weight: 2
```

## Exemplo: Adicionar ao Menu Acadêmico

Em `menus.yaml`:
```yaml
  - identifier: "nova-info"
    name: "Informações Adicionais"
    parent: "academico"            # Adiciona ao dropdown "Acadêmico"
    url: "/nova-info/"
    weight: 4
```

Em `menus.en.yaml`:
```yaml
  - identifier: "nova-info"
    name: "Additional Information"
    parent: "academico"
    url: "/nova-info/"
    weight: 4
```

## Remover Item do Menu

Delete ou comente as linhas em **ambos** os arquivos (`menus.yaml` e `menus.en.yaml`).

## Campos do Item de Menu

| Campo | Descrição |
|-------|-----------|
| `identifier` | ID único (deve ser igual em PT e EN) |
| `name` | Texto exibido (diferente em cada idioma) |
| `url` | URL da página (use `#` para dropdown sem link) |
| `weight` | Ordem no menu (menor = primeiro) |
| `parent` | ID do item pai (para submenus) |

## Menus Existentes

| Identifier | Tipo | Conteúdo |
|------------|------|----------|
| `home` | Item | Página inicial |
| `programa` | Dropdown | Sobre, Áreas, Estatísticas |
| `corpo-docente` | Item | Lista de professores |
| `academico` | Dropdown | Teses, Publicações, Documentos |
| `infraestrutura` | Dropdown | Laboratórios, Projetos |
| `contato` | Item | Página de contato |
