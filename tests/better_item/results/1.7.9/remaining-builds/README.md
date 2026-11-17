# Matriz complementar do ZIP estável 1.7.9

Seis execuções novas de 25 entradas: 4.3.2, 4.4.3, 4.5.16, 5.0.1, 5.1.2 e 5.2.4, Windows x64, mesmo ZIP 6a01eb80… . [Aceitação](acceptance.json). Perfis e portáteis no D:, checksums oficiais conferidos; o arquivo oficial de checksum foi reutilizado quando já estava em cache e isso consta na verificação.

Os registros anteriores de 24 entradas em três builds e os do ZIP antigo c053f366… não foram renomeados nem contabilizados como execuções novas. A proposta visual usa outro candidato e está fora desta matriz.

Para reduzir duplicação, summary.json é um índice compacto: cada result aponta ao JSON individual original em conteúdo, normalizado para LF, com SHA256. `_storage` registra os hashes do summary original e de sua versão LF. A reconstrução foi verificada: substituir as referências pelo conteúdo dos JSONs e serializar com json.dumps(indent=2) reproduz o summary original normalizado; restaurar CRLF quando indicado recupera o original. O summary bruto permanece no workspace D:. Não foram removidos dados individuais ou alterados valores para compactar. Logs preservados; perfis, runtime e .blend não publicados.
