# Proteção editorial e governança no GitHub

## Papéis mínimos

- colaboradores externos: entram no CMS, trabalham em fork e propõem pull request;
- editores: revisam informação e tradução;
- publicadores: aprovam e incorporam, sem contornar checks;
- mantenedor técnico: revisa workflows, Worker, schemas, layouts e scripts.

Designe pelo menos dois publicadores e mantenha contas com MFA. Registre um canal público para correção/remoção de dados pessoais.

## Ruleset de `main`

Em **Settings → Rules → Rulesets → New branch ruleset**, selecione `main` e configure:

- pull request obrigatório;
- pelo menos uma aprovação;
- descartar aprovação quando chegar novo commit;
- aprovação da alteração mais recente e conversas resolvidas;
- checks obrigatórios `validate-data`, `security`, `hugo-build` e `links`;
- bloqueio de force push e exclusão;
- regras aplicadas também a administradores, com exceção de recuperação documentada;
- merge permitido somente por squash.

O `CODEOWNERS` já exige `@flavioluiz` nas áreas técnicas. Acrescente um segundo mantenedor institucional antes de produção.

## Configurações complementares

1. Em **Settings → General → Pull Requests**, habilite squash e desabilite merge commit/rebase se a política for squash único.
2. Em **Settings → Actions → General**, mantenha permissões padrão somente leitura e habilite **Allow GitHub Actions to create and approve pull requests** para o robô Biblioteca.
3. Em **Settings → Code security**, habilite secret scanning, push protection e Dependabot alerts disponíveis.
4. Crie o label `bulk-reviewed`; somente mantenedores o aplicam após ler o relatório semântico.
5. Mantenha o repositório público enquanto usar Decap Open Authoring.

Mudança de código, autenticação, JavaScript ou workflow nunca deve ser aprovada apenas por revisor editorial. Pull requests de forks nunca recebem secrets e nenhum runner auto-hospedado atende este repositório.
