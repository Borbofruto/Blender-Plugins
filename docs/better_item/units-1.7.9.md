# Better Item 1.7.9 — qualificação de unidades e precisão física

Executada em **17/11/2026**, após a publicação `77ce932`. **Nenhum código do addon ou ZIP foi alterado.** SHA256: `6a01eb809165347e94668d259a492b922b69f0c368657cae48599a2f57a9f029`. Os testes novos usam o runner existente e ambientes/perfis separados no D:.

## Conclusão

A conversão de comprimentos e do mínimo explícito em mm foi consistente nas configurações testadas. Scale XYZ continuou adimensional. Isso não certifica uma precisão absoluta universal em milímetros: a resolução depende das coordenadas, da geometria e das transformações nativas float32.

Há dois achados que precisam permanecer explícitos:

1. **Exibição:** um mesmo valor físico pode ser arredondado mais cedo no addon conforme Unit Scale. Em 5.3.0, `12,3456789 mm` aparece como `12,3 mm` em Unit Scale 1 e `12,346 mm` em 0,001. O nativo mostra `12,346 mm` nos dois casos. Os valores RNA armazenados são iguais. A propriedade do addon tem `precision=3`, contra 5 no campo nativo; isso é uma pista técnica da causa, não uma mudança implementada. Pendência de apresentação para 1.8.x.
2. **Tolerância física:** Geometry Bounds pode aceitar uma diferença superior ao mínimo configurado, pois esse mínimo não é o erro máximo admissível. Um gap de 1 mm a 1 km da origem teve erro observado de até **0,050976574 mm**, aceito pelo orçamento de arredondamento atual. Não anunciar `Minimum Separation` como garantia de exatidão absoluta.

## O que foi executado agora

| Blender Windows x64 | Cenários numéricos | Configurações GUI | Casos de precisão aceitos | Recusas esperadas e atômicas |
| --- | ---: | ---: | ---: | ---: |
| 4.2.0 | 590/590 | 6 | 91 | 161 |
| 4.2.23 | 590/590 | 6 | 91 | 161 |
| 5.3.0 | 590/590 | 6 | 91 | 161 |

São **590 cenários internos por build**, com **26 configurações de unidades**, e seis configurações adicionais em GUI real. O runner lançou somente as duas entradas novas em cada build. A matriz anterior completa de 24 entradas não foi repetida, pois o runtime permaneceu byte a byte igual. Não reclassificar esses registros como três execuções novas da suíte inteira de 25 entradas.

A regressão numérica foi incluída na suíte padrão, que agora tem **25 entradas**. O estudo GUI é opt-in. A aprovação numérica significa conformidade com as asserções descritas abaixo; não aprovação da apresentação nem certificação de um erro máximo físico que o produto não definiu.

### Configurações e operações

- Metric: Unit Scale 1, 0,001, 0,01, 0,000001 e 1000; exibição Adaptive, Meters e Millimeters em cada escala.
- Imperial: Unit Scale 1, 0,3048, 0,0254 e 0,001; Feet e Inches.
- None: Unit Scale 1, 0,001 e 1000, como controle de convenção interna. **None não declara uma unidade física**; o parser nativo rejeita o sufixo `mm`. Não equivale a certificação de uma UI em milímetros.
- Entrada explícita de `mm` pelo parser nativo e aplicação pelos setters RNA, comparadas com Location nativa. Conversão de 1 inch para 25,4 mm. Python/RNA recebem Blender units; não reinterpretar um número Python como mm só porque o painel exibe mm.
- Location e Dimensions com Frame transladado/rotacionado, pai rotacionado com escala não uniforme e estágio GN afim; Frame Location e Scale adimensional.
- Offset/Endpoint com Origins, Bounds Center, Surface e Volume, em malhas fechadas cujo centro é deslocado da origem; oráculo geométrico independente e preservação da malha.
- Minimum Separation literal em mm: intervalos/comprimentos abaixo do mínimo recusam sem movimento; acima do mínimo são aceitos conforme o contrato de cada método.
- Troca da unidade exibida sem alterar geometria; troca de Unit Scale sem alterar coordenadas brutas, com a correspondente mudança da interpretação física. Inspeção aquecida após mudança de Unit Scale coincide com uma leitura nova.
- Escada de precisão: origens físicas em 0, 1.000, 1.000.000 e 1.000.000.000 mm; intervalos de 0,00000001 a 1 mm; pontos e gaps geométricos. Registrados o ULP em mm, o resultado efetivo, o erro e a reversão integral nas recusas.

## O que unidade, Scale e precisão significam aqui

