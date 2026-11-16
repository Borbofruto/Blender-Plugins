# Better Item 1.7.7 — Endpoint Python e manutenção do changelog

Entrega de manutenção em 16/11/2026, sobre o HEAD documental `e08009e00a26e059297b003f873e19ebc4ae0c58`. Mínimo preservado: **Blender 4.2.0**. Instalador estável: `addons/better_item.zip`.

## Problema, causa observada e correção

Na 1.7.6, `bpy.ops.better_item.distribute(method='ENDPOINT', distribution_mode='VOLUME')` retornava FINISHED, mas distribuía Origins. Bounds Center, Surface e até Geometry inválido também terminavam como Origins. A ordem dos kwargs não resolvia.

A reprodução foi repetida nesta sessão. Em uma cópia isolada instrumentada, o setter `placement.operator_write` recebeu o valor pedido enquanto `owner.method` ainda era OFFSET, para ambas as ordens de kwargs. O proxy gravava a escolha em `offset_placement`; quando Method passava a Endpoint, `endpoint_placement` continuava no padrão Origins. A atribuição dos argumentos do operador seguiu a ordem das propriedades RNA declaradas, não a ordem do dicionário Python, nas builds testadas.

A mudança de runtime consiste em declarar **Method antes do enum Placement que depende dele**, com um comentário explicando a dependência. Nenhum setter, solver, enum numérico, campo persistido ou migração foi reescrito. Dos 15 módulos Python, somente `__init__.py` mudou; os outros 14 são byte a byte iguais à base Git 1.7.6.

Endpoint direto agora usa o representante solicitado. Geometry é recusado pela conversão do enum RNA com TypeError, antes de executar e sem mover objetos. Não foi acrescentado Geometry Bounds ao menu Endpoint. Offset mantém os cinco Placements. Invoke continua copiando as escolhas da Scene; o operador mantém escolhas independentes para ajuste/repetição. O estado de Transform continua no Object; arranjo e Frames continuam na Scene.

## Changelog e pacote

O título do changelog foi movido para o início, antes das versões. A entrada 1.7.4 foi reconstruída pelo [relatório original](release-1.7.4.md), registrando que a descoberta/listagem de Custom Orientations foi removida na 1.7.5. Não houve reintegração. A versão atual é 1.7.7 no manifesto, sem `bl_info` duplicado.

SHA256 do ZIP definitivo: `b6e0d7cdc6bd6e55ecfab57494bb5003f934548793e00d422254340fe0fe2c1b`. O pacote contém apenas os 15 módulos e manifesto, README, CHANGELOG e LICENSE. Integridade, paridade byte a byte com `src`, AST dos módulos, versão, mínimo e checksum foram conferidos. A validação nativa de extensão e a instalação habilitada passaram nas duas builds abaixo. O arquivo `dist/SHA256SUMS` mantém o caminho relativo a `dist`.

O checkout Windows inicialmente aplicou `core.autocrlf=true`. A comparação com os blobs Git detectou CRLF antes da entrega. O texto do pacote foi normalizado para LF e a conversão desativada somente neste checkout; o ZIP foi reconstruído e a matriz completa repetida no artefato definitivo. Nenhum resultado do candidato foi reapresentado como execução desse hash final.

## Evidência nova desta sessão

Windows x64, executáveis oficiais preservados, perfis isolados, processos novos e o runner existente `tests/better_item/compatibility/`. Não foi criado outro runner de compatibilidade. Cada matriz usa o conteúdo extraído do mesmo ZIP definitivo, com `--python-exit-code 1`, logs e resultados atuais.

| Blender / build | Matriz do ZIP final | Regressões adicionais fora da matriz |
| --- | --- | --- |
| 4.2.23 LTS / `d0cbe84903e8` | **21/21** | Migração real 1.7.2→1.7.7 e persistência em novo processo: passaram |
| 5.3.0 / `02f0899d78e3` | **21/21** | Migração real 1.7.2→1.7.7 e persistência em novo processo: passaram |

São as 20 entradas existentes, incluindo API probe e instalação, mais `test_better_item_operator177.py`. A matriz existente inclui Transform, referências, sinais/hierarquias, Dimensions/GN, cache, distribuição, Live, GUI, Undo/Redo e a grade de 8.064 combinações. Os resultados estão em [results/1.7.7/matrix](../../tests/better_item/results/1.7.7/matrix/). A nova regressão tem também uma pasta própria [new-operator](../../tests/better_item/results/1.7.7/new-operator/), sem sobrescrever evidências 1.7.6.

### Nova regressão do operador

