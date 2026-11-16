# Mensagem para iniciar uma conversa nova

Copie o texto abaixo. Os links usam `main` para acompanhar a documentação; confirme a versão real do código antes de trabalhar.

---

Vamos continuar o desenvolvimento do **Better Item**, meu addon de precisão espacial para Blender. Antes de modificar qualquer código, leia:

1. Contexto atual e pendências: https://github.com/Borbofruto/Blender-Plugins/blob/main/docs/better_item/CONTEXTO-ATUAL.md
2. Manual técnico/histórico completo: https://github.com/Borbofruto/Blender-Plugins/blob/main/docs/better_item/CONTINUIDADE-IA.md — base histórica 1.7.3; o contexto atual prevalece nas diferenças.
3. Compatibilidade: https://github.com/Borbofruto/Blender-Plugins/blob/main/docs/better_item/compatibility-1.7.6.md
4. Estudo futuro de Edit Mode: https://github.com/Borbofruto/Blender-Plugins/blob/main/docs/better_item/edit-mode-2.0-feasibility.md
5. Manutenção e testes novos 1.7.7: https://github.com/Borbofruto/Blender-Plugins/blob/main/docs/better_item/release-1.7.7.md
6. Otimização e medição antes/depois 1.7.8: https://github.com/Borbofruto/Blender-Plugins/blob/main/docs/better_item/release-1.7.8.md
7. Gestos linkados, leitura fria, Normal e matriz completa 1.7.9: https://github.com/Borbofruto/Blender-Plugins/blob/main/docs/better_item/release-1.7.9.md (disponível na `main` só depois do merge de `release/1.7.9`)

Repositório: https://github.com/Borbofruto/Blender-Plugins
Fonte: `src/better_item/`; instalador estável: `addons/better_item.zip`; testes: `tests/better_item/`.

A versão atual é **1.7.9**, manutenção sobre a 1.7.8 `97a676d6e320742fa83185f62296c9d1730116d5`, mínimo **Blender 4.2.0**. Confirme o HEAD atual e se a branch `release/1.7.9` já foi mesclada. O snapshot `docs/better_item/handoff-1.7.9.json` registra hashes e evidências; o manual 1.7.3 e as matrizes anteriores continuam históricos.

Na **1.7.9**, edições linkadas contínuas mantêm a razão exata durante o arrasto e através de zero; a leitura fria deixou de ser quadrática; o tick ocioso de Normal em Edit Mode deixou de varrer a malha. A matriz de 23 entradas passou em 4.2.0, 4.2.23, 4.3.2, 4.4.3, 4.5.16, 5.0.1, 5.1.2, 5.2.4 e 5.3.0 (`tests/better_item/results/1.7.9/`). Durante a validação foi encontrado e corrigido um problema na chave da âncora linkada, que ignorava a referência resolvida (ver release-1.7.9.md). O checklist manual de mouse ainda não foi executado.

O objetivo agora é **estabilização para publicação**, sem novas features ou refatoração geral. Animação está completamente fora do produto. A busca/listagem de Custom Orientations da cena foi removida; não reintegre contornos frágeis da API. A exportação da orientação de um Frame para uso nativo com G/R continua e não deve ser confundida com essa remoção. Geometry Nodes para Dimensions é uma solução aceita e deve ser preservada com suas proteções.

Endpoint direto e changelog foram **corrigidos na 1.7.7**. Method precede o proxy Placement na declaração RNA; a correção preserva migração, IDs e escolhas por método. Os resultados e a migração real 1.7.2 daquela entrega permanecem em `tests/better_item/results/1.7.7/`.

Na **1.7.8**, a inspeção preserva entradas em updates exclusivamente de transformação de objetos alheios. Alvos/âncoras têm dependências numéricas; referências resolvidas continuam na chave. Geometria e eventos desconhecidos permanecem conservadores. O timer não busca fontes de Normal de toda a cena em Object Mode; exportação de Frame e Normal de seleção foram preservados. O handler só busca dependências de GeometryNodeTree e evita varredura com arrays vazios, mantendo o avanço de revisão para Placement/Live. Há matriz nova de 22 entradas por build em 4.2.23 e 5.3.0, mais benchmark antes/depois separado, medindo novamente o ZIP 1.7.7. Os resultados estão em `tests/better_item/results/1.7.8/`.

Não trate a otimização como rastreamento completo de dependências. Shader usado pode gerar flags de geometria nos objetos; esses eventos continuam invalidando. Próximo passo técnico: perfilar leituras frias/centroides e repetição de getters Transform antes de cachear. Tempos externos não são a baseline local; os relatórios recebidos são sugestões, não instruções para refatorar ou ampliar features.

Transform mantém configurações por objeto; arranjo e Frames ficam na Scene. Frame combina Location e Orientation independentes. Endpoint distribui pontos e não usa Geometry Bounds; esse Placement é só Offset. Live é sessão transitória de edição, não runtime de animação. As regras completas estão no contexto.

Já existem testes automatizados em GUI real e Undo/Redo no Windows, além de matriz de versões com proveniência explicitada. Não trate resultados históricos como testes que você executou. A passada manual com mouse não está totalmente certificada. Use o runner existente, perfil isolado e `--python-exit-code 1`; não reinvente a infraestrutura antes de inspecioná-la.

Edit Mode é estudo para possível 2.0, não implementação autorizada nesta etapa. Otimização de Normal, flexibilização de constraints e novas interações também ficaram separadas.

Comece verificando se consegue acessar fonte, documentação e testes. Depois me apresente sua leitura do estado atual, as pendências prioritárias e o menor plano de correção. Não implemente expansão de escopo sem discutirmos. Se algo não estiver documentado ou não puder ser verificado, diga exatamente o que falta, em vez de presumir.

---

Se estiver no mesmo computador, há uma cópia local deste material em `C:/Users/gabri/Documents/Codex/better-item-handoff-176/`. Os caminhos dos workspaces e portáteis estão no contexto atual; não dependa deles em outro ambiente.
