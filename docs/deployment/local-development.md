# Desenvolvimento Local

## Pré-requisitos

### Hugo

**macOS:**
```bash
brew install hugo
```

**Windows:**
```bash
choco install hugo-extended
```

**Linux:**
```bash
snap install hugo
```

Verifique:
```bash
hugo version
# Deve ser 0.121.0 ou superior
```

### Git

```bash
git --version
```

### Python (para scripts)

```bash
python3 --version
# Deve ser 3.8 ou superior

pip install requests beautifulsoup4 pybliometrics selenium webdriver-manager
```

## Clonar o Repositório

```bash
git clone https://github.com/flavioluiz/pgeam_dev.git
cd pgeam_dev
```

## Iniciar Servidor de Desenvolvimento

```bash
hugo server -D
```

Acesse: http://localhost:1313

### Flags úteis

| Flag | Descrição |
|------|-----------|
| `-D` | Inclui rascunhos (draft: true) |
| `--disableFastRender` | Rebuild completo a cada mudança |
| `--bind 0.0.0.0` | Acesso de outros dispositivos na rede |
| `--port 8080` | Usar porta diferente |

## Build Local

```bash
# Build simples
hugo

# Build otimizado
hugo --minify

# Build limpo
hugo --gc --cleanDestinationDir --minify
```

Os arquivos são gerados em `public/`.

## Estrutura de Pastas de Build

| Pasta | Propósito | BaseURL |
|-------|-----------|---------|
| `public/` | Desenvolvimento local | localhost:1313 |
| `deploy/` | Produção (GitHub Pages) | flavioluiz.github.io/pgeam/ |

## Limpeza de Cache

```bash
# Limpar build de desenvolvimento
rm -rf public/

# Limpar cache de recursos do Hugo
rm -rf resources/_gen/

# Limpeza completa
rm -rf public/ resources/_gen/
```

## Arquivos Permanentes

Não delete a pasta `static/` - ela contém arquivos permanentes:

```
static/
├── documents/     # PDFs
├── images/        # Logos, fotos
└── js/            # JavaScript customizado
```

Esses arquivos são copiados para `public/` durante o build.

## Debug

### Ver erros detalhados
```bash
hugo --debug
```

### Verificar configuração
```bash
hugo config
```

### Verificar dados
```bash
hugo config mounts
```
