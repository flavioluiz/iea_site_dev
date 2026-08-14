# Site IEA/ITA

Site bilíngue da Divisão de Engenharia Aeronáutica e Aeroespacial do ITA, gerado com Hugo.

- Piloto: <https://flavioluiz.github.io/iea_site/>
- Editor pedagógico: <https://flavioluiz.github.io/iea_site/admin/>
- Domínio oficial futuro: <https://www.aer.ita.br/>

## Edição de conteúdo

Pessoas autorizadas entram com uma conta GitHub e usam formulários em português; não precisam de terminal, Git ou acesso direto ao repositório. Toda alteração vira pull request, passa por validação automática, prévia visual e aprovação humana antes de ser publicada.

O painel permite atualizar páginas, professores, fotos, departamentos, laboratórios, projetos, linhas de pesquisa, horários, salas e documentos PDF. Comece pelo [guia do Decap CMS](docs/content-management/decap.md).

## Desenvolvimento local

Requisitos: Hugo Extended 0.152.2 e Python 3.12 para os validadores.

```bash
hugo server -D
python -m pip install -r scripts/requirements-cms.txt
python scripts/validate_data.py
python scripts/security_check.py
```

O build do piloto usa:

```bash
hugo --gc --minify --environment production \
  --config config/_default/config.yaml,config/production/config.yaml
```

## Implantação

- [Checklist de ativação pelo responsável](docs/operations/activation-checklist.md)
- [GitHub Pages, previews e publicação](docs/operations/github-pages.md)
- [OAuth GitHub e Cloudflare Worker](docs/operations/cloudflare-oauth.md)
- [Proteção da branch e governança](docs/operations/github-governance.md)
- [Pipeline Biblioteca](docs/operations/library-pipeline.md)
- [Pipeline Scopus isolado](docs/operations/scopus-pipeline.md)

Os dados editados por pessoas ficam separados de dados gerados em `data/generated/`. Robôs nunca publicam diretamente: abrem pull requests e preservam a última versão boa quando uma fonte falha.

## Segurança imediata

Uma credencial Scopus existia no histórico anterior. Ela deve permanecer revogada, ser substituída no ambiente privado e ter o histórico tratado conforme o [runbook de credenciais](docs/operations/credentials-and-rollback.md). Nunca coloque tokens, chaves ou documentos restritos neste repositório público.
