# Better Draft v0: calibração do reconhecimento

Etapa 3 da especificação: núcleo de reconhecimento e calibração (seção 6). Menus, diálogo e escritor DXF ainda não existem.

## 1. O que foi executado

| Item | Valor |
| --- | --- |
| Código | `src/better_draft/geometry2d.py`, `recognition.py` (sem `bpy`), `region.py` (lê a malha avaliada) |
| Script | `tests/better_draft/calibration/calibrate.py`, tabelas por `report.py` |
| Blender | 4.2.0 (`a51f293548ad`) e 5.3.0, portáteis Windows x64; ZIPs conferidos por SHA256 (4.2.0 `b6e72874…bc65`, 5.3.0 `3ac567a6…abfa8`) |
| Perfil | isolado (`BLENDER_USER_CONFIG/SCRIPTS/DATAFILES/EXTENSIONS`), `--background --factory-startup --python-exit-code 1` |
| Volume | 96 configurações de forma × 6 tolerâncias de ajuste (576) + 55 da varredura da tolerância de reta = 631 linhas por versão |
| Resultado entre versões | tabelas de 4.2.0 e 5.3.0 idênticas, linha a linha (só o cabeçalho com a versão difere) |
| Testes unitários do núcleo | `tests/better_draft/test_recognition.py`: 25 testes, todos passando (Python 3.13 do Blender 5.3 instalado, fora do Blender) |

Tabelas completas: [4.2.0](calibracao/tabelas-4.2.0.md), [5.3.0](calibracao/tabelas-5.3.0.md). Os JSON brutos (1,9 MB cada) ficaram fora do repositório e se regeneram com o script.

Fontes das formas: vértices analíticos via bmesh; modificador Bevel (`affect = VERTICES`); operador `bmesh.ops.bevel`; primitivos Circle e Cylinder; Bevel + Solidify (malha com espessura, região escolhida pela maior face).

## 2. Como o reconhecimento decide

1. Pontos repetidos são removidos. Vértices com giro abaixo da **tolerância de reta** viram parte de uma reta só se o desvio até a reta resultante ficar dentro da **tolerância de ajuste**. Um ponto de inflexão entre dois arcos opostos nunca é absorvido.
2. Um vértice pode ficar dentro de um arco se o giro estiver abaixo do limite de canto (65°) e as duas cordas vizinhas tiverem comprimento parecido (razão ≤ 2).
3. Dois vértices vizinhos pertencem ao mesmo arco se os quatro pontos em volta couberem num círculo dentro da tolerância de ajuste. Sequências contínuas formam o candidato; o círculo de todo o trecho é reajustado (Kåsa centrado + Gauss-Newton). Se o laço inteiro passa, o candidato é CIRCLE.
4. Sobreposição entre candidatos: o mais longo fica com as arestas.
5. Decisão: ARC/CIRCLE se segmentos ≥ mínimo **e** confiança ≥ limite; caso contrário, linhas. Marcações: "linhas" num trecho vence tudo; "arco" força o ajuste do trecho marcado (unido ao candidato que ele toca) e, fora da tolerância, recusa a operação inteira.
6. Linhas vizinhas de um arco terminam exatamente no ponto final do arco (sem fresta). Entre dois arcos, a fresta é medida e reportada.

### Fórmula de confiança

```
confiança = c_n × c_giro × c_corda × c_desvio
c_n      = 1 − exp(−(n − 1) / 1,5)          n = número de segmentos
c_giro   = máx(0, 1 − cv(|giros internos|) / 0,5)
c_corda  = máx(0, 1 − cv(comprimento das cordas) / 0,5)
c_desvio = máx(0, 1 − (desvio máximo / tolerância de ajuste)²)
```

`cv` = desvio padrão / média. Os giros internos excluem os dois pontos de tangência (que têm meio giro).

Os coeficientes 1,5 e 0,5 foram escolhidos por mim e não comparados com alternativas; a calibração ajusta o **limite** sobre essa fórmula. Nos dados, quem mais decide é a tolerância de ajuste (o candidato nem se forma) e o mínimo de segmentos. `c_giro` e `c_corda` só pesaram no Bevel com perfil 0,3 (cv de giro 0,14 a 0,36) e nas facetas irregulares (cv de corda até 0,2).

## 3. Tabela de calibração: confiança × segmentos × desvio

Tolerância de ajuste 0,01 mm, tolerância de reta 0,1°. Arcos e círculos verdadeiros gerados pelo Blender (Bevel modificador e operador, primitivos, bmesh), peça até 40 mm, perto da origem:

