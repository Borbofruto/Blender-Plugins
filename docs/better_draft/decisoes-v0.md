# Better Draft v0: decisões de Gabriel (18/11/2026)

Registro das respostas às perguntas da seção 8 da especificação e da calibração. Complementa [especificacao-v0.md](especificacao-v0.md) e [calibracao-v0.md](calibracao-v0.md).

## Valores padrão

| Parâmetro | Padrão | No diálogo |
| --- | --- | --- |
| Tolerância de ajuste | 0,01 mm | sim |
| Tolerância de reta | 0,1° | sim |
| Mínimo de segmentos (arco) | 4 | sim |
| Limite de confiança | 0,7 | sim |
| Mínimo de segmentos para laço inteiro virar CIRCLE | 8 | sim (novo) |
| Área mínima de uma parte solta | 1% da área da maior parte | sim (novo) |

Com o mínimo de 8 para CIRCLE, hexágono regular sai como linhas; octógono e acima viram CIRCLE. Isso diverge da linha "Furo circular, segmentos 6 a 64" da seção 6 da especificação: furos de 6 segmentos passam a sair como linhas por padrão.

## Interface

- Rótulos e mensagens em inglês, como no Better Item.
- Nome final: ainda em aberto; segue "Better Draft" provisório, centralizado em `constants.py`.

## Peças soltas no mesmo objeto

- O addon identifica as partes soltas da região e interrompe a exportação, oferecendo:
  1. **Exportar só a maior peça** (por área). Se as maiores forem iguais (mesmo contorno dentro da tolerância de ajuste, depois de deslocar e girar; espelhada conta como diferente), exporta uma só. Se forem diferentes mas com a mesma área exata, a operação é recusada e a mensagem pede para separar as partes (Separate > By Loose Parts).
  2. **Exportar todas as partes**, cada uma como peça própria.
- Partes com área abaixo do limite (padrão 1% da maior, regulável) são ignoradas e citadas no relatório (vértices soltos, faces perdidas).

## Cena intacta

O addon pode criar cópias temporárias para converter ou manipular dados, mas a cena que a pessoa encontra depois de qualquer ação do addon tem de estar igual à de antes. A única escrita permitida continua sendo o atributo `better_draft_arc_mode`, por ação explícita de marcação.

## Limite declarado

Bevel do Blender em canto não reto não gera arco circular (achado 1 da calibração); esses cantos saem como linhas.

## ezdxf

Escolhido o ezdxf 1.4.5, empacotado como wheel junto com pyparsing 3.3.3, typing_extensions 4.16.0 e fonttools 4.68.0 (todas `py3-none-any`, SHA256 conferido contra o PyPI). O ZIP montado com `blender --command extension build` instalou com `--offline-mode` em perfis isolados dos portáteis 4.2.0 e 5.3.0. Em ambos, o ezdxf foi importado de `extensions/.local/.../site-packages`, escreveu LINE/ARC/CIRCLE com `$INSUNITS = 4` (mm) e releu o arquivo (`tests/better_draft/test_wheel_install.py`). Limites desse teste: a máquina tinha rede, e o modo offline só impede o acesso online do Blender; o conflito com outra extensão que traga versões diferentes dessas bibliotecas no mesmo site-packages compartilhado não foi testado. O fonttools imprime um aviso ao carregar uma fonte do sistema (`'name' table stringOffset incorrect`), sem efeito no resultado.
