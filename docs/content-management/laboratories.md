# Gerenciamento de Laboratórios

## Arquivo de Dados

Todos os laboratórios estão em `data/laboratorios.yaml`.

## Adicionar um Laboratório

```yaml
laboratorios:
  meu-lab:                        # ID único
    id: "meu-lab"
    sigla: "MEU-LAB"              # Sigla exibida no card
    nome_pt: "Meu Laboratório"
    nome_en: "My Laboratory"
    area: "eam1"                  # eam1, eam2 ou eam3
    descricao_pt: |
      Descrição completa do laboratório em português.
      Pode ter múltiplas linhas.
    descricao_en: |
      Full laboratory description in English.
      Can have multiple lines.
    infraestrutura:               # Equipamentos (PT)
      - "Equipamento 1"
      - "Equipamento 2"
    infraestrutura_en:            # Equipamentos (EN)
      - "Equipment 1"
      - "Equipment 2"
    projetos_associados:          # Projetos vinculados
      - "Projeto A"
      - "Projeto B"
    pnipe_url: "https://pnipe.mcti.gov.br/laboratory/XXXX"  # Opcional
```

## Campos Obrigatórios

| Campo | Descrição |
|-------|-----------|
| `id` | Identificador único (slug, sem espaços) |
| `sigla` | Sigla do laboratório |
| `nome_pt` | Nome completo em português |
| `nome_en` | Nome completo em inglês |
| `area` | Área de concentração (eam1, eam2 ou eam3) |
| `descricao_pt` | Descrição em português |
| `descricao_en` | Descrição em inglês |

## Campos Opcionais

| Campo | Descrição |
|-------|-----------|
| `infraestrutura` | Lista de equipamentos (PT) |
| `infraestrutura_en` | Lista de equipamentos (EN) |
| `projetos_associados` | Lista de projetos vinculados |
| `pnipe_url` | Link para o PNIPE |

## Exibição no Site

Os laboratórios são exibidos na página `/pt/laboratorios/` como cards expansíveis, organizados por área.

## Usar em Outras Páginas

Para incluir lista de laboratórios em outras páginas, use o shortcode:

```markdown
{{< lab-list area="eam1" >}}              <!-- Cards completos -->
{{< lab-list area="eam1" compact="true" >}} <!-- Lista compacta -->
```