O Blender mantém coordenadas internas. Unit Scale faz parte da conversão dessas coordenadas para comprimentos exibidos; mudar a unidade não deve aplicar Scale ou redimensionar a malha silenciosamente. Isso é consistente com o [manual oficial de unidades](https://docs.blender.org/manual/pt/4.2/scene_layout/scene/properties.html) e foi verificado pelos testes. `bpy.utils.units.to_value` é o parser nativo usado nesta qualificação ([API](https://docs.blender.org/api/current/bpy.utils.units.html)).

Os fixtures fisicamente equivalentes foram construídos separadamente para cada escala, usando o valor efetivamente armazenado de Unit Scale (que também tem arredondamento). O oráculo mede vértices avaliados e matrizes em float64 e converte os resultados para mm; ele não usa o resolvedor do addon para gerar o resultado esperado.

O parâmetro `Minimum Separation (mm)` tem default 0,00001 mm e limite configurável inferior de aproximadamente 0,00000001 mm. Ele regula condições de separação/ordenação e certos comprimentos mínimos; **não é uma tolerância de erro físico máximo**. Endpoint e Geometry Bounds têm contratos próprios: o mínimo não deve ser aplicado indiscriminadamente como gap de todas as operações. Uma configuração menor não recupera precisão já perdida na geometria ou nas matrizes float32.

Pontos próximos da origem conseguiram intervalos de 0,00000001 mm nos cenários testados. Em geometria de 2 mm e coordenadas maiores, nem todo intervalo desse tamanho é representável; há recusas e também resultados aceitos cujo erro absoluto excede esse intervalo. São efeitos distintos de uma conversão errada por fator 1000.

Maiores erros geométricos aceitos na amostra, medidos contra o gap efetivamente armazenado após conversão:

| Build | Sistema / Unit Scale | Distância à origem | Gap pedido | Erro máximo observado |
| --- | --- | ---: | ---: | ---: |
| 4.2.0 | IMPERIAL / 0.3048 | 1e+06 mm | 1 mm | 0.050976574 mm |
| 4.2.23 | IMPERIAL / 0.3048 | 1e+06 mm | 1 mm | 0.050976574 mm |
| 5.3.0 | IMPERIAL / 0.3048 | 1e+06 mm | 1 mm | 0.050976574 mm |

Para prometer um limite absoluto em mm seria necessário definir **erro físico admissível**, faixa de coordenadas/tamanhos e uma política de recusa. Isso mudaria o comportamento/contrato e não foi implementado como parte desta qualificação. O orçamento nativo atual, as recusas e os erros observados estão registrados sem serem apresentados como exatidão universal.

## Evidência visual e limitações

[Unit Scale 1](../../tests/better_item/results/1.7.9/units/5.3.0/units-gui-00-METRIC-MILLIMETERS.png) e [Unit Scale 0,001](../../tests/better_item/results/1.7.9/units/5.3.0/units-gui-01-METRIC-MILLIMETERS.png) mostram a diferença de arredondamento do mesmo comprimento. Os demais screenshots e valores RNA estão nos resultados. A comparação visual foi uma inspeção humana das imagens, não OCR.

Foram validados renderização dos campos e valores RNA, sem erros de draw. **Não houve digitação por teclado ou mouse nos widgets**, edição sem sufixo, certificação de todos os tamanhos/larguras do painel ou interação física com unidades. A entrada textual em `mm` foi exercitada pela API do parser, seguida dos setters; não equivale a todo o fluxo de uma edição interativa. macOS/Linux GUI e outras builds não foram repetidos nesta qualificação.

## Desenvolvimento do teste e reprodução

A primeira tentativa falhou ao serializar um escalar NumPy no JSON; corrigido no teste. Uma rodada ampliada teve 78 divergências de preparação: o teste escolhia Placement antes de Method, e a troca de método restaurava corretamente sua escolha persistida. A ordem foi corrigida e a configuração efetiva passou a ser verificada. Nenhuma dessas ocorrências motivou alteração do addon. Os registros estão em `results/1.7.9/units/test-development/`, separados da aceitação final.

```powershell
python tests/better_item/compatibility/prepare_matrix.py --repository PATH_TO_REPO --workspace D:/better-item-unit-check
python D:/better-item-unit-check/run_matrix.py --exe PATH_TO_BLENDER --version VERSION --studies --only test_better_item_units179.py test_better_item_units_gui179.py
```

[Aceitação e proveniência](../../tests/better_item/results/1.7.9/units/acceptance.json), [observações físicas/visuais](../../tests/better_item/results/1.7.9/units/observations.json), [resultados brutos](../../tests/better_item/results/1.7.9/units/README.md).
