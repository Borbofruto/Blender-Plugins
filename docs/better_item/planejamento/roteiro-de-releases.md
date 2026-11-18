# Better Item — política de releases e roteiro (v2)

Versão 2, **aprovada em 18/11/2026**, a partir da 1.7.10 oficial. Implementação segue uma fase de preparação e uma segunda aprovação antes de alterar comportamento. IDs e encaixes estão em [backlog-ideias.md](backlog-ideias.md); o escopo da 1.8 está em [escopo-1.8.md](escopo-1.8.md).

## 1. Princípio

Uma versão descreve um **escopo entregue**, não o momento em que algo ficou pronto. Corrigir ou implementar algo não obriga a publicar. Cada release deve poder ser explicada ao usuário em uma frase.

## 2. Significado dos números

| Número | Significa | Teste |
| --- | --- | --- |
| **X.0** (versão maior do produto) | Um novo **domínio de trabalho**. 1.x é Object Mode; 2.0 inaugura Edit Mode. **Não indica quebra de compatibilidade**: uma 2.0 não implica API ou dados incompatíveis. Depois dela ainda se melhora o Object Mode dentro da 2.x. | O produto passou a atuar sobre algo que antes não tocava? |
| **1.N** (minor) | Um **tema**, com recursos e correções que pertencem a ele. | O tema cabe numa frase? Se precisa de "e também", são duas releases ou algo está fora do tema. |
| **1.N.P** (patch) | O **mesmo programa, consertado**. Só correção objetiva de comportamento errado. Sem recurso, sem tema novo, sem mudar contrato. | Um usuário da versão anterior diria "é o mesmo programa, agora certo"? |

Notas:

- O manifesto do Blender só aceita três números (o validador rejeitou `1.7.9.1`). O contador de patch pode passar de 9, como em 1.7.10.
- **A 1.7.10 permanece como patch da linha 1.7.**
- **Correção pronta não é publicação imediata.** Um bug corrigido pode esperar a release do tema a que pertence, se isso deixar essa release mais coerente.
- **Correção crítica nunca espera.** Resultado errado sem aviso, perda ou corrupção de dados, travamento, falha de instalação ou migração saem como patch na hora, mesmo no meio de uma release em andamento. Mensagem enganosa e defeito visual esperam o tema correspondente, salvo se forem isolados e baratos.
- **Ideia nova nunca entra "porque deu tempo".** Ela recebe um encaixe no roteiro. Se bagunça o tema da release em andamento, vai para outra.
- **Uma release por vez.**

## 3. Modelo de escopo de uma release

Preencher antes de implementar e aprovar com Gabriel:

1. **Tema** (uma frase, em linguagem de quem usa).
2. **Problema do usuário** que o tema resolve.
3. **Entra**, cada item como **comportamentos verificáveis** (dado / quando / então, com a prova). Um item que não vira comportamento verificável não está pronto para entrar.
4. **Fica de fora** (explícito, com a release em que provavelmente entra).
5. **Pronto quando** (evidência exigida; o gate de publicação existente continua valendo).
6. **Nota ao usuário:** três linhas no README/CHANGELOG, começando pela frase do tema. Patches ficam agrupados sob a minor a que pertencem.

Do que o usuário vê (README, CHANGELOG, manual) fica de fora todo registro de processo: comparações entre versões de IA, conversas, briefings. Engenharia e evidências continuam em `docs/` e `tests/`, como já está em `CONTEXTO-ATUAL.md`.

## 4. Roteiro aprovado

