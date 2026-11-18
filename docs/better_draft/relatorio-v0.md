# Better Draft v0 (0.1.0): relatório

18/11/2026. Branch `feature/better-draft-v0`, sem push e sem merge.

## Artefato

| Item | Valor |
| --- | --- |
| ZIP | `addons/better_draft.zip`, 2 734 259 bytes |
| SHA256 | `E7CDE78D1E347B64599CF31B88A11443BADBC781BA2F46BFF1D6688656F57C84` |
| Origem | `git -c core.autocrlf=false archive HEAD:src/better_draft` no commit `4db8b93`; nenhum `.py`/`.toml` com CRLF |
| Validação | `blender --command extension validate` (4.2.0): sem erros |
| Conteúdo | código do addon, `LICENSE` (GPL-3.0), wheels ezdxf 1.4.5, fonttools 4.68.0, pyparsing 3.3.3, typing_extensions 4.16.0 |

## O que foi testado, e onde

Executado nesta sessão, em portáteis Windows x64 conferidos por SHA256, cada um com perfil novo e isolado. O ZIP acima foi instalado com `--offline-mode --command extension install-file`.

| Bateria | 4.2.0 | 4.5.16 LTS | 5.3.0 |
| --- | --- | --- | --- |
| `test_wheel_install.py` (ezdxf importado da extensão, DXF escrito e relido) | passou | passou | passou |
| `test_blender_v0.py` (16 casos de ponta a ponta; DXF relido com ezdxf e com um leitor mínimo de códigos de grupo escrito no teste, as duas leituras conferidas uma contra a outra) | 16/16 | 16/16 | 16/16 |
| `test_recognition.py` (26) e `test_parts.py` (13), fora do Blender | Python 3.11.7 do 4.2.0 e 3.13 do 5.3 instalado: todos passaram | | |
| Calibração (`calibrate.py`, 631 linhas) | sim | não | sim |

Resultados brutos: `tests/better_draft/results/0.1.0/`.

Casos de ponta a ponta: em cada exportação o teste compara uma impressão digital da cena antes e depois (objetos, malhas, textos, matrizes, seleção, vértices, arestas, faces, atributos, modo). Uma recusa também tem de terminar sem nenhum arquivo novo.

| Caso | Verifica |
| --- | --- |
| registro | operador e entradas em File > Export, menu de contexto e menu Edge do Edit Mode |
| retângulo com Bevel (modificador, 8 seg.) | 4 ARC R 5 nos centros certos, 4 LINE de 10 e 30 mm, camada OUTER, `$INSUNITS` = 4, relatório `.txt` |
| chapa com furo de 32 seg. | CIRCLE R 8 em (30, 20) na camada INNER |
| furo hexagonal | 6 LINE com o padrão; CIRCLE com mínimo de círculo 6 |
| escala de cena 0,001; objeto escalado 2,5×, rotacionado e deslocado | raios 5 e 12,5 mm |
| normal virada para baixo | DXF idêntico ao da face virada para cima (sem espelhar) |
| chapa com espessura (Bevel + Solidify) | região da maior face, 4 ARC |
| Mark as Arc + Undo | atributo nas 3 arestas certas; exportar indisponível em Edit Mode; Undo remove as marcas; vértices intactos; facetado de 3 segmentos vira 1 ARC R 5 |
| Mark as Automatic sem marcas | não cria o atributo |
| "linhas" vence "arco" | canto com aresta "linhas" e arestas "arco" sai como linhas; os outros 3 cantos, ARC |
| arco forçado fora da tolerância | recusa com o desvio medido e o que fazer |
| peças soltas | Stop recusa (2 partes + 1 abaixo da área mínima); Largest exporta 1; All exporta 2 lado a lado com 5 mm |
| peças iguais / mesma área | cópia girada 40°: exporta uma; mesma área com formas diferentes: recusa |
| recusas | face torta, contorno que se cruza, furo tocando o contorno num vértice, World XY com peça inclinada, malha sem faces |
| um objeto ruim no lote | nenhum arquivo para nenhum objeto |
| um arquivo com dois objetos / um por objeto | peças lado a lado sem sobreposição; nomes `<arquivo>_<objeto>.dxf` |

## Mensagens de recusa (texto real)

- `warped: the reference face (largest) is not flat within 0.01 mm. In Edit Mode make a flat face active, or raise Fit Tolerance.`
- `rr: 7 edges marked as arc near (20.000, 18.380) mm do not fit one circle within 0.01 mm (deviation 0.5670 mm). Mark them Automatic or Lines, raise Fit Tolerance, or correct the vertices.`
- `parts: has 2 separate parts (plus 1 below the minimum area). Set Loose Parts to Largest or All in the export options, or separate them (Mesh > Separate > By Loose Parts).`

Todas começam com `Nothing exported.`

## Decisões de implementação a conferir

- **Lado do desenho:** o contorno é visto do +Z do objeto (ou +Y, +X para peça em pé). Sem isso, uma chapa com a normal para baixo saía espelhada; achado e corrigido nesta sessão.
- **Peças soltas:** são agrupadas por arestas compartilhadas. Duas faces que só se tocam num vértice contam como peças separadas.
- **Espaçamento padrão de 10 mm** entre peças lado a lado: escolhido por mim, sem dado de calibração.
- **Gravação dos arquivos:** primeiro tudo vai para arquivos temporários na mesma pasta; os arquivos finais só são substituídos depois que todos foram escritos. Uma falha no meio da troca final (depois de todas as gravações) não é revertida.
- **Relatório completo:** sai em `.txt` ao lado do DXF, não num bloco do Text Editor, porque isso criaria um dado novo na cena. O resumo vai para o aviso do Blender.

## Sem teste

- **DXF num programa de CAD ou de corte:** passo manual seu, exigido na seção 5 da especificação. Como o escritor também é o ezdxf, o teste tem um segundo leitor próprio (lê os códigos de grupo de LINE/ARC/CIRCLE); ele confirma tipo, camada, coordenadas, raio e ângulos, mas não valida o arquivo como um programa de CAD faria.
- **Undo em um único passo, pela interface:** em background, um Undo depois de marcar remove as marcas, mas cai em Object Mode, porque os passos empurrados por Python não espelham a pilha da interface. Falta conferir na interface que cada marcação é exatamente um passo.
- **Diálogo e menus clicados à mão:** os menus foram verificados como registrados, não abertos na tela.
- **Outras versões:** 4.3, 4.4, 5.0, 5.1 e 5.2 não rodaram; Linux e macOS também não.
- **Rede desligada de fato:** a máquina tinha rede; o `--offline-mode` só impede o acesso online do Blender.
- **Bibliotecas compartilhadas:** conflito de versão com outra extensão que traga ezdxf, fonttools ou pyparsing não foi testado.
- **Calibração vs. código final:** as tabelas foram geradas antes do mínimo de círculo (8) e da correção do lado do desenho. A lógica de reconhecimento é a mesma; a única diferença é que laços inteiros de 6 segmentos agora saem como linhas.
- **Desempenho:** não foi medido dentro do Blender, só no núcleo.
- **Atributo após modificadores:** se as marcas sobrevivem a modificadores que criam arestas não foi testado.

## Pendências suas

- Nome final do addon.
- Abrir um DXF num programa de CAD ou de corte.
- Push, merge e publicação, quando quiser.
