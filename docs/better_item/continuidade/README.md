# Better Item — continuidade para outra IA

Comece pelo [manual integral](../CONTINUIDADE-IA.md), ou use os capítulos abaixo para leitura gradual. A fonte de edição é o manual integral; os capítulos são gerados, não versões independentes.

Base auditada: **1.7.3**, commit `0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9`. Documentação não altera a versão nem o instalador do add-on.

| Parte | Conteúdo | Seções | Palavras aproximadas |
|---|---|---|---:|
| 1 | [Produto, histórico, arquitetura e persistência](01-produto-historico-arquitetura.md) | 1–6 | 3175 |
| 2 | [Matemática, precisão, Dimensions e Frames](02-matematica-dimensions-frames.md) | 7–11 | 2546 |
| 3 | [Distribuição, Live, caches, UI e diagnóstico](03-distribuicao-live-diagnostico.md) | 12–16 | 3844 |
| 4 | [Ambiente e testes headless/GUI no Blender](04-testes-no-blender.md) | 17–20 | 2475 |
| 5 | [Entrega, manutenção, pendências e passagem de contexto](05-entrega-pendencias-referencias.md) | 21–25 | 3332 |

O [snapshot JSON](../handoff-1.7.3.json) contém hashes, inventário dos módulos, testes e referências. A [verificação documental](../VERIFICACAO-DOCUMENTAL.json) registra integridade, links e execução dos exemplos.

A seção 25 do último capítulo inclui uma mensagem pronta para iniciar outra conversa. Leia escopo e limitações antes de implementar. Resultados de versões anteriores são históricos, não validação automaticamente repetida.

Para regenerar os capítulos: `python docs/better_item/continuidade/gerar.py`, usando Python 3 com suporte aos argumentos de pathlib utilizados. O script só escreve os cinco capítulos e este índice ao lado dele.