- 16 chamadas Endpoint: quatro bases válidas, duas ordens de kwargs e os dois caminhos Between Points/Reference Axis.
- Duas chamadas Geometry inválidas, com ambas as ordens: recusa e ausência de alterações.
- Dez chamadas Offset: cinco Placements e ambas as ordens, com conferência dos eixos transversais preservados.
- Tetraedro fechado deslocado da origem, com centros distintos: Bounds `(2,1,3)`, Surface `(10/9,4/9,16/9)` e Volume `(1,1/2,3/2)`, acrescidos do deslocamento conhecido. O oráculo analítico não chama o helper de Placement nem o planejador em teste.
- Conferência das posições mundiais, malha base, identidade dos dados, Scale, rotação, deltas, seleção e Active. Os kwargs diretos não sobrescrevem as escolhas da Scene.
- IDs salvos `0/1/2/3/4`, migração Geometry legado e aviso preservados.
- Invoke nativo com Volume; Undo/Redo real; novo invoke após reobter o estado; memória independente das propriedades utilizadas pelo F9; repeat-last aplicando Surface com conferência geométrica.

O ajuste programático das propriedades de F9 e repeat-last não equivale a arrastar um campo no popup com mouse. O teste GUI173 existente também foi repetido, incluindo timer real, desenho, troca de seleção, invoke e Undo/Redo. A passada humana completa permanece pendente.

### Controles negativos e desenvolvimento do teste

A regressão nova foi executada contra o **ZIP original 1.7.6**, em ambas as builds, e falhou no primeiro Bounds Center: observou Origins onde o oráculo exigia os centros geométricos. Esses resultados `passed:false` em [baseline-1.7.6](../../tests/better_item/results/1.7.7/baseline-1.7.6/) são controles negativos esperados, não falhas do pacote novo.

As primeiras iterações do teste também detectaram expectativas incorretas do próprio harness: status externo de repeat-last, estado restaurado pela repetição/Undo/Redo e esvaziamento do histórico de operadores após Undo em contexto de script. Elas foram corrigidas separando Undo/Redo do invoke e a repetição após editar propriedades, com um novo invoke antes de obter o operador. Os resumos/tracebacks permanecem em [test-development](../../tests/better_item/results/1.7.7/test-development/). Não motivaram outras mudanças no runtime. O [wrapper nativo de repeat-last na 4.2](https://github.com/blender/blender/blob/v4.2.0/source/blender/editors/screen/screen_ops.cc#L3643) retorna CANCELLED após repetir a operação interna; por isso o teste verifica o resultado geométrico, sem tratar esse status externo como a aceitação do distribuidor.

### Migração e persistência

O teste existente `test_better_item_migration173.py` gerou seu fixture usando a fonte real do commit 1.7.2 `4db16357101b08c540f4313e31434ab9ce99db2c`. Outro processo carregou o fixture com o conteúdo extraído do ZIP 1.7.7. Foram verificados Origins e aviso no antigo Endpoint/Geometry, manutenção de Geometry em Offset e distribuição pontual curta sem redimensionar.

O auxiliar novo `test_better_item_placement177_persistence.py` abriu, em outro processo, o `.blend` produzido pelo teste 173 no pacote atual: Endpoint/Volume, Offset/Geometry e ausência de sessão Live persistida foram conferidos. O auxiliar está listado no toolkit e documenta suas entradas. [Resultados, logs e comandos exatos](../../tests/better_item/results/1.7.7/migration-persistence/).

## Limites e próximas pendências

- A 4.2.0 inicial e as outras versões da [matriz 1.7.6](compatibility-1.7.6.md) não foram repetidas nesta entrega. Sua evidência continua histórica; não é execução da 1.7.7. O mínimo do manifesto permanece 4.2.0.
- Não houve certificação nova de macOS/Linux, outros patches, GPUs ou todos os arquivos/gestos possíveis.
- Falta a passada humana completa com mouse: Live, fontes, Endpoint, F9, Undo/Redo, larguras do painel e mensagens.
- A invalidação ampla do cache de inspeção permanece como estava. Os tempos do revisor externo não foram reproduzidos; esta sessão não foi benchmark de desempenho. Medir antes de otimizar ou impor limites.
- Animação continua fora do escopo. Descoberta de Custom Orientations permanece removida; exportação de Frame e GN de Dimensions permanecem suportados. Edit Mode continua estudo para futura 2.0, sem implementação nova.

Inventário e validações do artefato: [handoff-1.7.7.json](handoff-1.7.7.json). Contexto atualizado: [CONTEXTO-ATUAL.md](CONTEXTO-ATUAL.md).
