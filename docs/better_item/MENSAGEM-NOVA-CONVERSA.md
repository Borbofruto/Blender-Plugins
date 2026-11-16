# Mensagem para iniciar uma conversa nova

Copie o texto abaixo. Os links usam `main` para acompanhar a documentação; confirme a versão real do código antes de trabalhar.

---

Vamos continuar o desenvolvimento do **Better Item**, meu addon de precisão espacial para Blender. Antes de modificar qualquer código, leia:

1. Contexto atual e pendências: https://github.com/Borbofruto/Blender-Plugins/blob/main/docs/better_item/CONTEXTO-ATUAL.md
2. Manual técnico/histórico completo: https://github.com/Borbofruto/Blender-Plugins/blob/main/docs/better_item/CONTINUIDADE-IA.md — base histórica 1.7.3; o contexto atual prevalece nas diferenças.
3. Compatibilidade: https://github.com/Borbofruto/Blender-Plugins/blob/main/docs/better_item/compatibility-1.7.6.md
4. Estudo futuro de Edit Mode: https://github.com/Borbofruto/Blender-Plugins/blob/main/docs/better_item/edit-mode-2.0-feasibility.md
5. Manutenção e testes novos 1.7.7: https://github.com/Borbofruto/Blender-Plugins/blob/main/docs/better_item/release-1.7.7.md

Repositório: https://github.com/Borbofruto/Blender-Plugins
Fonte: `src/better_item/`; instalador estável: `addons/better_item.zip`; testes: `tests/better_item/`.

A versão atual é **1.7.7**, manutenção sobre a base revisada 1.7.6 e o HEAD documental `e08009e00a26e059297b003f873e19ebc4ae0c58`, mínimo **Blender 4.2.0**. Confirme o HEAD atual. O snapshot `docs/better_item/handoff-1.7.7.json` registra hashes e evidências; o manual 1.7.3 e a matriz 1.7.6 continuam históricos.

O objetivo agora é **estabilização para publicação**, sem novas features ou refatoração geral. Animação está completamente fora do produto. A busca/listagem de Custom Orientations da cena foi removida; não reintegre contornos frágeis da API. A exportação da orientação de um Frame para uso nativo com G/R continua e não deve ser confundida com essa remoção. Geometry Nodes para Dimensions é uma solução aceita e deve ser preservada com suas proteções.

Endpoint direto e changelog foram **corrigidos na 1.7.7**. Method agora precede o proxy Placement na declaração RNA; a correção preserva migração, IDs e escolhas por método. Há regressão com centros analíticos distintos, ambas as ordens de kwargs, recusa atômica, Offset, invoke, propriedades de F9, repeat-last e Undo/Redo. A matriz completa foi repetida no ZIP final em 4.2.23 e 5.3.0; migração 1.7.2 e persistência em novos processos têm resultados próprios em `tests/better_item/results/1.7.7/`. Os diagnósticos 1.7.6 continuam como evidência anterior à correção. O cache de inspeção permanece invalidado por qualquer atualização do Dependency Graph; os tempos externos ainda precisam de medição local antes de otimizar.

Transform mantém configurações por objeto; arranjo e Frames ficam na Scene. Frame combina Location e Orientation independentes. Endpoint distribui pontos e não usa Geometry Bounds; esse Placement é só Offset. Live é sessão transitória de edição, não runtime de animação. As regras completas estão no contexto.

Já existem testes automatizados em GUI real e Undo/Redo no Windows, além de matriz de versões com proveniência explicitada. Não trate resultados históricos como testes que você executou. A passada manual com mouse não está totalmente certificada. Use o runner existente, perfil isolado e `--python-exit-code 1`; não reinvente a infraestrutura antes de inspecioná-la.

Edit Mode é estudo para possível 2.0, não implementação autorizada nesta etapa. Otimização de Normal, flexibilização de constraints e novas interações também ficaram separadas.

Comece verificando se consegue acessar fonte, documentação e testes. Depois me apresente sua leitura do estado atual, as pendências prioritárias e o menor plano de correção. Não implemente expansão de escopo sem discutirmos. Se algo não estiver documentado ou não puder ser verificado, diga exatamente o que falta, em vez de presumir.

---

Se estiver no mesmo computador, há uma cópia local deste material em `C:/Users/gabri/Documents/Codex/better-item-handoff-176/`. Os caminhos dos workspaces e portáteis estão no contexto atual; não dependa deles em outro ambiente.
