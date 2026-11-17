# Better Item 1.7.10

Versão oficial aprovada em **17/11/2026**. Mínimo **Blender 4.2.0**. Instalador: `addons/better_item.zip`.

## Correções

- O observador de orientação nativa protege leitura e redesenho por janela, verifica se a janela continua disponível e preserva diagnóstico, retentativa e isolamento dos Frames.
- A inspeção de espaçamento mostra a causa da indisponibilidade: geometria inválida para Volume, referência incompleta ou eixos não selecionados. Preserva o retorno `(status, valor)` e não modifica o solver.
- Location, Rotation e Dimensions usam precisão visual 5; Scale continua em 3, conforme os campos nativos. Valores armazenados e conversões de unidade permanecem iguais.
- BI-F006 usa o título Orientation sync paused, preservando severidade e política de sincronização.

IDs RNA, migração, persistência das escolhas por método, matemática e tolerâncias foram preservados. Só quatro dos quinze módulos Python diferem da 1.7.9.

## Artefato e validação

SHA256 do instalador oficial: **d0d06869fcb4e6143116f4acad38912a7530e69303452b109200c9a170a02175**. Fingerprint Python: `d9a02770dc57b25836de826a0031fe5cabb38e83e3ae6ce3699fa2afc58bd1f0`. [Snapshot](handoff-1.7.10.json).

A suíte completa de **28 entradas passou nas nove builds Windows x64**: 4.2.0, 4.2.23, 4.3.2, 4.4.3, 4.5.16, 5.0.1, 5.1.2, 5.2.4 e 5.3.0; **252 entradas** no total. Houve quatro comparações GUI frias de unidades e vinte processos auxiliares, incluindo persistência nas nove builds, migração real da 1.7.2 em três e intercâmbio de cena 4.2→5.3. Guards de infraestrutura são contados separadamente.

Essas execuções completas usaram o ZIP `53ea12dee71f48cf755964405111688b15fa943ffb1bfb07ba4a67301a63fbef`. A embalagem oficial difere dele **apenas em CHANGELOG.md**, que deixou de mencionar uma etapa experimental. Os quinze módulos Python e todos os demais arquivos são byte a byte iguais. Não foram reclassificados registros de um SHA como execução de outro. A instalação pelo teste existente e a validação nativa do ZIP final são registradas separadamente em [package-final](../../tests/better_item/results/1.7.10/package-final/README.md).

[Matriz e registros de runtime](../../tests/better_item/results/1.7.10/README.md). Logs e resultados completos ficam em arquivos ZIP com índices e hashes. As tentativas de desenvolvimento permanecem separadas da aceitação.

## Limites da evidência

O [checklist de teclado/mouse](manual-publication-checklist.md) não foi executado; aprovação de publicação não equivale a teste manual. Capturas e setters não certificam digitação, arrasto ou cancelamento físicos. A causa exata dos crashes de sondagens artificiais anteriores não foi isolada; o cenário final válido de janela passou nas nove builds. Não há garantia universal de erro físico absoluto em mm: separação mínima é um parâmetro do solver, não erro máximo.

A 1.8 será discutida a partir desta base oficial, com foco em UX/UI e defeitos associados. Animação e novos alvos Edit Mode não entraram nesta versão.
