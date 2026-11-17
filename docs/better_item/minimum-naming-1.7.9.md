# Inventário do nome do mínimo — pacote 1.7.9 inalterado

Inspeção do runtime `02f6728`, ZIP `6a01eb80…`. Todos os locais abaixo se referem ao mesmo parâmetro ou ao limite convertido dele. Nenhum rótulo, mensagem, identificador ou README do pacote foi alterado. Os números de linha referem-se a essa base.

| Camada | Arquivo / linha | Identificador ou texto atual | Observação |
| --- | --- | --- | --- |
| Propriedade persistente Scene | `src/better_item/__init__.py:202` | `minimum_distance_mm`: Minimum Separation (mm) | Default 0,00001; mínimo RNA 0,00000001; não tem unidade LENGTH porque já é mm literal. |
| Descrição da propriedade | `__init__.py:203` | Minimum distinguishable starting origin separation. Also the minimum interval in Origins mode; Geometry Gap may be zero | Explica parte do contrato; não é erro físico máximo. |
| Rótulo do painel Solver Settings | `__init__.py:513` | Minimum (mm) | Sobrescreve o nome RNA com `text=`. |
| Propriedade do operador | `__init__.py:277` | `minimum_mm`: Minimum Distance (mm) | Mesmo default e limite inferior; exposta em redo/F9. Não renomear o identificador sem avaliar scripts. |
| Desenho do operador | `__init__.py:313` | `layout.prop(self, minimum_mm)` sem override | Mostra o nome Minimum Distance (mm), distinto do painel. |
| Captura no invoke | `__init__.py:294` | `self.minimum_mm = settings.minimum_distance_mm` | Faz a ponte Scene→operador. |
| BI-D001, caminho legado | `arrange.py:136` | Minimum Distance must be greater than zero. | Valida o mínimo. |
| BI-D001, Endpoint atual | `distribution.py:174` | Solver minimum separation must be positive. | Mesma conversão mm→BU. |
| BI-D001, Offset por pontos | `distribution.py:235` | Solver minimum separation must be positive. | Ocorrência distinta, mesmo texto. |
| BI-D001, Geometry Bounds | `geometry_arrange.py:36` | Solver minimum separation must be greater than zero. | Variante da mensagem positiva. |
| Manual incluído no ZIP | `src/better_item/README.md:190` | Minimum Separation (mm) | Descreve separações iniciais, Endpoint e intervalo Offset por pontos; Geometry Gap pode ser zero. |
| Tabela de suporte no mesmo README | `README.md:210` | BI-D001: Zero, too-small or invalid spacing/minimum | Usa apenas minimum, sem o rótulo completo. |

## Mensagens que usam o limite sem repetir seu nome

- `arrange.py:75–84`, BI-D001/D002: informa spacing e/ou distância mínima em mm com “at least”/“closer than”.
- `arrange.py:113`, BI-D003: informa “closer than … mm after distribution”.
- `geometry_arrange.py:52`, BI-D002: informa separação inicial “at least … mm”.
- `distribution.py:110–123`, BI-D002: ordem inicial ambígua/empatada, conforme as comparações com o mínimo.
- `distribution.py:175` e `:193`, BI-E001: Endpoint ou âncoras coincidentes/próximos/revertidos, comparados com o mínimo, sem repetir seu valor no texto.

## Fluxo técnico e preservação

`distribution.plan` (`distribution.py:266–270`) usa o argumento `minimum_mm` quando fornecido e, senão, Scene.minimum_distance_mm. Os caminhos de aplicação do operador (`__init__.py:321–332`) passam o valor capturado. `arrange._mm_per_unit` (`arrange.py:54–57`) converte pela escala da cena. Os caches/observadores incluem o valor do mínimo nos respectivos estados, mas não inventam um quarto conceito.

Mesmo conceito não significa um único slot de estado: a Scene guarda a configuração; o operador captura uma cópia no invoke. Um valor explícito via Python ou F9 pode diferir do valor da Scene. O inventário não autoriza fundir propriedades, centralizar estado ou alterar essa precedência.

A referência a Minimum/Maximum de bounding boxes, clamps de campos, mínimo suportado do Blender e flags MINIMUM de nodes não é esse parâmetro e foi excluída do inventário.

Uma futura padronização pode alinhar os textos de painel/operador/mensagens com Minimum Separation (mm), preservando `minimum_distance_mm`, `minimum_mm`, defaults, IDs, persistência e comportamento. Isso é proposta documental, não uma renomeação aprovada. O parâmetro não deve ser apresentado como tolerância absoluta de erro; ver [qualificação de unidades](units-1.7.9.md).
