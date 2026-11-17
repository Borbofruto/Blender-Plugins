# Auditoria antes da 1.8 — diagnóstico, não aceite

17/11/2026. ZIP estável **6a01eb80…**, main **18747c3**. Não altera a matriz histórica nem o instalador. Seis processos novos, lançados pelo runner existente com perfis isolados; as sondagens foram acrescentadas somente a manifestos temporários em D. O manifesto padrão do repositório não mudou.

| Sondagem | 4.2.0 | 5.3.0 |
| --- | --- | --- |
| Falha de migração + fechar janela real durante a chamada | Crash nativo; sem JSON final | Timer sobrevive; aviso Volume reproduzido |
| Wrapper Window sintético inválido + falha de migração | ReferenceError escapa de sync() | ReferenceError escapa de sync() |
| Fechar janela secundária sem importar addon | PASS | PASS |

As quatro execuções de diagnóstico de defeitos aparecem como **FAIL** nos summaries, intencionalmente preservados. Não são quatro regressões aprovadas. Os dois controles são PASS. A sondagem sintética captura a exceção para registrar o stack; não demonstra que um usuário tenha removido o timer. Na combinada da 5.3, o wrapper ainda não estava invalidado e o timer permaneceu registrado; a exceção seguinte foi TypeError: Window not found.

O crash da combinada 4.2 ocorreu em BKE_workspace_active_screen_get / bpy_rna_context_temp_override_enter, sob fechamento reentrante e erro injetado. O controle sem addon passou. Isso não isola a causa do crash nem prova uma corrida espontânea ao fechar janela; exige reexecução e isolamento adicionais antes de atribuição. Não ocultar esse resultado ao desenvolver a proteção.

Volume na 5.3: referências resolvidas, solver emite BI-P003 pedindo geometria fechada/orientada, alvos intactos; captura Python dos labels mostra “Complete references to measure spacing.” Não é interação com mouse ou captura de tela. A combinada 4.2 caiu antes de escrever o resultado de Volume; não contar uma nova aprovação desse cenário nessa build.

[Correções publicadas](../../../../../docs/better_item/release-1.7.10.md). [Inventário e hashes](inventory.json). Logs, JSONs, manifestos, scripts e crash foram preservados; somente CRLF→LF na publicação, com hashes originais e publicados. Nenhum perfil ou .blend foi incluído. A primeira tentativa de preparação, sem lançamento de Blender por manifesto incorreto, permanece no D e não entra nas seis execuções.
