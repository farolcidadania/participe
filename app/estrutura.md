# Estrutua de projeto social / clone API


## apps

- integrations: model CamaraToken, clients HTTP reutilizáveis, lógica de rotação do token.

- ingest: ProposicaoRaw (JSONField) + management commands para buscar a API e salvar o raw; logs de importação.

- legis: Modelos normalizados (Proposicao, Autor, TipoProposicao, Situacao) usados pela aplicação.

- social: Comentario, Curtida, endpoints de criação e listagem (com permissões).
