# Manutenção antes da 1.8 — avaliação e critérios de fechamento

17/11/2026. Avaliação da main `18747c3`, addon **1.7.9**, ZIP SHA256 `6a01eb809165347e94668d259a492b922b69f0c368657cae48599a2f57a9f029`. **Proposta de escopo, sem implementação ou nova release.** A branch visual `65971a2` continua sem merge. As instruções de relatórios recebidos foram tratadas como recomendações a verificar, não como autorização para ampliar o produto.

## Recomendação

Fazer uma manutenção pequena antes da 1.8. O número técnico recomendado é **1.7.10**: a função `pkg_manifest_validate_field_any_version(..., strict=True)` dos validadores distribuídos nos Blender 4.2.0 e 5.3.0 rejeitou `1.7.9.1` como não sendo semantic-version e aceitou `1.7.10`. Conferido também no instalado 5.2. Não distribuir um manifesto de quatro números ou sobrescrever silenciosamente a 1.7.9.

Não é possível garantir ausência de todos os bugs. É possível exigir que cada defeito conhecido incluído tenha reprodução e regressão, que o artefato publicado seja o testado e que as pendências sejam explícitas. A matriz verde atual não elimina os problemas de apresentação e recuperação descritos abaixo.

## Escopo mínimo proposto

| Item | Evidência e impacto | Correção limitada |
| --- | --- | --- |
| Limite do tratamento de erros do observador | Nova sondagem sintética em 4.2.0/5.3.0: uma falha de migração entra no except, mas `window.scene` lança ReferenceError fora da proteção e escapa de sync(). Não é reprodução de uma corrida espontânea de usuário. | Proteger obtenção de Scene/Window também na recuperação; evitar reutilizar uma janela removida para temp_override. Manter diagnóstico, retentativa limitada e processamento das janelas/Frames válidos. Sem engolir falhas indiscriminadamente. |
| Aviso de Volume inválido | Reproduzido agora na 5.3.0: referências válidas, duas malhas abertas; solver BI-P003, alvos intactos, painel pede para completar referências. Evidência anterior em 4.2.23 permanece histórica. | Preservar a causa do impedimento na inspeção e mostrar orientação coerente. Não enfraquecer validação de Volume, nem mudar geometria/solver. Preservar consumidores atuais do resultado de inspeção ou adaptar todos explicitamente. |
| Precisão visual de Transform | Comparações frias já registradas: Location/Rotation/Dimensions em 3 contra 5 nativo, Scale em 3 nos dois. Valores RNA iguais. | Aproveitar a proposta separada: 5/5/3/5 por grupo; não mudar conversões, setters, armazenamento ou tolerância matemática. |
| Título BI-F006 | Corpo informa pausa de sincronização; cabeçalho atual diz Reference unavailable mesmo com fonte válida. | Aproveitar título Orientation sync paused da proposta. Preservar severidade, corpo, demais títulos e métodos string de Diagnostic. |

Esses são ajustes de correção e diagnóstico; não constituem o redesenho de UX da 1.8. A troca da precisão visual e do título continua sendo uma proposta até a aprovação do escopo desta manutenção. Não mesclar a branch visual inteira sem conferir diferenças e evidências: ela tem documentos que avisam que seu fonte proposto difere do ZIP estável.

### Pendência adicional descoberta na sondagem combinada

Fechar uma janela real **dentro** da migração injetada, após o observador guardar a lista de janelas, teve resultados distintos: 5.3 manteve o timer, enquanto 4.2.0 sofreu EXCEPTION_ACCESS_VIOLATION em `BKE_workspace_active_screen_get / bpy_rna_context_temp_override_enter`. O fechamento normal de uma janela secundária sem importar o addon passou nas duas builds.

Isso não permite atribuir o crash a uma corrida cotidiana, nem concluir que um simples except resolve uma falha nativa. A causa permanece **não isolada**. Antes de fechar o item de robustez, repetir esse cenário com checkpoints, testar janela fechada normalmente com o addon ativo e conferir que o candidato não usa wrappers removidos. Se o crash permanecer, reduzir a um controle mínimo e registrar causa/limite; não declarar o item resolvido com base só na sondagem sintética.

## O que já está coberto na 1.7.9, sem reclassificar história

- Endpoint Python direto, escolhas de Placement por método, links por gesto/zero, instâncias, cache e observador têm testes existentes. A matriz final do ZIP 6a01eb80… está documentada por artefato: três builds com 24 entradas mais unidades separadas; seis builds com as 25 entradas completas. Não são nove execuções novas de 25.
- O teste native-sync cobre leitura inesperada, retentativa/backoff, isolamento de Frames, exclusão nativa, fonte inválida, cena removida, migração global com falha, Undo/load/unregister. **Não injeta separadamente falhas em publish/remove nem cobre o wrapper inválido agora demonstrado.** Esses caminhos merecem regressões direcionadas, sem afirmar que foram executados antes.
- A migração real de fixture 1.7.2 foi testada historicamente para a 1.7.7. Persistência e intercâmbio 4.2→5.3 foram executados na consolidação. Para a manutenção, repetir a migração real até o candidato, em vez de tomar AST inalterada como teste funcional.
- A qualificação de unidades cobre conversão, estado adimensional, mínimo em mm, Frames, Dimensions, Placement e recusas atômicas. Não valida digitação física nem garante erro absoluto em mm.

