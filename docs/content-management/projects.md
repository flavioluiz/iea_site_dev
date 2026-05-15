# Gerenciamento de Projetos de Pesquisa

## Arquivo de Dados

Todos os projetos estão em `data/projetos.yaml`.

## Adicionar um Projeto

```yaml
projetos:
  meu-projeto:                    # ID único
    id: "meu-projeto"
    titulo_pt: "Título do Projeto em Português"
    titulo_en: "Project Title in English"
    area: "eam1"                  # eam1, eam2 ou eam3
    financiador: "FAPESP/CNPq"    # Agência(s) de fomento
    valor: 1500000.00             # Valor em reais (número)
    moeda: "BRL"
    periodo: "2023-2027"          # Período de vigência
    status: "em_andamento"        # em_andamento ou concluido
    descricao_pt: |
      Descrição completa do projeto em português.
    descricao_en: |
      Full project description in English.
```

## Campos Obrigatórios

| Campo | Descrição |
|-------|-----------|
| `id` | Identificador único (slug) |
| `titulo_pt` | Título em português |
| `titulo_en` | Título em inglês |
| `area` | Área de concentração |
| `financiador` | Agência(s) de fomento |
| `valor` | Valor do financiamento (número) |
| `periodo` | Período de vigência |
| `status` | `em_andamento` ou `concluido` |

## Campos Opcionais

| Campo | Descrição |
|-------|-----------|
| `moeda` | Moeda (padrão: BRL) |
| `descricao_pt` | Descrição detalhada (PT) |
| `descricao_en` | Descrição detalhada (EN) |

## Exibição no Site

- Apenas projetos com `status: "em_andamento"` são exibidos
- O valor é formatado automaticamente (ex: R$ 1,5 milhões)
- O total de investimentos é calculado automaticamente

## Página de Projetos

Os projetos são exibidos em `/pt/projetos/` como cards expansíveis com:
- Título e financiador
- Valor do financiamento
- Período de vigência
- Descrição expandível