| Segmentos | Confiança | Desvio máx. (mm) | Erro de raio máx. (mm) | Erro de centro máx. (mm) | Decisão com mínimo 4 e limite 0,7 |
| --- | --- | --- | --- | --- | --- |
| 2 | 0,487 | < 1e-15 | 4,8e-06 | 5,8e-06 | linhas (abaixo do mínimo) |
| 3 | 0,736 | 4,2e-07 | 5,6e-06 | 7,0e-06 | linhas (abaixo do mínimo) |
| 4 | 0,865 | 1,7e-06 | 7,1e-06 | 9,5e-06 | ARC |
| 6 | 0,964 | 1,2e-06 | 5,1e-06 | 6,4e-06 | ARC / CIRCLE |
| 8 | 0,991 | 1,6e-06 | 7,3e-06 | 9,9e-06 | ARC / CIRCLE |
| 12 | 0,999 | 1,2e-06 | 1,4e-07 | 2,7e-07 | CIRCLE |
| 16 a 64 | 1,000 | 2,8e-06 | 6,2e-06 | 9,3e-06 | ARC / CIRCLE |
| 128 (Bevel) | 0,994 a 0,999 | 2,0e-06 | 1,3e-06 | 4,4e-06 | ARC |

Mesma tolerância, casos que degradam o ajuste:

| Caso | Segmentos | Confiança | Desvio máx. (mm) | Resultado |
| --- | --- | --- | --- | --- |
| Peça × 100 (cantos R 500 mm) | 8 | 0,991 | 6,6e-05 | ARC; erro de raio 1,6e-04 mm |
| Objeto escalado 2,5× e rotacionado | 8 | 0,991 | 4,0e-06 | ARC; R = 12,5 mm |
| Escala de cena 0,001 | 8 | 0,991 | 1,3e-06 | ARC |
| Objeto a 1 km (malha local perto da origem) | 8 | 0,991 | 1,6e-06 | ARC, sem perda |
| Malha deslocada 100 m da origem do objeto | 8 | 0,874 a 0,900 | 2,7e-03 | ARC; erro de raio 4,1e-03 mm |
| Malha deslocada 1 km da origem do objeto | 2 a 4 | ≤ 0,512 | 7,4e-03 | linhas: ruído de float32 ≈ 0,06 mm |
| Círculo com ruído radial σ = 0,0002 mm | 32 | 0,996 | 4,2e-04 | CIRCLE |
| σ = 0,001 mm | 32 | 0,947 | 2,1e-03 | CIRCLE |
| σ = 0,003 mm | 32 | 0,589 | 6,3e-03 | linhas (confiança) |
| σ ≥ 0,01 mm | 3 a 8 | ≤ 0,733 | ~0,01 | linhas |
| Elipse 1,001 | 32 | 0,749 | 5,0e-03 | CIRCLE |
| Elipse 1,01 | 9 a 11 (pedaços) | ≤ 0,602 | ≤ 9,7e-03 | linhas |
| Elipse 1,1 | 4 a 8 (pedaços) | ≤ 0,459 | ≤ 1,0e-02 | linhas |
| Bevel perfil 0,3 | 3 a 4 (pedaços) | ≤ 0,585 | ≤ 7,2e-03 | linhas |
| Bevel perfil 0,7 / 1,0 | 2 / — | ≤ 0,487 | — | linhas |
| Bevel em cantos de 60° e 120° | 2 a 9 (pedaços) | ≤ 0,592 | ≤ 9,3e-03 | linhas (ver achado 1) |
| Facetas irregulares feitas à mão (5 a 10 lados) | 2 a 3 | ≤ 0,491 | — | linhas |
| Polígono regular de 6, 8, 12 lados | 6 / 8 / 12 | 0,964 / 0,991 / 0,999 | ~1e-07 | CIRCLE (ver achado 2) |

Casos de controle, todos corretos: reta dividida em 10 sem giro → uma LINE (também com a malha a 100 m); oblongo → 2 ARC + 2 LINE com tangência ≤ 1e-4°; arco de 8 segmentos seguido de chanfro → ARC de 8 segmentos, chanfro separado; curva em S (R 10 e R 6, 4/8/16 segmentos) → dois ARC com sentidos opostos e todos os segmentos; facetado de 3 segmentos → linhas, e marcado como arco pelo atributo → ARC R 5; Bevel + Solidify → região da maior face, 4 ARC.

### Varredura da tolerância de ajuste

Arcos esperados com segmentos ≥ 4 (167 no total):

| Tolerância (mm) | Reconhecidos | Perdidos, fora os perdidos em toda a faixa* | Falsos ARC/CIRCLE |
| --- | --- | --- | --- |
| 0,0005 | 142 | ruído σ 0,0002 / 0,001 / 0,003 / 0,01; malha a 100 m | polígonos 6/8/12 |
| 0,001 | 145 | ruído σ 0,001 / 0,003 / 0,01; malha a 100 m | polígonos; 1 arco num pedaço da elipse 1,01 |
| 0,002 | 146 | ruído σ 0,001 / 0,01; malha a 100 m | polígonos; 1 arco num pedaço da elipse 1,01 |
| 0,005 | 146 | ruído σ 0,003 / 0,01; malha a 100 m | polígonos |
| **0,01** | **148** | ruído σ 0,003 / 0,01 | polígonos; elipse 1,001 como CIRCLE |
| 0,05 | 150 | — | polígonos; elipse 1,001 como CIRCLE |

