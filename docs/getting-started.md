# Início Rápido

Este guia mostra como configurar o ambiente e fazer alterações básicas no site.

## 1. Instalar Hugo

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

Verifique a instalação:
```bash
hugo version
# Deve ser 0.121.0 ou superior
```

## 2. Clonar o Repositório

```bash
git clone https://github.com/flavioluiz/pgeam_dev.git
cd pgeam_dev
```

## 3. Iniciar Servidor de Desenvolvimento

```bash
hugo server -D
```

Acesse http://localhost:1313 para ver o site.

O servidor recarrega automaticamente quando você edita arquivos.

## 4. Fazer uma Alteração Simples

### Exemplo: Editar a página "Sobre"

1. Abra `content/sobre/_index.md` (português) ou `content/sobre/_index.en.md` (inglês)
2. Edite o conteúdo em Markdown
3. Salve o arquivo
4. O site recarrega automaticamente no navegador

### Exemplo: Adicionar um laboratório

1. Abra `data/laboratorios.yaml`
2. Adicione uma nova entrada seguindo o modelo existente
3. Salve o arquivo
4. O site recarrega automaticamente

## 5. Fazer Deploy

Quando estiver satisfeito com as alterações:

```bash
./scripts/deploy.sh
```

O script:
1. Gera o site estático com URLs de produção
2. Copia para a pasta `deploy/`
3. Faz commit das alterações
4. Pergunta se deseja fazer push

## Fluxo de Trabalho Típico

```
1. hugo server -D          # Inicia servidor local
2. Editar arquivos         # Fazer alterações
3. Verificar no navegador  # Testar mudanças
4. ./scripts/deploy.sh     # Publicar
```

## Próximos Passos

- [Gerenciar páginas de conteúdo](content-management/pages.md)
- [Atualizar dados de professores](content-management/professors.md)
- [Entender a estrutura do projeto](reference/project-structure.md)
