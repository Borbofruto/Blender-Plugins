# Proposta visual Better Item — sem merge e sem versão de destino decidida

Base: `02f6728`. Branch `proposal/better-item-ui-precision`. Nenhuma mudança desta branch foi incorporada à main. Gabriel decidirá se entra em manutenção 1.7.9 ou 1.8.0.

## Mudanças propostas

| Grupo Transform | Estável | Nativo conferido em 4.2.0/5.3.0 | Proposta |
| --- | ---: | ---: | ---: |
| Location | 3 | 5 | 5 |
| Rotation | 3 | 5 | 5 |
| Scale | 3 | 3 | 3 |
| Dimensions | 3 | 5 | 5 |

São metadados de apresentação dos campos. Getters, setters, unidades, RNA IDs, funções de migração, solvers e persistência por método permanecem intactos. Frame e Spacing já tinham precision 5 e não foram alterados. Scale continua adimensional.

BI-F006 recebe o título **Orientation sync paused**, em vez de Reference unavailable. O texto que avisa sobre eixos possivelmente desatualizados e retentativa automática foi preservado. Outros diagnósticos continuam com Reference unavailable, Setup needed ou Operation failed conforme seu estado. A política de suspensão/retentativa não mudou.

## Correção da premissa sobre Unit Scale

As capturas sequenciais da qualificação anterior mostravam 12,346 mm no addon após mudar para 0,001. Isso não provava que a mudança de escala eliminava a diferença. **Nos novos processos frios, a baseline mostra 12,3 mm tanto em 1 quanto em 0,001**, em 4.2.0 e 5.3.0; o nativo mostra 12,346 mm. O painel real foi capturado além da fixture lado a lado. A causa específica da imagem antiga não foi reproduzida; não a atribuir a um ganho de precisão por unidade nem declarar que foi provadamente um cache de UI.

O código do Blender explica o resultado frio: a formatação de comprimentos usa um orçamento de algarismos significativos, descontando os algarismos inteiros do valor convertido para a unidade. Para 12,3456789 mm há dois algarismos inteiros: precision 3 deixa uma casa (12,3); precision 5 deixa três (12,346). O caminho de unidades limita a contagem visível e não promete cinco casas decimais fixas. Mudar Unit Scale mantendo o mesmo comprimento físico deixa o valor convertido em mm igual; não muda esse orçamento do campo.

Fontes primárias conferidas: [formatação 4.2.0](https://github.com/blender/blender/blob/v4.2.0/source/blender/blenkernel/intern/unit.cc#L1597), [chamada de UI 4.2.0](https://github.com/blender/blender/blob/v4.2.0/source/blender/editors/interface/interface.cc#L3709), [formatação 5.3.0](https://github.com/blender/blender/blob/v5.3.0/source/blender/blenkernel/intern/unit.cc#L1665) e [chamada de UI 5.3.0](https://github.com/blender/blender/blob/v5.3.0/source/blender/editors/interface/interface.cc#L4204).

## Validação da proposta

- Quatro comparações frias da baseline: 4.2.0 e 5.3.0 × Unit Scale 1 e 0,001.
- Quatro comparações frias do candidato nas mesmas configurações, com capturas da fixture nativa/addon e do painel original. Os quatro grupos têm a precisão RNA do campo nativo e mantêm os mesmos valores armazenados.
- Candidato em Unit Scale 1: regressão native-sync e os 590 cenários de unidades executados também em cada build. Todos passaram. O teste de título confere BI-F006 e preservação dos títulos dos demais diagnósticos.
- Sem digitação física, certificação de todos os layouts, nem matriz completa de 25 entradas do candidato. A matriz de seis builds na main pertence ao ZIP estável, não a este candidato.

[Qualificação e hashes](../../tests/better_item/results/ui-precision-proposal/qualification.json), [capturas baseline](../../tests/better_item/results/ui-precision-proposal/baseline/), [capturas proposta](../../tests/better_item/results/ui-precision-proposal/proposal/).

## Empacotamento e decisão pendentes

O `addons/better_item.zip` rastreado nesta branch continua sendo o estável `6a01eb80…`. Para a prova foi gerado apenas no D: um candidato temporário `a90a9101…`, com os dois módulos Python alterados, manifesto ainda 1.7.9 e suite temporária apontando a seus fingerprints. **Não distribuir esse candidato como release aprovada.** A divergência entre src proposto e ZIP rastreado é deliberada; o gate de release deve recusá-la até haver decisão, versão e empacotamento.

Para reproduzir: criar cópia temporária da branch no D:, construir uma extensão a partir de src/better_item com o builder nativo do Blender para o addons dessa cópia, atualizar nessa cópia o SHA do ZIP e o fingerprint Python de suite.json, e usar prepare_matrix/run_matrix existentes. O algoritmo do fingerprint está no README de compatibilidade. Os manifests usados estão nas pastas de baseline/proposta acima. Definir BI_UI_EXPECTATION=baseline ou proposal e BI_UI_UNIT_SCALE=1 ou 0.001; os valores são registrados no JSON.

A nomenclatura do mínimo e o possível acesso a window.scene fora da proteção **não foram alterados nesta branch**. Precisão visual não aumenta a precisão de armazenamento nem estabelece tolerância física absoluta em mm.
