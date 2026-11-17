# Qualificação de unidades — Better Item 1.7.9

17/11/2026, runtime `77ce932`, ZIP `6a01eb809165347e94668d259a492b922b69f0c368657cae48599a2f57a9f029`, sem alteração do addon. [Relatório](../../../../../docs/better_item/units-1.7.9.md).

- Cada pasta de build contém as duas entradas novas: 590 cenários numéricos, seis configurações GUI, logs, screenshots e versão do executável.
- `acceptance.json` separa esses resultados da matriz anterior de 24 entradas. A suíte padrão atual tem 25, mas não foi toda repetida aqui.
- `observations.json` registra limites físicos e o achado de arredondamento visual. Testes funcionais aprovados não significam aprovação da exibição ou garantia absoluta em mm.
- `suite.json` e `workspace-inputs.json` identificam os inputs congelados. Perfis, runtime e bytecode não são publicados.
- `test-development/` preserva a falha inicial de serialização do relatório e a configuração incorreta da ordem Method/Placement na rodada intermediária. São falhas do teste, separadas da execução final.

Sem simulação de teclado ou mouse. Os registros anteriores, inclusive os da consolidação, mantêm seus hashes e contagens originais.
