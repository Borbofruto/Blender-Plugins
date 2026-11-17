# Better Item 1.7.10 — correções de painel e observador (versão Claude)

Preparada em **17/11/2026** pela sessão do Claude, na branch `claude/better-item-1.7.10-vc`, sobre a `main` em `18747c3` (1.7.9). Não substitui a 1.7.9 até ser integrada por quem mantém o repositório. A versão é 1.7.10 porque extensões do Blender usam semver de três números; "VC" aparece só no nome da branch e deste relatório.

## O que entrou

1. **Espaçamento de malha aberta em Volume (F7).** Com Placement Volume Centroid e referências completas, uma malha aberta ou com orientação inconsistente mostrava "Complete references to measure spacing", como se faltasse uma referência. A inspeção engolia o erro BI-P003. Agora o painel mostra "Spacing cannot be measured." seguido da explicação do diagnóstico (reparar a malha ou escolher Surface Centroid). Só códigos de geometria (BI-P001, P002, P003, G001, M005) viram esse estado; referência faltando continua com a mensagem anterior. O solver e a recusa do operador não mudaram.
2. **Precisão por grupo (P1).** Os campos de Location, Rotation e Dimensions passam a declarar 5 dígitos, como os campos nativos; Scale continua com 3. Antes todos usavam 3. É o conteúdo da proposta `proposal/better-item-ui-precision` (`65971a2`), aplicado sem alteração.
3. **Título do BI-F006 (F6).** A exportação nativa pausada aparece como "Orientation sync paused", não como "Reference unavailable". Os outros diagnósticos mantêm o título.
4. **Janela inválida na recuperação (F8).** O redesenho de recuperação do observador lia `window.scene` fora de qualquer proteção. Uma janela fechada durante a falha podia levantar `ReferenceError` justamente no caminho que existe para sobreviver a falhas. Agora janelas inválidas são ignoradas. Esse risco foi identificado por leitura de código e **não foi reproduzido** numa sessão real; o teste usa janelas simuladas.

Quatro dos quinze módulos Python mudaram (`__init__`, `diagnostics`, `distribution`, `native_refs`); os outros onze são idênticos à 1.7.9. Schema, migração, enums, contratos espaciais e solvers estão preservados.

## Evidência

Novo teste [`test_better_item_regressions1710.py`](../../tests/better_item/test_better_item_regressions1710.py), entrada `background` da suíte. Contra o código da `main` ele **falha** (`('UNAVAILABLE', None)` onde se espera `INVALID`); contra esta branch passa. Cobre malha aberta em Volume (mais as outras quatro bases e a malha fechada), referência faltando, classificação por código, texto do painel, precisão por grupo, títulos e janelas inválidas.

| Executado pela sessão Claude, Linux x64, `bpy` headless | Resultado |
| --- | --- |
| Blender 4.2.23, 4.5.16, 5.0.1, 5.1.2, 5.3.0 | 14 scripts `background` aprovados em cada build |
| Instalação do ZIP final pelo operador de extensões (`test_archive_install`) | Aprovada nas cinco builds |
| `check_release.py` | Aprovado |

SHA256 do ZIP: `2c8dfbf3d2254700aba44e669e64ab81e6a4362f2ade8d7c206c7964826fd72d`. Python combinado: `b181a1238be9601deaff8b774b45438344e78e4f0a3789336d4a75725c8ba7cc`. [Snapshot](handoff-1.7.10.json).

## O que não foi executado

Estes itens **não** foram feitos e precisam rodar no ZIP final antes de qualquer publicação:

- Matriz Windows x64 completa (suíte inteira, incluindo 4.2.0, 4.2.23 e 5.3.0) com este SHA. Os resultados da 1.7.9 não valem para este ZIP.
- As dez entradas `gui_sync` e `gui_async`. O texto novo do painel foi exercitado com um substituto de layout, não desenhado de verdade; aparência, quebra de linha em painel estreito e o título do BI-F006 precisam de olhar humano.
- `test_retired_custom175_persistence`: depende de um `.blend` que uma entrada GUI gera; não existe no ambiente.
- Lista manual de [publicação](manual-publication-checklist.md).
- Builds 4.3.2, 4.4.3 e 5.2.4 da validação de compatibilidade da 1.7.9 não foram repetidas.

## Fora desta versão

Alterar o solver ou a tolerância de distribuição, nomes de Placement (P2), Frames a partir de uma fonte, ações rápidas, Offset por contato, ferramentas de Edit Mode e o pop-up de empates. Ficam no backlog da 1.8.x.

Relatório anterior: [1.7.9](release-1.7.9.md). Lista de mudanças: [CHANGELOG](../../src/better_item/CHANGELOG.md).
