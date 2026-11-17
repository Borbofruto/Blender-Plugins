# Better Item 1.7.10 — validação de runtime

**1.7.10 oficial. A matriz abaixo qualifica o runtime no ZIP 53ea12de…; o pacote final altera apenas CHANGELOG.md e tem validação de instalação separada em package-final/. Checklist manual não executado.** Veja [qualification.json](qualification.json) e o [relatório](../../../../docs/better_item/release-1.7.10.md).

Cada pasta matrix/BUILD contém um summary legível e runner-records.zip com o summary original completo, todos os resultados JSON, logs e identificação da build. Os bytes originais foram verificados após compactação; hashes dos membros e do ZIP estão no summary legível. Extraia com qualquer leitor ZIP. Os três testes novos também têm seus JSONs diretamente disponíveis. Essa publicação evita centenas de arquivos de logs expansivos e duplicação inline, preservando o registro integral. Os resultados de 1.7.9 permanecem históricos e não foram renomeados.

Capturas publicadas: as oito imagens das comparações GUI frias e duas representativas de sincronização (4.2.0/5.3.0). As demais imagens repetitivas permanecem no workspace original do D, com SHA256 e published=false no índice; não afirmar que todas as imagens estão no Git. Logs, resultados e scripts completos permanecem publicados nos arquivos ZIP, inclusive nas tentativas anteriores.

before-controls registra falhas esperadas contra o ZIP 1.7.9 e a tentativa inválida de reutilizar uma janela já fechada sem addon. Ambos os controles de janela deram TypeError, sem repetir o crash nativo antigo; não declarar a causa do crash isolada. development preserva a primeira tentativa (erro de pertencimento na coleção RNA e simulador de layout incompleto) e a rodada dirigida posterior; não são matrizes completas nem qualificam o ZIP final. O runtime passou o cenário corrigido que fecha a janela uma única vez, com erro injetado e timer real.

Arquivos de cena, perfis, runtime e downloads ficam fora do Git. O workspace original completo permanece no D. Essa qualificação não certifica digitação/arrasto humanos, outras plataformas nem erro físico absoluto em mm.
