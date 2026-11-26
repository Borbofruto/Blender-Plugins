# Continuidade — Better Item

Main oficial: **f7337d0 / 1.7.10**, Blender mínimo 4.2.0. Candidata atual: **release/1.7.11**, correção crítica de identidade de objetos locais/vinculados homônimos. Ler CONTEXTO-ATUAL.md, release-1.7.11.md e handoff-1.7.11.json. Não publicar na main antes da revisão independente e da matriz sobre o ZIP final.

O teste independente de identidade veio de a2b1bc0 e deve permanecer sem alterações. Chaves de objeto percorrem plano/aplicação/verificação/Live; nomes ficam para apresentação. New Frame usa UID transitório capturado no operador. Preservar PointerProperty, IDs persistidos, migração, escolhas por método, oráculos e recusas atômicas. Distribute legado, leitura zero e limpeza de cache não entram no patch.

release/1.8 está em 3d951c4, apenas preparação; nenhuma 1.8 foi entregue e a fase 2 não começou. Seu roteiro temático e escopo aprovados permanecem naquela branch. Depois do patch, incorporar a 1.7.11 à 1.8 antes de implementar funcionalidades. Não retomar o antigo plano de quatro frentes juntas.

Usar runner e testes existentes, só Blenders portáteis e perfis isolados. Portáteis: D:/BetterItem/portables; workspaces: D:/BetterItem/workspaces; candidata: D:/BetterItem/release-1.7.11. Nunca Blender instalado. Diferenciar testes novos, desenvolvimento com FAIL preservado, histórico e pendências. Não declarar interação física ou matriz completa sem execução. Documentação trata do produto e evidências, sem comparações por autoria ou registros de conversa.
