# Troubleshooting

## Hugo

### "Hugo not found"
```bash
# Verificar instalação
hugo version

# Instalar (macOS)
brew install hugo

# Instalar (Windows)
choco install hugo-extended

# Instalar (Linux)
snap install hugo
```

### Erros de build
```bash
# Ver erros detalhados
hugo --debug

# Rebuild completo
hugo --gc --cleanDestinationDir --minify
```

### Links quebrados
- Verifique se as páginas referenciadas existem
- Use `{{< ref "/pagina" >}}` para links internos verificados

### Site não atualiza no navegador
- Pare o servidor (Ctrl+C)
- Limpe o cache: `rm -rf resources/_gen/`
- Reinicie: `hugo server -D`

## Lattes

### "selenium not found"
```bash
pip install selenium webdriver-manager
```

### "Chrome driver not found"
Instale o Google Chrome no seu computador.

### Página não carrega
- Aguarde mais tempo antes de pressionar ENTER
- Verifique sua conexão com a internet
- O Lattes pode estar temporariamente indisponível

### Publicações com títulos estranhos
Use a extração com API Synthetic:
```bash
export SYNTHETIC_API_KEY='sua-chave'
python extract_lattes_improved.py --force
```

### Foto não aparece no site
```bash
# Verificar se foto existe
ls static/images/professores/nome-professor.jpg

# Verificar path no JSON
grep '"foto"' data/professores/profiles/nome-professor.json
```

## Scopus

### Erro de autenticação (403)
- Verifique se está na rede do ITA ou usando VPN
- A API do Scopus requer IP institucional

### Rate limit (429)
```bash
# Aumentar delay entre requisições
python fetch_scopus_all_professors.py --delay 5
```

### Professor não encontrado no Scopus
- Verifique se o ORCID está correto
- Use matching por nome: `--mode name`
- Use matching com IA: `--mode llm`

## Teses

### Erro de conexão com BDITA
- Verifique conexão com a internet
- O servidor pode estar temporariamente indisponível
- Tente novamente mais tarde

### Match incorreto de orientador
```bash
# Modo interativo para corrigir
python generate_thesis_pages.py

# Buscar orientador
f nome-do-orientador

# Editar e corrigir
```

## Deploy

### Links quebrados após deploy
```bash
# Verificar se usou environment correto
hugo --environment production --destination deploy
```

### CSS/JS não carregam
```bash
# Criar arquivo .nojekyll
touch deploy/.nojekyll
```

### Alterações não aparecem
1. Verifique se fez push de `deploy/`
2. Aguarde propagação (alguns minutos)
3. Limpe cache do navegador (Ctrl+Shift+R)

### Erro no submódulo deploy/
```bash
rm -rf deploy/
git clone https://github.com/flavioluiz/pgeam.git deploy
```

## Python

### ModuleNotFoundError
```bash
pip install requests beautifulsoup4 pybliometrics selenium webdriver-manager
```

### Versão do Python incorreta
```bash
python3 --version
# Deve ser 3.8 ou superior
```

### Permissão negada em script
```bash
chmod +x scripts/deploy.sh
```

## Dados

### JSON corrompido
```bash
# Verificar sintaxe
python -m json.tool data/arquivo.json
```

### YAML com erro
- Verifique indentação (use espaços, não tabs)
- Verifique strings com caracteres especiais (use aspas)

### Perfil não atualizado
1. Verifique se o arquivo JSON existe
2. Verifique se o id do professor está correto
3. Rode o script com `--dry-run` primeiro

## Contato

Se nenhuma solução funcionar:
- Email: pgeam@ita.br
- GitHub Issues: https://github.com/flavioluiz/pgeam_dev/issues