\* Perdidos em todas as tolerâncias: Bevel em cantos de 60°/120° (12 arcos), malha a 1 km (4), ruído σ 0,03 mm (1). O ruído é sorteado com semente fixa; perto do limite o resultado oscila de uma tolerância para outra (σ 0,003 passa em 0,002 e falha em 0,005).

### Varredura da tolerância de reta (ajuste 0,01 mm)

| Tolerância de reta | Bevel 64 segmentos | Bevel 128 segmentos | Retas subdivididas (origem e 100 m) |
| --- | --- | --- | --- |
| 0,05° / 0,1° / 0,25° | 64 | 128 | uma LINE |
| 0,5° | 64 | 126 (perde as cordas de tangência) | uma LINE |
| 1,0° | 62 | 12 (o arco se desfaz) | uma LINE |

## 4. Valores padrão

Aprovados por Gabriel em 18/11/2026, como propostos abaixo.

| Parâmetro | Proposta | Justificativa nos dados |
| --- | --- | --- |
| Tolerância de ajuste | **0,01 mm** | Arcos do Blender desviam ≤ 7e-5 mm em peças de até 4 m (margem ≥ 140×). É o menor valor que ainda aceita malha a 100 m da origem do objeto. Continua recusando perfis de Bevel ≠ 0,5, Bevel em canto não reto, elipses ≥ 1,01. Custo: elipse 1,001 (5 µm fora do círculo) vira CIRCLE. |
| Tolerância de reta | **0,1°** | Nenhum caso precisou de mais que 0,05° para juntar retas subdivididas; 0,5° já come as cordas de tangência de um Bevel de 128 segmentos. 0,1° preserva Bevel de 90° até 450 segmentos. |
| Mínimo de segmentos | **4** (da especificação) | Arcos limpos de 3 segmentos têm confiança 0,736 e seriam aceitos pela confiança sozinha; o mínimo é o que separa o facetado intencional, como pede o caso da seção 6. |
| Limite de confiança | **0,7** | Arcos verdadeiros com ≥ 4 segmentos: ≥ 0,865 (ruído σ 0,001 mm: 0,947). Maior negativo não circular com ≥ 4 segmentos: 0,602 (elipse 1,01). 0,7 fica no intervalo e abaixo de 0,736, para que baixar o mínimo para 3 funcione sem mexer no limite. Alternativa: 0,8 recusaria a elipse 1,001, mas aí mínimo 3 exigiria baixar o limite também. |

Constantes internas (fora do diálogo, documentadas): limite de canto 65°, razão de cordas 2,0, coeficientes da fórmula 1,5 e 0,5. A razão de cordas entrou porque, sem ela, a tolerância de 0,01 mm aceitava uma reta de 10 mm mais duas cordas de um canto R 5 / 32 segmentos como um círculo de R 106 (desvio 0,004 mm), e trapézios isósceles (corda, reta, corda) sempre cabem num círculo. Todos os arcos do Blender medidos têm cordas iguais (cv 0,000).

## 5. Achados

1. **Bevel do Blender em canto não reto não gera arco circular.** Com perfil 0,5, um canto de 120° desvia 0,012 mm do melhor círculo e um de 60° desvia 0,044 a 0,046 mm (largura 4 mm; cordas variam até 1,33×). O raio também não bate com o círculo tangente esperado (60°: 2,09 a 2,12 mm contra 2,31 mm). Igual em 4.2.0 e 5.3.0. Esses cantos saem como linhas em todas as tolerâncias testadas (até 0,05 mm); marcados como arco, a operação será recusada por estar fora da tolerância. Cantos de 90° são arcos exatos.
2. **Polígono regular e círculo de mesmo número de vértices são geometricamente iguais.** Um hexágono ou octógono regular vira CIRCLE com a mesma confiança do primitivo Circle; nenhuma métrica da malha separa os dois. A saída prevista é marcar "linhas".
3. **Precisão float32 depende da distância entre a malha e a origem do objeto**, não da posição do objeto no mundo: objeto a 1 km com malha local perto da origem não perde nada; malha a 100 m da própria origem perde ~0,003 mm; a 1 km, ~0,06 mm, e os arcos viram linhas.

## 6. Ainda não feito nesta etapa

- Escritor DXF, ezdxf, diálogo de exportação, menus, operadores de marcação, relatório pós-exportação, ZIP.
- Testes em 4.5 e demais 5.x (só 4.2.0 e 5.3.0 executados).
- Recusa por malha não plana, laço aberto e laços que se cruzam está coberta no núcleo e no extrator, mas só por testes unitários do núcleo (laços que se cruzam, ilhas); o caminho completo dentro do Blender ainda não tem teste.
- Desempenho: medido só no núcleo, fora do Blender (círculo de 4096 vértices em 0,08 s; retângulo com quatro cantos de 256 segmentos em 0,41 s).
