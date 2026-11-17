REGISTRO HISTÓRICO ANTERIOR À CONSOLIDAÇÃO. Não reaplique o patch nem use os HEADs esperados abaixo na main atual. Comece por docs/better_item/CONTEXTO-ATUAL.md e MENSAGEM-NOVA-CONVERSA.md; as instruções do usuário atual prevalecem.

# Better Item 1.7.9 — briefing para a sessão do Claude Code no PC da Gabriel

Este arquivo é a instrução completa. Leia inteiro antes de qualquer comando. Responda sempre em português.

## 0. Como trabalhar com ela

- Direto, sem rodeios, sem hedge. Reportar **problemas objetivos e reproduzidos**, nunca "lacunas" genéricas.
- Tom neutro e gentil. Evitar gírias e entusiasmo performático ("cara", "mano", caps lock, tom de coach).
- Distinguir sempre o que **você executou** do que veio de relatórios ou de resultados históricos. Não afirmar teste que não rodou.
- Se faltar informação ou permissão, diga exatamente o que falta. Não presuma.

## 1. Regras que não podem ser quebradas

1. **Não escreva na `main`, não faça push e não force nada.** Todo trabalho fica na branch local `release/1.7.9`. Push só se ela pedir, depois de você mostrar o que será enviado.
2. Antes de qualquer alteração: `git status` limpo e `git rev-parse main` deve ser `97a676d…` (1.7.8). Se a `main` andou, pare e diga o que mudou.
3. Nada de refatoração geral, `ruff format`, Session, migration.py, novas funcionalidades, animação ou Edit Mode. Escopo = estabilização/correção.
4. Não reintroduza a busca de Custom Orientations por texto de exceção (removida na 1.7.5). Endpoint é point-only; Geometry Bounds é só Offset.
5. Nunca rode scripts de limpeza contra a instalação normal do Blender dela. Use perfis isolados e builds portáteis em pasta de trabalho separada. O runner já usa `--factory-startup` e `--python-exit-code 1`.
6. Não altere resultados históricos em `tests/better_item/results/<versão anterior>/`.

## 2. Contexto

Better Item é um addon de Blender (extensão, mínimo 4.2.0, GPL-3.0-or-later) de precisão espacial: painel Transform relativo a referências, Frames com Location/Orientation independentes, Dimensions oblíquo, distribuição com Placement (Origins, Bounds Center, Surface, Volume, Geometry Bounds).

Leia antes de mexer: `docs/better_item/CONTEXTO-ATUAL.md`, `docs/better_item/release-1.7.8.md`, `docs/better_item/MENSAGEM-NOVA-CONVERSA.md` e `tests/better_item/compatibility/README.md`. O manual histórico `CONTINUIDADE-IA.md` é longo; consulte por busca, não leia inteiro.

## 3. O que já foi feito (fora do PC dela, em Linux, com `bpy` do pip)

Há um patch com **1 commit** em `handoff-1.7.9/better-item-1.7.9.patch`, que aplica limpo sobre `97a676d`. Conteúdo, em resumo (detalhes em `docs/better_item/release-1.7.9.md`, que vem no próprio patch):

- **Edições linkadas contínuas** (`math_core.link_base/link_remember`, usado em `transform_view.edit_component`, `_edit_default` e `engine.edit_scale_component`): o arrasto de 400 passos perdia ~6e-6 da razão e, ao passar por 0, tudo colapsava e cada passo seguinte dava BI-T008.
- **Leitura fria**: `transform_view._instancer_pointers` substitui um `any(...)` que varria todas as instâncias para cada objeto (O(n²)). Com 1.500 objetos: Geometry 1,59 s → 0,12 s; Volume 1,98 s → 0,42 s (5.3.0, Linux).
- **Normal em Edit Mode**: `native_refs._normal_signature` reutiliza o fingerprint de seleção até haver evento do depsgraph, mudança do conjunto de objetos ou 2 s. Tick ocioso com 164 mil vértices: ~103 ms → 0,008 ms.
- Teste novo `tests/better_item/test_better_item_gestures179.py`, nota de release, CHANGELOG, README, versão 1.7.9 no manifesto.

Verificado só em Linux, Blender 4.2.23 e 5.3.0 via `bpy` do pip, sem GUI: teste novo passa (o caso de deriva falha na 1.7.8); 18 suítes legadas deram saída idêntica entre 1.7.8 e 1.7.9; 0 resultados velhos de cache em 12 cenários × 3 bases.

