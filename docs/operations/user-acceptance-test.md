# Roteiro de aceite com usuários não técnicos

Este roteiro comprova a entrega operacional; testes automatizados não substituem estas sessões. Use pelo menos duas pessoas que não tenham trabalhado na implementação e reserve 30–45 minutos para cada uma.

## Pré-condições

- `iea_site_dev` público, com histórico previamente saneado e ruleset ativo;
- painel publicado em <https://flavioluiz.github.io/iea_site/admin/>;
- Worker OAuth saudável e conta de teste na allowlist;
- preview `pr-N.iea-site-previews.pages.dev` funcionando;
- três papéis disponíveis: colaborador externo sem acesso direto, editor/revisor e publicador;
- foto institucional de teste e PDF público de teste, sem dados pessoais indevidos.

Nunca use credenciais reais de automação, chave Scopus ou documento restrito na sessão.

## Sessão 1 — formulário, foto e PDF

O colaborador externo deve, sem terminal:

1. entrar no painel com GitHub;
2. alterar um link e o resumo de uma pessoa de teste;
3. enviar uma foto JPEG/PNG/WebP válida de até 2 MB;
4. anexar um PDF válido de até 10 MB em Documentos;
5. salvar, enviar para revisão e localizar o pull request/fork;
6. abrir a prévia isolada e conferir perfil, foto, documento e idiomas;
7. explicar com suas palavras que salvar não publica diretamente.

O editor pede uma correção; o usuário a faz no mesmo fluxo. O publicador confere checks, diff semântico e preview antes do merge.

## Sessão 2 — importação JSON em lote e mensagens de erro

O segundo usuário, acompanhado por um mantenedor, deve:

1. preparar um lote descartável com registros de teste;
2. executar o importador sem `--apply` e explicar a prévia de novos/atualizados;
3. introduzir deliberadamente um campo desconhecido e observar a recusa com o caminho exato;
4. corrigir o JSON e confirmar a importação numa branch;
5. ler o relatório semântico e explicar quem foi alterado;
6. confirmar que uma mudança em mais de dez pessoas exige `bulk-reviewed`;
7. enviar o PR e conferir a prévia.

Não faça o teste de remoção em massa com dados reais. Use branch/PR descartável e não incorpore a versão deliberadamente inválida.

## Testes do publicador

1. rejeitar upload HTML renomeado para `.jpg` e arquivo não PDF renomeado para `.pdf`;
2. confirmar que usuário fora da allowlist não entra;
3. confirmar que colaborador externo não faz push em `main` nem publica o site;
4. incorporar uma alteração aprovada e observar o deploy somente após CI verde;
5. usar **Revert** em um PR de teste e comprovar a restauração;
6. simular duas edições concorrentes e confirmar que o conflito é explícito, sem perda silenciosa.

## Registro de evidências

Preencha sem senhas, tokens ou dados pessoais além do necessário:

| Evidência | Sessão 1 | Sessão 2 |
|---|---|---|
| Data e participante |  |  |
| Experiência prévia com Git |  |  |
| PR de teste |  |  |
| URL da prévia |  |  |
| Foto/PDF validados |  |  |
| Erro compreendido sem ajuda técnica |  |  |
| Tempo total |  |  |
| Dificuldades observadas |  |  |
| Resultado: aprovado / repetir |  |  |

O aceite do plano exige duas sessões aprovadas, mais a comprovação do papel de publicador. Registre ajustes pedagógicos feitos após cada sessão.