| Release | Tema (frase) | Entra | Fica de fora | Antes de começar |
| --- | --- | --- | --- | --- |
| **1.7.10** | *(entregue, patch)* Correções de diagnóstico, precisão visual e observador. | — | — | — |
| **1.8** | **Quando o Better Item recusa ou não consegue medir, diz o motivo e deixa o usuário resolver.** Release de diagnóstico e recuperação, sem mudança estrutural de layout além do necessário para exibir ou acionar a solução. | Núcleo: U2, P2, F4. Condicional: U1 (tabela de casos), P3. B1 só como auditoria limitada (ver `escopo-1.8.md`). | F5, F1, F3 (ver abaixo). Layout (1.9). | Ver "Antes de implementar" em `escopo-1.8.md`. |
| **1.9** | **Um painel mais fácil de ler.** | B2 (hierarquia, agrupamento, largura, rótulos). Ajustes do diagnóstico no painel (posição do texto, ícone repetido em cada linha). Largura de texto dinâmica. | Novos botões e ações (1.10). | Depende da 1.8. |
| **1.10** | **Criar e escolher referências com menos passos.** | C1 (Frame inicializado de uma fonte em Object Mode). C2 (ações de acesso rápido). **Condicionado:** C3 (selecionar Frame pelo indicador), só entra se o escopo de viewport for definido antes. | Frame a partir de elementos de malha (2.0). Arrastar Frames, snapping próprio. | Depende da 1.9. |
| **Sem número** | **Distribuição pelo contato real entre geometrias.** | U3 (novo Placement, só Offset). | — | O número só existe depois que o protótipo de desempenho provar que a abordagem é viável (paralelogramo, peça em L; 1 mil, 10 mil e 100 mil triângulos). Decidir os três pontos abertos de U3. |
| **2.0** | **Better Item passa a trabalhar em Edit Mode, com vértices.** | E2 (Frame a partir de vértices selecionados) e E1 apenas para vértices. | Arestas, faces e multiobjeto (2.1 em diante). | BMesh de escrita com Undo por gesto; decidir o que fazer com vértice compartilhado. |
| **2.1+** | Multiobjeto e ilhas; depois arestas e faces. | Resto de E1. | — | Resultado da 2.0. |

**Fora da 1.8 por decisão ou por não caber no tema:**

- **F1** (empty, câmera ou luz cancelando o Geometry Bounds) e **F3** (objeto bloqueado ou com constraint cancelando o lote): alteram a regra do produto, não só as mensagens. Ficam fora até existir decisão explícita de comportamento.
- **F5** (detectar dependências antes de aplicar): ao ler o código, os sete códigos envolvidos (T009, A005, A006, G003, G004, G005, T011) são **verificações depois da aplicação**, seguidas de reversão. As mensagens já dizem o que fazer e que a operação foi revertida. Detectar antes exige uma análise nova de dependências, que é recurso e não correção de texto. Candidato a um tema próprio, depois.

**Gestos (B3) e responsividade (B4)** não têm release própria por enquanto. Ainda não há falha de gesto reproduzida: o checklist manual de teclado e mouse nunca foi executado, e é dele que sairiam os itens de B3. Executá-lo vem antes de decidir se B3 existe como tema. B4 só entra com medição. Se algo objetivo aparecer, sai como patch.

**Sem release até decisão dela:** P4 (contrato de erro físico máximo). Animação, descoberta de Custom Orientations, refactor geral e estado de Transform na Scene continuam fora, como em `CONTEXTO-ATUAL.md`.

## 5. Decisões e assuntos abertos

- 1.8, 1.9 e 1.10 seguem os temas da tabela aprovada.
- P2: **Minimum Separation** em todo texto visível; identificadores internos preservados.
- F4: reordenar/ligar só por clique explícito e após revalidar alvo, modificador e estado. Não repetir automaticamente a edição recusada.
- U2: Live continua recusando BI-D002 sem diálogo; Endpoint não entra na 1.8.
- U1 e P3 dependem dos resultados da preparação e de aprovação específica. Correções de B1 dependem da auditoria reproduzida e da lista aprovada.
- U3 continua sem número até viabilidade e decisões geométricas. P4 continua sem release.
- A proposta de transformar a 1.9 em comandos fora do painel permanece aberta para decisão **depois da 1.8**. Ela não altera o tema atual da 1.9 nem antecipa C2/C4.

## 6. Execução

- Contexto, continuidade e backlog seguem este roteiro aprovado. A base anterior de quatro frentes juntas foi substituída pelas releases por tema.
- Trabalhar **uma release por vez**, começando pela preparação da 1.8. A fase 1 não altera comportamento; a fase 2 só começa após aprovação dos resultados e da lista de correções.
- Antes de qualquer item, perguntar: **isto cabe na frase do tema?** Se não, registrar com o encaixe sugerido e seguir.
- Bug encontrado no meio do caminho: aplicar o critério da seção 2. Crítico vira patch separado; o resto fica no escopo ou espera.
- Texto público de cada release: a frase do tema e três linhas. Sem narrativa de processo.
- Preservar o que já vale: gate de release, evidência por SHA, recusa sem efeito parcial, limites declarados.