Pontos que foram **medidos e não eram problema** (não refaça): getters do painel (~0,4 ms por redesenho), `set_dimensions` oblíquo (1 `to_mesh` por passo), `context` vs `bpy.context`, troca de `as_pointer` por `session_uid` (não reproduzido; reutilização de endereço não testada).

## 4. O que fazer agora, em ordem

### 4.1 Aplicar e conferir
1. `git switch -c release/1.7.9` a partir da `main` (97a676d) e `git am handoff-1.7.9/better-item-1.7.9.patch`.
2. Revisar `git diff main..release/1.7.9`. Se algo parecer errado, **reporte antes de corrigir**.

### 4.2 Testes que só o PC dela consegue executar
1. Gerar o ZIP 1.7.9 com o próprio Blender (`blender --command extension build` dentro de `src/better_item`, ou o método que o repositório já usa; confira como o `addons/better_item.zip` foi feito). Registrar o SHA256.
2. Atualizar `tests/better_item/compatibility/suite.json` (`addon_version`, `addon_zip_sha256`, `python_source_sha256`) e acrescentar `test_better_item_gestures179.py` às entradas. Veja no arquivo qual `mode` os testes usam. O teste novo é standalone: confirme se roda como `background` ou `gui_sync` e ajuste o necessário **sem enfraquecer as asserções**.
3. Rodar a matriz padrão (22 entradas + a nova) no Blender portátil de cada versão: 4.2.0, 4.2.23, 4.3.2, 4.4.3, 4.5.16, 5.0.1, 5.1.2, 5.2.4, 5.3.0. Use `prepare_matrix.py`, `download_portables.py`, `extract_portable.py`, `run_matrix.py` conforme o README da pasta `compatibility`. Uma extração por vez; baixar só com checagem de SHA256 oficial. Usar a instalação normal do Blender dela apenas para uma execução extra, se ela confirmar.
4. Benchmark: `benchmark_cache_invalidation.py` com a baseline imutável 1.7.8 (ZIP anterior) e a 1.7.9, no mesmo PC, processos novos, sem outras cargas. Acrescentar o cenário de primeira leitura (cold) com 600 e 1.500 objetos em Geometry Bounds e Volume.
5. Medir Edit Mode em GUI real: malha densa (≥100 mil vértices), orientação Normal selecionada, tick ocioso e após trocar a seleção por um vértice diferente com a mesma contagem.
6. Salvar tudo em `tests/better_item/results/1.7.9/` e reportar **números reais do PC dela**. Se qualquer teste falhar, mostre a saída e investigue antes de mudar código.

### 4.3 O que não é automatizável (entregar como checklist para ela executar no mouse)
- Arrastar com o mouse um campo X linkado de Location, Rotation e Scale atravessando 0, com e sem Ctrl; depois Ctrl+Z e Ctrl+Shift+Z.
- Digitar valores durante o gesto e cancelar com Esc.
- Normal em Edit Mode com malha densa: selecionar, caixa de seleção, trocar vértice.
- Dimensions com Geometry Nodes e malha densa: arrasto contínuo do campo.

### 4.4 Documentação
- Ao final, atualizar `docs/better_item/release-1.7.9.md` (seção de validação com os números do PC dela), `CONTEXTO-ATUAL.md`, `MENSAGEM-NOVA-CONVERSA.md` e criar `handoff-1.7.9.json` seguindo o formato do `handoff-1.7.8.json`. Não afirmar compatibilidade de builds que não foram executadas.

## 5. Relatório final (em português, curto)
1. O que foi executado, em quais builds, com contagem de passes/falhas.
2. Problemas objetivos encontrados, com reprodução.
3. O que ficou sem verificar e por quê.
4. Lista de commits na branch e o que falta para ela decidir (merge, ZIP, publicação).

## 6. Candidatos 1.8.x já combinados (não implementar agora)
Diagnósticos mais claros (Volume, "Unavailable", mensagens repetidas); texto adaptado à largura; revisar termo "Apply Location"; confiabilidade dos gestos (somente falhas reproduzidas); medir getters; inicialização opcional de Frame a partir de uma fonte; ações rápidas reutilizando operadores; selecionar Frame pelo indicador do viewport. Fora da primeira implementação: arrastar Frames no viewport, snapping próprio, modo simples/avançado, guias que medem durante o redraw, migrar Transform para a Scene, refatoração geral.
