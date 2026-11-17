# Comparação independente — 1.7.10 VC e VG

17/11/2026. VC **2cb09d5** (`claude/better-item-1.7.10-vc`), VG **cc5b058** (`release/1.7.10-vg`). Revisão sem alterar código/ZIP nem integrar ou excluir branches. **Recomendação: manter VG como candidata; VC como referência.**

## Achados confirmados e diferenças

1. **Diagnósticos ainda incompletos na VC, não regressões novas.** Com referências Global válidas e todos os eixos de Move desligados, o painel ainda pede Complete references to measure spacing, embora plan recuse BI-A001. Com Endpoint coincidente ou Reference Axis sem eixo, mostra somente Spacing is derived from the endpoints, enquanto o plano recusa BI-E001/BI-A001. Reproduzido nas três builds desta revisão. As sondagens equivalentes da VG em 4.2.0/5.3.0 mostram a orientação específica. A seleção por cinco códigos de geometria da VC resolve o caso principal de Volume; os demais motivos continuam sem explicação. Código: [VC distribution.py:355](https://github.com/Borbofruto/Blender-Plugins/blob/2cb09d5/src/better_item/distribution.py#L355), [painel:429](https://github.com/Borbofruto/Blender-Plugins/blob/2cb09d5/src/better_item/distribution.py#L429).
2. **Download da VC aponta à main.** O README anuncia 1.7.10, mas seu botão baixa a 1.7.9 da main (6a01eb80…), não seu próprio ZIP (2c8dfbf3…). Isso não altera o pacote da branch, mas pode fazer alguém instalar o artefato errado ao revisá-la. [README:9](https://github.com/Borbofruto/Blender-Plugins/blob/2cb09d5/README.md#L9).
3. **Proteção de janelas mais estreita na VC, por inspeção de código.** _redraw_all protege window.scene no relato de falha/recuperação. O laço principal ainda o lê antes da proteção por cena; uma ReferenceError ali interrompe a passada e cai na pausa global. A VG protege cada janela e verifica presença na coleção viva antes de acessar RNA/contexto. **Não foi reproduzido um crash da VC nesta revisão:** o cenário controlado final com janela real passou nas três builds. Não converter essa diferença estática em alegação de falha cotidiana.
4. **Contrato interno de inspeção.** VC introduz `(INVALID, texto)` para geometria. Os consumidores atuais consultados tratam UNIFORM antes de consumir o número e continuam funcionando; não encontrei uma quebra concreta nesses consumidores. A VG conserva os dois valores/estados existentes, anexando a causa ao tuple de indisponibilidade. Para manutenção com preservação de contratos, prefiro a abordagem da VG e sua cobertura mais geral de causas. Não afirmar que o novo estado da VC, sozinho, prova um bug.

Precisão de Transform e diagnostics.py, incluindo o título BI-F006, são **byte a byte iguais** entre as branches. Os outros onze módulos também permanecem na base. As duas diferenças relevantes de implementação estão em distribution.py e native_refs.py; não há benefício em fundir arquivos já iguais.

## Execuções desta revisão

Gate check_release.py da VC passou: fonte/ZIP/metadados coerentes. SHA VC **2c8dfbf3d2254700aba44e669e64ab81e6a4362f2ade8d7c206c7964826fd72d**; VG continua **53ea12dee71f48cf755964405111688b15fa943ffb1bfb07ba4a67301a63fbef**.

| Artefato | Builds Windows x64 | Executado agora |
| --- | --- | --- |
| VC | 4.2.0, 4.3.2, 5.3.0 | Teste novo do Claude + regressões VG de falhas publish/remove e janela real: 3/3 por build |
| VC | As mesmas três | Uma sondagem de três estados do painel por build |
| VG | 4.2.0, 5.3.0 | A mesma sondagem de três estados por build |

São **14 processos**, separados em **9 execuções de regressão** e **5 de observação**, todos concluídos. PASS na sondagem significa que ela registrou os estados; não significa que o diagnóstico observado da VC esteja correto. Runner existente, perfis isolados e entradas/ZIP congelados em workspaces temporários no D; as branches não foram modificadas para adicionar as sondagens às suas suítes oficiais. Não é uma execução da matriz completa da VC, nem altera os 252 resultados anteriores da VG.

[Índice, hashes e escopo](../../tests/better_item/results/1.7.10/vc-review/review.json). Cada subpasta tem registros completos em runner-records.zip, summary legível e diagnostic-observations.json. Os scripts exatos estão nos registros; conteúdo bruto foi conferido após compactação.

## Parecer externo posterior do Claude

Gabriel trouxe um parecer que também recomenda a VG. Segundo esse relato, Claude verificou paridade do ZIP 53ea12de…, 13 testes background existentes em cinco versões Linux e os dois testes spacing_diagnostics/native_faults em 4.2.23/5.3.0, além de uma sondagem de reparo/quebra de malha sem limpar o cache à mão. **São execuções relatadas por outro agente, não executadas nesta revisão.** O commit VC revisado não contém novos JSONs/logs brutos dessa qualificação Linux; não tratá-la como matriz reproduzida pelo GPT nem transferir a matriz Windows da VG para o ZIP VC.

Uma precisão metodológica: os registros anteriores demonstram falhas específicas dos controles contra a 1.7.9. Não presumir que todo script novo necessariamente falhe em toda build antiga. O caso de janela real é também cobertura preventiva; a brecha Python foi demonstrada separadamente por wrapper sintético.

## O que aproveitar e o que continua pendente

- Manter o fonte/ZIP da VG, já qualificado na matriz completa. A VC oferece casos headless úteis (cubo aberto e controle das outras quatro bases, propriedades XYZ e títulos); uma futura incorporação de testes pode ampliar a suíte sem transplantar o novo status INVALID. Não houve incorporação automática nesta revisão.
- O cabeçalho curto da VC para espaçamento indisponível é uma alternativa de apresentação para avaliar na 1.8. Posição da explicação abaixo de Spacing e INFO repetido por linha na VG são ajustes visuais, não falhas matemáticas. Não mudar o ZIP já qualificado só para polimento sem registrar a nova validação necessária.
- Checklist real de teclado/mouse segue pendente. A causa exata dos crashes das sondagens artificiais anteriores segue não isolada. Os testes válidos finais de janela passaram, mas isso não prova que um except cure falhas nativas nem garante ausência universal de crash.
- Não excluir a VC com base na frase do relatório do Claude: ela é recomendação externa; Gabriel pediu revisão. A branch foi mantida como referência. Publicação estável/merge continuam decisões posteriores à revisão e aos gates abertos.
