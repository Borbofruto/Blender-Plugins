# Better Item 1.7.6 — suporte a partir do Blender 4.2.0

## Decisão e mudança

O mínimo do manifesto passa de 5.0.0 para **4.2.0**. O suporte das capacidades atuais não exigiu adaptação no runtime Python: seu hash combinado continua `37848ddc104c3c10dfcedb8758b2e16e9d40c5811feb1568b85ab11603aa3b5f`, idêntico à 1.7.5. Mudaram manifesto, versão e documentação. Não houve cortes de recursos, refatoração dos motores, novos caminhos matemáticos ou introdução de uma camada de compatibilidade no produto.

O ZIP final 1.7.6 tem SHA256 `a4182db99196e502768cae288781546d6c89619f3c7172cfbf78abc8fcadd382`. A paridade entre suas fontes e os arquivos do repositório foi conferida. O formato de extensões que já usamos foi introduzido na 4.2; não precisamos criar um pacote legado para esse mínimo.

## Evidência por versão

Windows x64, portáteis oficiais com SHA256 validado, perfis isolados e processos novos. Cada matriz tem 19 entradas de API/regressão e uma de instalação.

| Blender | Build | Origem da evidência do runtime | API/regressão | Instalação habilitada |
| --- | --- | --- | --- | --- |
| 4.2.0 | a51f293548ad | 1.7.6 final | 19/19 | Sim |
| 4.2.23 | d0cbe84903e8 | 1.7.6 candidate | 19/19 | Sim |
| 4.3.2 | 32f5fdce0a0a | 1.7.6 candidate | 19/19 | Sim |
| 4.4.3 | 802179c51ccc | 1.7.6 candidate | 19/19 | Sim |
| 4.5.16 | 3f6797307da5 | 1.7.5 baseline | 19/19 | Sim |
| 5.0.1 | a3db93c5b259 | 1.7.5 baseline | 19/19 | Sim |
| 5.1.2 | ec6e62d40fa9 | 1.7.5 baseline | 19/19 | Sim |
| 5.2.4 | cd5dc428cce1 | 1.7.5 baseline | 19/19 | Sim |
| 5.3.0 | 02f0899d78e3 | 1.7.6 final | 19/19 | Sim |

É importante distinguir os artefatos: o ZIP **final** foi submetido à matriz completa na 4.2.0 e na 5.3.0. Na 4.2.23, 4.3.2 e 4.4.3 foi testado o candidato 1.7.6 com o mesmo manifesto mínimo e o mesmo Python; a diferença até o ZIP final é documentação. Na 4.5.16 a instalação foi repetida com o ZIP final, somada às 19 regressões do mesmo Python já verificadas na 1.7.5. Para 5.0.1/5.1.2/5.2.4 reutilizamos a evidência 1.7.5 do código byte a byte idêntico, sem dizer que o novo ZIP inteiro foi novamente executado nessas três versões. Os JSONs preservam os hashes de pacote e as origens correspondentes.

Os testes incluem referências, hierarquias e sinais de escala, Location/Rotation/Dimensions, condições de recusa previstas, cache, Geometry Nodes afim, isolamento de dados, Offset/Endpoint, Live, Undo/Redo, desenho dos painéis e persistência. A grade de referências permanece com 8.064 combinações por versão, incluindo aceitações e recusas esperadas, além das demais matrizes. O mínimo 4.2.0 e o patch 4.2.23 foram executados; não inferimos suporte somente pelo patch mais recente.

## Persistência entre versões

Um arquivo criado na 4.2.0, contendo Frame com fonte vinculada, posição relativa, configurações de distribuição e modificador afim de Dimensions, foi aberto na 5.3.0. Foram conferidos matriz mundo, Scale nativo, Location relativa, Dimensions, UID/fonte do Frame, seleção de referência e modificador. A fixture representativa passou. Isso não promete abrir todo arquivo novo em versões antigas nem certifica todas as combinações de migração.

## Manutenção dos testes

A fixture do cache agora usa a API pública de Actions correspondente aos dados disponíveis: curvas legadas antes dos slots, layers/channelbags onde existem. É preparação de dados de teste, sem adicionar animação ao produto. O teste de instalação lê o mínimo do manifesto em vez de assumir que toda versão abaixo de 5.0 deve ser rejeitada. O diagnóstico anterior de encerramento da GUI na 5.1 continua documentado na [matriz 1.7.5](compatibility-1.7.5.md); não foi acrescentado um workaround ao add-on por esse problema do executor.

## Viabilidade da futura 2.0

[Estudo completo de Edit Mode](edit-mode-2.0-feasibility.md). Um probe independente, sem importar o add-on, passou na 4.2.0, 4.2.23, 4.3.2, 4.4.3 e 5.3.0. Exercitou BMesh, edição multiobjeto, referências matriciais externas sob escala não uniforme/espelhamento, captura da orientação nativa de face com conferência da normal, preservação de vértices fora da seleção, Undo/Redo e persistência de atributos.

Também confirmou uma dificuldade de identidade: duplicação de geometria herda valores de IDs customizados. Referências persistentes não podem ser implementadas simplesmente guardando índice ou um inteiro sem política para mudanças topológicas. Destinos conflitantes de faces compartilhadas e a definição de Rotation/Scale de uma seleção são decisões da 2.0, comuns às versões antigas e novas.

O estudo não identificou uma API exclusiva de 4.5/5.x necessária para o Mesh Edit Mode proposto. Isso permite adotar 4.2 como base das funções atuais sem bloquear, por essa razão, a futura 2.0. Não foi implementada a funcionalidade 2.0 no instalador 1.7.6.

## Limites

A evidência é finita e Windows x64. Não há certificação de todos os patches, GPUs, sistemas operacionais, backends ou arquivos. A 2.0 ainda precisa de definições e testes para shape keys, elementos degenerados, conectividade, referências persistentes, malhas compartilhadas e desempenho em seleções densas. Os limites documentados atuais de constraints, precisão e hierarquias não rígidas continuam os mesmos.

O custo de compatibilidade observado para o produto atual foi baixo: declaração de mínimo e validação. Não foi necessário avisar sobre um grande retrabalho porque ele não surgiu. Não foram implementadas otimização de Normal, flexibilização de constraints ou funções de animação.

[Resultados](../../tests/better_item/results/1.7.6/), [ferramentas de reprodução](../../tests/better_item/compatibility/README.md), [API BMesh 4.2](https://docs.blender.org/api/4.2/bmesh.html), [extensões e API 4.2](https://developer.blender.org/docs/release_notes/4.2/python_api/).
