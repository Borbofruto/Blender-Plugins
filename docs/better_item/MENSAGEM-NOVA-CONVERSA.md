# Continuidade — Better Item 1.8, preparação

Versão oficial na main: **1.7.10**, commit `f7337d0`, mínimo Blender 4.2.0. Trabalhar na branch **release/1.8**, criada dessa base. O planejamento aprovado está em docs/better_item/planejamento/: ler roteiro-de-releases.md v2, escopo-1.8.md e backlog-ideias.md, além de CONTEXTO-ATUAL.md. O planejamento veio do commit `bad3455`, integrado sem mudança do addon.

Tema: **Quando o Better Item recusa ou não consegue medir, diz o motivo e deixa o usuário resolver.** Uma release por vez. Crítico vira patch separado; outros itens precisam caber na frase do tema ou receber encaixe no backlog.

Fase 1 autorizada: documentos e encaixes; protótipo U2 descartável fora do addon em portáteis 4.2/4.5/5.3 (diálogo dinâmico, ordem no redo/F9, cancelamento sem alterações e identidade estável); tabelas U1, auditoria B1 dos códigos e regra/viabilidade de P3. Apresentar resultados, três tabelas e lista B1 proposta; **parar antes da fase 2**.

Decisões: P2 usa Minimum Separation, sem mudar IDs; F4 reordena/liga só ao clique, com revalidação de objeto/modificador/estado e sem reaplicar a edição; U2 cobre Offset, mantém BI-D002 sem diálogo em Live e exclui Endpoint. U1 e P3 são condicionais e precisam de aprovação após as tabelas. B1 só admite diagnóstico reproduzido com correção de texto/ação aprovada; não muda regra/solver/contrato nem bloqueia o núcleo.

Fase 2 ainda não autorizada; ordem sugerida P2 → F4 → U2. Fonte, manifesto e ZIP continuam 1.7.10 durante a preparação. Usar o runner existente, somente portáteis e perfis isolados; nunca o Blender instalado. Não declarar teclado/mouse testados por setters.

A proposta de mudar a 1.9 para comandos fora do painel permanece aberta, sem mudar o roteiro agora. Layout segue na 1.9; referências com menos passos na 1.10. Animação segue fora e novos alvos Edit Mode são de 2.0. Documentação permanece centrada no produto, sem comparações entre IAs ou briefings de autoria.

Fase 1 concluída: [protótipo U2, tabelas U1/B1/P3 e propostas](planejamento/fase-1-resultados.md). U2 passou os casos de integração em 4.2.0, 4.5.16 e 5.3.0. Unificação de U1 e aviso P3 por distância/ULP não recomendados. Quatro correções B1 propostas (D001/E003/F001/T001), ainda sem implementação. Aguarda decisão de Gabriel; **parar antes da fase 2**. Fonte e ZIP oficiais permanecem 1.7.10.
