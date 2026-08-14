# Pipeline Scopus no runner isolado

O Scopus é a única parte que pode exigir execução dentro da rede/VPN do ITA. O site, CMS, GitHub Pages e Worker não dependem dessa máquina.

## Topologia obrigatória

1. Crie um repositório privado `iea_data_automation`.
2. Instale o runner em conta de sistema de baixo privilégio e registre-o somente nesse repositório privado, com label `ita-scopus`.
3. Nunca registre o runner no `iea_site_dev` público e nunca execute evento de pull request nele.
4. Restrinja saída de rede ao GitHub/Scopus necessários e mantenha sistema/runner atualizados.
5. Copie e revise `infra/scopus-automation/workflow.yml.example` no repositório privado.

Secrets privados: `SCOPUS_API_KEY`, `SCOPUS_INST_TOKEN` quando aplicável e `SITE_BOT_TOKEN`/GitHub App com Contents, Pull requests e Issues mínimos no repositório do site. Issues é usado somente para agrupar alertas operacionais e fechá-los após recuperação.

## Sequência de ativação

1. Confirme com Biblioteca/gestão da assinatura quais métricas podem ser públicas.
2. Rode `dry_run` para um único `professor`.
3. Confira o relatório, IDs, contagens e zero abstracts.
4. Rode conjunto completo ainda em dry run.
5. Execute dois ciclos assistidos antes de habilitar agenda e abertura automática de PR.

Depois dos ciclos assistidos, crie no repositório privado a variável `SCOPUS_AUTOMATION_ENABLED=true`. Sem ela, o evento agendado fica inativo; a execução manual continua disponível e nasce em dry run.

O código público solicita campos mínimos e nunca escreve respostas brutas em `data/`. A normalização proíbe `abstract`, `authkeywords`, e vocabulário controlado até autorização expressa. Queda global acima de 5%, queda individual acima de 20%, estágio incompleto ou erro de quota abortam antes da promoção.

Em execução completa, a deduplicação usa nesta ordem: EID; DOI normalizado; e, somente quando ambos os registros não têm DOI, igualdade exata após normalização de título, ano e periódico. EIDs consolidados são remapeados nas referências dos autores, sem perder coautoria. A regra conservadora evita fundir trabalhos de mesmo título que tenham DOIs distintos. O manifest registra os IDs Scopus curados, e o relatório destaca inclusões, trocas e retiradas desses IDs.

## Reexecução e recuperação

- `--professor ID`: atualiza uma pessoa e mescla com o conjunto bom;
- `--resume`: reaproveita arquivos completos no staging privado;
- `--force`: repete uma coleta do estágio;
- falha parcial: descarte o staging; não copie arquivos manualmente para o site.

Revogue imediatamente a credencial antiga do histórico conforme [credenciais e rollback](credentials-and-rollback.md).