Detalhes e proveniência: [revisão complementar](followup-review-1.7.9.md), [consolidação](release-1.7.9.md), [unidades](units-1.7.9.md). As [seis sondagens novas](../../tests/better_item/results/1.7.9/pre-1.8-audit/README.md) são **diagnóstico**, não aprovação de candidato: quatro FAIL preservados e dois controles PASS. O check de integridade da release estável foi executado novamente e passou; o ZIP não mudou.

## Critérios para fechar a manutenção

1. **Rastrear cada correção.** Caso reproduzido no estável e aprovado no candidato, com oráculo adequado. Para Volume: erro geométrico não deve pedir referências; referência realmente ausente continua com orientação pertinente; objeto corrigido deve limpar o aviso, inclusive após cache/Live/Undo. Garantir recusa sem movimento parcial.
2. **Cobrir os limites do observador.** Wrapper inválido nos caminhos de falha e recuperação, janela removida, janela saudável que continua sendo atendida; falhas RuntimeError/TypeError de publicação e remoção separadamente; política de fonte inválida preservada; retentativa, recuperação, desligamento, Undo/load e unregister. Investigar o crash combinado antes de declarar a proteção concluída.
3. **Preservar contratos e dados.** Endpoint/Offset com kwargs em ambas as ordens, invocação/F9, escolhas independentes por método, save/reopen em processo novo, fixture legada migrada até o candidato e intercâmbio de versões. Não mudar IDs RNA, esquema, política de suspensão ou algoritmo de precisão sem decisão explícita.
4. **Validar o artefato novo.** Rodar a suíte completa existente, acrescida das regressões pertinentes, nas nove builds Windows x64 já usadas, **com o ZIP final do candidato**. Congelar entradas e hashes com o runner existente, sem reutilizar resultados do 6a01eb80… como se fossem da manutenção. Se o pacote mudar depois, repetir o aceite afetado e a matriz final.
5. **Conferir integração e publicação.** Gate de paridade fonte/ZIP, versão/changelog/README/handoff/checksums e validação de extensão; guards de infraestrutura existentes. Identificar testes novos, repetições e controles de diagnóstico separadamente. Nenhuma contagem fixa de casos prometida antes da definição das regressões.
6. **Executar interação real.** [Checklist manual](manual-publication-checklist.md): digitação `12,3456789 mm` e controle com ponto conforme idioma, Unit Scale 1/0,001, comparação nativa, Esc, arrasto, Undo/Redo, F9, Live, seleção Normal e troca de janelas. Registrar evidência e eventuais limites. Parser via API ou captura de painel não substitui esse gate; continua pendente nesta avaliação.

Nenhuma release nova será considerada qualificada apenas por concluir código ou reutilizar a matriz da 1.7.9. “Entrar na 1.8 limpo” significa fechar os defeitos aceitos, verificar as regressões e declarar o que ficou conscientemente fora; não ocultar pendências por troca de versão.

## Fora desta manutenção e decisões que não devem ser misturadas

- **Precisão física:** a separação mínima é um parâmetro de admissibilidade, não erro máximo. Já houve aceitação de 1 mm a 1 km da origem com ~0,051 mm de erro, dentro do orçamento atual. Aumentar algarismos do widget não corrige isso. Documentar os limites e revisar qualquer promessa conflitante antes de publicar. Se o objetivo for garantir um erro absoluto determinado, definir tolerância, escala/distância de operação e política de recusa com Gabriel; isso muda contrato e pode exigir trabalho numérico além de UX/UI.
- **Nomes do mínimo:** [inventário](minimum-naming-1.7.9.md) concluído. Não é defeito de conversão comprovado. Unificar rótulos/mensagens pode entrar na 1.8; preservar a distinção entre valor da Scene e override do operador. Não tornar isso uma migração implícita.
- **1.8.x:** redesenho de layout, clareza de estados além das mensagens incorretas acima, gestos e responsividade ainda podem formar as quatro frentes. Novos trabalhos de desempenho exigem medição própria; a otimização parcial já feita não é pendência repetida. Uma exigência nova de erro físico absoluto impediria classificar toda a próxima etapa como apenas UX/UI.
- Nada de animação, novos alvos Edit Mode, Custom Orientation discovery, flexibilização de constraints, estado global de Transform ou refatoração geral.
