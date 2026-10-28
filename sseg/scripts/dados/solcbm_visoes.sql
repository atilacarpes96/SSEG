-- Visões do banco da Consulta SOLCBM (Sgt Magalhães, esquema 2), copiadas do solcbm.db de 17/10/2026.
-- O sol_banco.py cria estas visões sobre sol_lista, sol_bruto e sol_cia_texto e grava cada uma como tabela.
-- Só lógica de leitura do JSON do SOL: nenhum dado de processo aqui.

CREATE VIEW v_analises AS 
SELECT b.id_licenciamento,
       l.numero,
       g.key AS grupo,
       COALESCE(json_extract(a.value, '$.tipoRetornoHistorico'),
                CASE g.key WHEN 'historicoRecurso' THEN 'RECURSO' END) AS tipo,
       COALESCE(json_extract(a.value, '$.status'), json_extract(a.value, '$.statusRecurso'),
                json_extract(a.value, '$.situacao')) AS status,
       json_extract(a.value, '$.descricaoStatus') AS descricao_status,
       datetime(CAST(COALESCE(json_extract(a.value, '$.dthOperacao'), json_extract(a.value, '$.data')) AS INTEGER) / 1000, 'unixepoch', 'localtime') AS data_hora,
       json_extract(a.value, '$.ciencia') AS ciencia,
       json_extract(a.value, '$.tipoVistoria') AS tipo_vistoria,
       datetime(CAST(json_extract(a.value, '$.dataCiv') AS INTEGER) / 1000, 'unixepoch', 'localtime') AS data_civ,
       COALESCE(json_extract(a.value, '$.idArquivo'), json_extract(a.value, '$.arquivoCiaCiv.id')) AS id_arquivo,
       COALESCE(json_extract(a.value, '$.nomeDocComplementar'),
                json_extract(a.value, '$.descricaoDocComplementar')) AS documento,
       json_extract(a.value, '$.instancia') AS instancia_recurso,
       json_extract(a.value, '$.tipoRecurso') AS tipo_recurso,
       json_extract(a.value, '$.tipoSolicitacaoRecurso') AS abrangencia_recurso,
       datetime(CAST(json_extract(a.value, '$.dthEmissao') AS INTEGER) / 1000, 'unixepoch', 'localtime') AS data_emissao,
       datetime(CAST(json_extract(a.value, '$.dtValidade') AS INTEGER) / 1000, 'unixepoch', 'localtime') AS data_validade,
       json_extract(a.value, '$.validade') AS validade_anos,
       (SELECT group_concat(
                  COALESCE(json_extract(n.value, '$.parametroNcs.valor'), '')
                  || COALESCE(' — ' || json_extract(n.value, '$.justificativa'), ''), ' | ')
          FROM json_each(a.value, '$.justificativasNcs') n) AS motivos
FROM sol_bruto b JOIN sol_lista l ON l.id = b.id_licenciamento,
     json_each(b.json) g, json_each(g.value) a
WHERE b.recurso = 'historico' AND g.type = 'array';

CREATE VIEW v_areas_memorial AS 
WITH inf AS (
    SELECT id_licenciamento AS id,
           json_extract(json, '$.licenciamentoDTO') AS d,
           json AS j,
           coletado_em
    FROM sol_bruto WHERE recurso = 'informacoes'
)
SELECT inf.id AS id_licenciamento,
       l.numero,
       json_extract(x.value, '$.tpArea') AS tipo_area,
       json_extract(x.value, '$.area') AS area,
       json_extract(x.value, '$.populacao') AS populacao,
       json_extract(x.value, '$.densidade.descricao') AS densidade
FROM inf JOIN sol_lista l ON l.id = inf.id, json_each(inf.d, '$.caracteristica.areasMemorial') x;

CREATE VIEW v_boletos AS 
WITH inf AS (
    SELECT id_licenciamento AS id,
           json_extract(json, '$.licenciamentoDTO') AS d,
           json AS j,
           coletado_em
    FROM sol_bruto WHERE recurso = 'informacoes'
)
SELECT inf.id AS id_licenciamento,
       l.numero,
       json_extract(b.value, '$.tipo') AS tipo,
       json_extract(b.value, '$.boleto.situacao') AS situacao,
       json_extract(b.value, '$.boleto.valorNominal') AS valor,
       datetime(CAST(json_extract(b.value, '$.boleto.dataEmissao') AS INTEGER) / 1000, 'unixepoch', 'localtime') AS data_emissao,
       datetime(CAST(json_extract(b.value, '$.boleto.dataVencimento') AS INTEGER) / 1000, 'unixepoch', 'localtime') AS data_vencimento,
       datetime(CAST(json_extract(b.value, '$.boleto.dataPagamento') AS INTEGER) / 1000, 'unixepoch', 'localtime') AS data_pagamento,
       json_extract(b.value, '$.boleto.nomePagador') AS pagador,
       COALESCE(json_extract(b.value, '$.boleto.cnpjPagador'), json_extract(b.value, '$.boleto.cpfPagador')) AS cpf_cnpj_pagador,
       json_extract(b.value, '$.boleto.cidadePagador') AS cidade_pagador
FROM inf JOIN sol_lista l ON l.id = inf.id, json_each(inf.d, '$.boletosLicenciamento') b;

CREATE VIEW v_cias AS 
SELECT c.id_arquivo,
       c.id_licenciamento,
       l.numero,
       datetime(CAST(c.dth_marco AS INTEGER) / 1000, 'unixepoch', 'localtime') AS data_conclusao,
       (SELECT json_extract(m.value, '$.nomeResponsavel')
          FROM sol_bruto b, json_each(b.json) m
         WHERE b.id_licenciamento = c.id_licenciamento AND b.recurso = 'marcos'
           AND json_extract(m.value, '$.arquivo.id') = c.id_arquivo
           AND json_extract(m.value, '$.descricao') = 'Conclusão de análise técnica - CIA'
         LIMIT 1) AS analista,
       c.paginas,
       c.texto,
       c.erro
FROM sol_cia_texto c JOIN sol_lista l ON l.id = c.id_licenciamento;

CREATE VIEW v_elementos_graficos AS 
WITH inf AS (
    SELECT id_licenciamento AS id,
           json_extract(json, '$.licenciamentoDTO') AS d,
           json AS j,
           coletado_em
    FROM sol_bruto WHERE recurso = 'informacoes'
)
SELECT inf.id AS id_licenciamento,
       l.numero,
       json_extract(e.value, '$.tipo') AS tipo,
       json_extract(e.value, '$.descricao') AS descricao,
       json_extract(e.value, '$.situacao') AS situacao,
       json_extract(e.value, '$.codigoAnalise') AS numero_analise,
       datetime(CAST(json_extract(e.value, '$.dthInclusao') AS INTEGER) / 1000, 'unixepoch', 'localtime') AS data_inclusao,
       datetime(CAST(json_extract(e.value, '$.dthExclusao') AS INTEGER) / 1000, 'unixepoch', 'localtime') AS data_exclusao,
       json_extract(e.value, '$.arquivo.nomeArquivo') AS nome_arquivo,
       json_extract(j.value, '$.parametro') AS parametro_inconformidade,
       trim(json_extract(j.value, '$.justificativa'), ' ' || char(9) || char(10) || char(13)) AS justificativa_inconformidade
FROM inf JOIN sol_lista l ON l.id = inf.id
JOIN json_each(inf.d, '$.elemGraficos') e
LEFT JOIN json_each(e.value, '$.justificativas') j;

CREATE VIEW v_envolvidos AS 
WITH inf AS (
    SELECT id_licenciamento AS id,
           json_extract(json, '$.licenciamentoDTO') AS d,
           json AS j,
           coletado_em
    FROM sol_bruto WHERE recurso = 'informacoes'
),
pessoas AS (
    SELECT inf.id, 'RESPONSAVEL_TECNICO' AS papel, e.value AS v, NULL AS de FROM inf, json_each(inf.d, '$.envolvidos.rts') e
    UNION ALL
    SELECT inf.id, 'RESPONSAVEL_USO', e.value, NULL FROM inf, json_each(inf.d, '$.envolvidos.rus') e
    UNION ALL
    SELECT inf.id, 'PROCURADOR', json_extract(e.value, '$.procurador'), 'RESPONSAVEL_USO: ' || json_extract(e.value, '$.nome')
        FROM inf, json_each(inf.d, '$.envolvidos.rus') e WHERE json_extract(e.value, '$.procurador') IS NOT NULL
    UNION ALL
    SELECT inf.id, 'PROPRIETARIO', e.value, NULL FROM inf, json_each(inf.d, '$.envolvidos.proprietarios') e
    UNION ALL
    SELECT inf.id, 'PROCURADOR', json_extract(e.value, '$.procurador'), 'PROPRIETARIO: ' || json_extract(e.value, '$.nome')
        FROM inf, json_each(inf.d, '$.envolvidos.proprietarios') e WHERE json_extract(e.value, '$.procurador') IS NOT NULL
    UNION ALL
    SELECT inf.id, 'PROCURADOR', e.value, NULL FROM inf, json_each(inf.d, '$.envolvidos.procuradores') e
    UNION ALL
    SELECT inf.id, 'ESTABELECIMENTO', e.value, NULL FROM inf, json_each(inf.d, '$.envolvidos.estabelecimentos') e
)
SELECT p.id AS id_licenciamento,
       l.numero,
       p.papel,
       p.de AS procurador_de,
       COALESCE(json_extract(p.v, '$.nome'), json_extract(p.v, '$.razaoSocial')) AS nome,
       json_extract(p.v, '$.nomeFantasia') AS nome_fantasia,
       COALESCE(json_extract(p.v, '$.cpf'), json_extract(p.v, '$.cpfCnpj')) AS cpf_cnpj,
       json_extract(p.v, '$.email') AS email,
       json_extract(p.v, '$.telefone') AS telefone,
       COALESCE(json_extract(p.v, '$.tipo'), json_extract(p.v, '$.pessoa')) AS tipo_pessoa,
       json_extract(p.v, '$.tipoResponsabilidadeTecnica') AS tipo_responsabilidade_tecnica,
       json_extract(p.v, '$.aceitou') AS aceitou,
       json_extract(p.v, '$.aceiteVistoria') AS aceite_vistoria
FROM pessoas p JOIN sol_lista l ON l.id = p.id;

CREATE VIEW v_laudos AS 
WITH inf AS (
    SELECT id_licenciamento AS id,
           json_extract(json, '$.licenciamentoDTO') AS d,
           json AS j,
           coletado_em
    FROM sol_bruto WHERE recurso = 'informacoes'
)
SELECT inf.id AS id_licenciamento,
       l.numero,
       json_extract(x.value, '$.tpLaudo') AS tipo_laudo,
       json_extract(x.value, '$.tipoVistoria') AS tipo_vistoria,
       CASE WHEN json_extract(x.value, '$.dataInclusao') IS NULL THEN NULL ELSE substr(json_extract(x.value, '$.dataInclusao'),7,4)||'-'||substr(json_extract(x.value, '$.dataInclusao'),4,2)||'-'||substr(json_extract(x.value, '$.dataInclusao'),1,2)||CASE WHEN length(json_extract(x.value, '$.dataInclusao')) >= 18 THEN ' '||substr(json_extract(x.value, '$.dataInclusao'),14,5) ELSE '' END END AS data_inclusao,
       json_extract(x.value, '$.consolidado') AS consolidado,
       json_extract(x.value, '$.indRenovacao') AS renovacao,
       json_extract(x.value, '$.arquivo.nomeArquivo') AS nome_arquivo
FROM inf JOIN sol_lista l ON l.id = inf.id, json_each(inf.j, '$.laudos') x;

CREATE VIEW v_marcos AS 
SELECT b.id_licenciamento,
       l.numero,
       datetime(CAST(json_extract(m.value, '$.dthMarco') AS INTEGER) / 1000, 'unixepoch', 'localtime') AS data_hora,
       json_extract(m.value, '$.descricao') AS descricao,
       json_extract(m.value, '$.nomeResponsavel') AS responsavel,
       json_extract(m.value, '$.descricaoTipoResponsavel') AS tipo_responsavel,
       json_extract(m.value, '$.visibilidade') AS visibilidade,
       json_extract(m.value, '$.textoComplementar') AS complemento,
       json_extract(m.value, '$.arquivo.id') AS id_arquivo,
       json_extract(m.value, '$.arquivo.nomeArquivo') AS nome_arquivo,
       json_extract(m.value, '$.tituloArquivo') AS titulo_arquivo
FROM sol_bruto b JOIN sol_lista l ON l.id = b.id_licenciamento, json_each(b.json) m
WHERE b.recurso = 'marcos';

CREATE VIEW v_medidas AS 
WITH inf AS (
    SELECT id_licenciamento AS id,
           json_extract(json, '$.licenciamentoDTO') AS d,
           json AS j,
           coletado_em
    FROM sol_bruto WHERE recurso = 'informacoes'
)
SELECT inf.id AS id_licenciamento,
       l.numero,
       json_extract(m.value, '$.tipo.nome') AS medida,
       json_extract(m.value, '$.norma.nome') AS norma,
       json_extract(m.value, '$.compartimentacao') AS compartimentacao,
       json_extract(m.value, '$.inviabilidade') AS inviabilidade
FROM inf JOIN sol_lista l ON l.id = inf.id, json_each(inf.d, '$.especSeguranca.medidas') m;

CREATE VIEW v_ocupacoes AS 
WITH inf AS (
    SELECT id_licenciamento AS id,
           json_extract(json, '$.licenciamentoDTO') AS d,
           json AS j,
           coletado_em
    FROM sol_bruto WHERE recurso = 'informacoes'
)
SELECT inf.id AS id_licenciamento,
       l.numero,
       json_extract(o.value, '$.ocupacao') AS ocupacao,
       json_extract(o.value, '$.cnae.divisao') AS divisao,
       json_extract(o.value, '$.cnae.grupoOcupacao.codigo') AS grupo_ocupacao,
       json_extract(o.value, '$.cnae.grupoOcupacao.descricao') AS grupo_ocupacao_descricao,
       json_extract(o.value, '$.cnae.cnae') AS cnae,
       json_extract(o.value, '$.cnae.descricao') AS cnae_descricao,
       json_extract(o.value, '$.cargaIncendio') AS carga_incendio,
       json_extract(o.value, '$.grauRisco') AS grau_risco,
       json_extract(o.value, '$.determinaSeguranca') AS determina_seguranca,
       json_extract(o.value, '$.subsolo') AS subsolo,
       json_extract(o.value, '$.cnae.densidade.descricao') AS densidade
FROM inf JOIN sol_lista l ON l.id = inf.id, json_each(inf.d, '$.caracteristica.ocupacoes') o;

CREATE VIEW v_processos AS 
WITH inf AS (
    SELECT id_licenciamento AS id,
           json_extract(json, '$.licenciamentoDTO') AS d,
           json AS j,
           coletado_em
    FROM sol_bruto WHERE recurso = 'informacoes'
)
SELECT
    l.id,
    l.numero,
    l.tipo,
    l.situacao,
    l.presente_ultima_lista,
    l.situacao_alterada_em,
    json_extract(inf.d, '$.fase') AS fase,
    json_extract(inf.d, '$.passo') AS passo,
    CASE WHEN json_extract(inf.d, '$.dataCriacao') IS NULL THEN NULL ELSE substr(json_extract(inf.d, '$.dataCriacao'),7,4)||'-'||substr(json_extract(inf.d, '$.dataCriacao'),4,2)||'-'||substr(json_extract(inf.d, '$.dataCriacao'),1,2)||CASE WHEN length(json_extract(inf.d, '$.dataCriacao')) >= 18 THEN ' '||substr(json_extract(inf.d, '$.dataCriacao'),14,5) ELSE '' END END AS data_criacao,
    json_extract(inf.d, '$.isencao') AS isencao,
    json_extract(inf.d, '$.situacaoIsencao') AS situacao_isencao,
    json_extract(inf.d, '$.reserva') AS reserva,
    json_extract(inf.d, '$.bloqueadoParaRecurso') AS bloqueado_para_recurso,

    -- Endereço e localização
    json_extract(inf.d, '$.localizacao.enderecoLicenciamento.logradouro') AS logradouro,
    json_extract(inf.d, '$.localizacao.enderecoLicenciamento.numero') AS numero_endereco,
    json_extract(inf.d, '$.localizacao.complemento') AS complemento,
    json_extract(inf.d, '$.localizacao.bairro') AS bairro,
    json_extract(inf.d, '$.localizacao.cep') AS cep,
    COALESCE(json_extract(inf.d, '$.localizacao.enderecoLicenciamento.cidade'), l.cidade) AS cidade,
    json_extract(inf.d, '$.localizacao.enderecoLicenciamento.estado') AS uf,
    json_extract(inf.d, '$.localizacao.enderecoLicenciamento.nroMunicipioIBGE') AS codigo_ibge,
    json_extract(inf.d, '$.localizacao.latitudeMapa') AS latitude_mapa,
    json_extract(inf.d, '$.localizacao.longitudeMapa') AS longitude_mapa,
    json_extract(inf.d, '$.localizacao.latitudeEndereco') AS latitude_endereco,
    json_extract(inf.d, '$.localizacao.longitudeEndereco') AS longitude_endereco,
    CASE
        WHEN json_extract(inf.d, '$.localizacao.latitudeMapa') IS NOT NULL THEN
            'https://www.google.com/maps?q=' || json_extract(inf.d, '$.localizacao.latitudeMapa')
            || ',' || json_extract(inf.d, '$.localizacao.longitudeMapa')
        WHEN json_extract(inf.d, '$.localizacao.latitudeEndereco') IS NOT NULL THEN
            'https://www.google.com/maps?q=' || json_extract(inf.d, '$.localizacao.latitudeEndereco')
            || ',' || json_extract(inf.d, '$.localizacao.longitudeEndereco')
    END AS link_mapa,
    json_extract(inf.d, '$.localizacao.isolamentoRisco') AS isolamento_risco,

    -- Edificação
    json_extract(inf.d, '$.caracteristica.edificacao') AS edificacao,
    json_extract(inf.d, '$.caracteristica.periodoConstrucao') AS periodo_construcao,
    json_extract(inf.d, '$.caracteristica.regularizada') AS regularizada,
    json_extract(inf.d, '$.caracteristica.areaConstruida') AS area_construida,
    json_extract(inf.d, '$.caracteristica.areaProtegida') AS area_protegida,
    json_extract(inf.d, '$.caracteristica.areaMaiorPopulacao') AS area_maior_populacao,
    json_extract(inf.d, '$.caracteristica.areaSubsolo') AS area_subsolo,
    json_extract(inf.d, '$.caracteristica.pavimAcimaSolo') AS pavimentos_acima_solo,
    json_extract(inf.d, '$.caracteristica.pavimAbaixoSolo') AS pavimentos_abaixo_solo,
    json_extract(inf.d, '$.caracteristica.alturaAscendente') AS altura_ascendente,
    json_extract(inf.d, '$.caracteristica.alturaDescendente') AS altura_descendente,
    json_extract(inf.d, '$.caracteristica.populacaoTotal') AS populacao_total,
    json_extract(inf.d, '$.caracteristica.populacaoPavimMaior') AS populacao_pavimento_maior,
    json_extract(inf.d, '$.caracteristica.caracteristicaConstrutiva') AS caracteristica_construtiva,
    json_extract(inf.d, '$.caracteristica.depositoDescoberto') AS deposito_descoberto,
    json_extract(inf.d, '$.caracteristica.possuiAfastamento') AS possui_afastamento,
    json_extract(inf.d, '$.caracteristica.separacaoHorizontalAreas') AS separacao_horizontal_areas,
    json_extract(inf.d, '$.caracteristica.separacaoVerticalAreas') AS separacao_vertical_areas,
    json_extract(inf.d, '$.caracteristica.tempoResistenciaFogo') AS tempo_resistencia_fogo,
    json_extract(inf.d, '$.caracteristica.m3.instalacao') AS transformador_instalacao,
    json_extract(inf.d, '$.caracteristica.m3.operacao') AS transformador_operacao,
    json_extract(inf.d, '$.caracteristica.m3.capacidadeTransformado') AS transformador_capacidade,
    json_extract(inf.d, '$.caracteristica.m3.liquidoIsolante') AS transformador_liquido_isolante,
    json_extract(inf.d, '$.caracteristica.m5.unidadeArmazenadora') AS unidade_armazenadora,
    json_extract(inf.d, '$.especSeguranca.laudo.texto') AS justificativa_inviabilidade,

    -- Ocupação predominante
    (SELECT json_extract(o.value, '$.cnae.divisao') FROM json_each(inf.d, '$.caracteristica.ocupacoes') o WHERE json_extract(o.value, '$.ocupacao') = 'PREDOMINANTE' LIMIT 1) AS divisao,
    (SELECT json_extract(o.value, '$.cnae.grupoOcupacao.codigo') FROM json_each(inf.d, '$.caracteristica.ocupacoes') o WHERE json_extract(o.value, '$.ocupacao') = 'PREDOMINANTE' LIMIT 1) AS grupo_ocupacao,
    (SELECT json_extract(o.value, '$.cnae.grupoOcupacao.descricao') FROM json_each(inf.d, '$.caracteristica.ocupacoes') o WHERE json_extract(o.value, '$.ocupacao') = 'PREDOMINANTE' LIMIT 1) AS grupo_ocupacao_descricao,
    (SELECT json_extract(o.value, '$.cnae.cnae') FROM json_each(inf.d, '$.caracteristica.ocupacoes') o WHERE json_extract(o.value, '$.ocupacao') = 'PREDOMINANTE' LIMIT 1) AS cnae,
    (SELECT json_extract(o.value, '$.cnae.descricao') FROM json_each(inf.d, '$.caracteristica.ocupacoes') o WHERE json_extract(o.value, '$.ocupacao') = 'PREDOMINANTE' LIMIT 1) AS cnae_descricao,
    (SELECT json_extract(o.value, '$.cargaIncendio') FROM json_each(inf.d, '$.caracteristica.ocupacoes') o WHERE json_extract(o.value, '$.ocupacao') = 'PREDOMINANTE' LIMIT 1) AS carga_incendio,
    (SELECT json_extract(o.value, '$.grauRisco') FROM json_each(inf.d, '$.caracteristica.ocupacoes') o WHERE json_extract(o.value, '$.ocupacao') = 'PREDOMINANTE' LIMIT 1) AS grau_risco,
    json_array_length(inf.d, '$.caracteristica.ocupacoes') AS qtd_ocupacoes,
    json_array_length(inf.d, '$.especSeguranca.medidas') AS qtd_medidas,
    json_array_length(inf.d, '$.especsRiscos') AS qtd_riscos_especiais,

    -- Envolvidos (o primeiro de cada tipo; todos estão na tabela envolvidos)
    COALESCE((SELECT json_extract(e.value, '$.razaoSocial') FROM json_each(inf.d, '$.envolvidos.estabelecimentos') e LIMIT 1), l.razao_social) AS razao_social,
    (SELECT json_extract(e.value, '$.nomeFantasia') FROM json_each(inf.d, '$.envolvidos.estabelecimentos') e LIMIT 1) AS nome_fantasia,
    (SELECT json_extract(e.value, '$.cpfCnpj') FROM json_each(inf.d, '$.envolvidos.estabelecimentos') e LIMIT 1) AS cpf_cnpj_estabelecimento,
    (SELECT json_extract(e.value, '$.nome') FROM json_each(inf.d, '$.envolvidos.rts') e LIMIT 1) AS responsavel_tecnico,
    (SELECT json_extract(e.value, '$.nome') FROM json_each(inf.d, '$.envolvidos.rus') e LIMIT 1) AS responsavel_uso,
    (SELECT json_extract(e.value, '$.nome') FROM json_each(inf.d, '$.envolvidos.proprietarios') e LIMIT 1) AS proprietario,

    -- Vistoria / alvará
    json_extract(inf.j, '$.tipoVistoria') AS tipo_vistoria,
    json_extract(inf.j, '$.vistoriaDetalhe.numeroVistoria') AS numero_vistoria,
    datetime(CAST(json_extract(inf.j, '$.vistoriaDetalhe.dataSolicitacao') AS INTEGER) / 1000, 'unixepoch', 'localtime') AS data_solicitacao_vistoria,
    datetime(CAST(json_extract(inf.j, '$.vistoriaDetalhe.dthRealizacaoVistoria') AS INTEGER) / 1000, 'unixepoch', 'localtime') AS data_realizacao_vistoria,
    json_extract(inf.j, '$.vistoriaDetalhe.qtdDiasVistoria') AS dias_vistoria,
    json_extract(inf.j, '$.vistoriaDetalhe.nomeUltimoVistoriador') AS ultimo_vistoriador,
    json_extract(inf.j, '$.vistoriaDetalhe.observacoes.texto') AS observacoes_vistoria,
    json_extract(inf.j, '$.vistoriaDetalhe.indeferimentoHomolog') AS indeferimento_homologacao,

    -- Datas tiradas dos marcos
    datetime(CAST((SELECT json_extract(mm.value, '$.dthMarco') FROM sol_bruto mb, json_each(mb.json) mm WHERE mb.id_licenciamento = l.id AND mb.recurso = 'marcos' AND json_extract(mm.value, '$.descricao') = 'Encaminhamento para análise técnica' ORDER BY json_extract(mm.value, '$.dthMarco') ASC LIMIT 1) AS INTEGER) / 1000, 'unixepoch', 'localtime') AS primeiro_encaminhamento_analise,
    datetime(CAST((SELECT json_extract(mm.value, '$.dthMarco') FROM sol_bruto mb, json_each(mb.json) mm WHERE mb.id_licenciamento = l.id AND mb.recurso = 'marcos' AND json_extract(mm.value, '$.descricao') = 'Encaminhamento para análise técnica' ORDER BY json_extract(mm.value, '$.dthMarco') DESC LIMIT 1) AS INTEGER) / 1000, 'unixepoch', 'localtime') AS ultimo_encaminhamento_analise,
    (SELECT count(*) FROM sol_bruto mb, json_each(mb.json) mm WHERE mb.id_licenciamento = l.id AND mb.recurso = 'marcos' AND json_extract(mm.value, '$.descricao') = 'Encaminhamento para análise técnica') AS qtd_encaminhamentos_analise,
    (SELECT count(*) FROM sol_bruto mb, json_each(mb.json) mm WHERE mb.id_licenciamento = l.id AND mb.recurso = 'marcos' AND json_extract(mm.value, '$.descricao') = 'Conclusão de análise técnica - CIA') AS qtd_cia,
    datetime(CAST((SELECT json_extract(mm.value, '$.dthMarco') FROM sol_bruto mb, json_each(mb.json) mm WHERE mb.id_licenciamento = l.id AND mb.recurso = 'marcos' AND json_extract(mm.value, '$.descricao') = 'Conclusão de análise técnica - CA' ORDER BY json_extract(mm.value, '$.dthMarco') DESC LIMIT 1) AS INTEGER) / 1000, 'unixepoch', 'localtime') AS data_ca,
    datetime(CAST((SELECT json_extract(mm.value, '$.dthMarco') FROM sol_bruto mb, json_each(mb.json) mm WHERE mb.id_licenciamento = l.id AND mb.recurso = 'marcos' AND json_extract(mm.value, '$.descricao') LIKE 'Emissão de Alvará%' ORDER BY json_extract(mm.value, '$.dthMarco') DESC LIMIT 1) AS INTEGER) / 1000, 'unixepoch', 'localtime') AS data_emissao_appci,
    (SELECT json_extract(mm.value, '$.nomeResponsavel') FROM sol_bruto mb, json_each(mb.json) mm WHERE mb.id_licenciamento = l.id AND mb.recurso = 'marcos' AND json_extract(mm.value, '$.descricao') LIKE 'Conclusão de análise técnica%' ORDER BY json_extract(mm.value, '$.dthMarco') DESC LIMIT 1) AS ultimo_analista,
    (SELECT count(*) FROM sol_bruto mb, json_each(mb.json) mm WHERE mb.id_licenciamento = l.id AND mb.recurso = 'marcos' AND 1) AS qtd_marcos,
    datetime(CAST((SELECT json_extract(mm.value, '$.dthMarco') FROM sol_bruto mb, json_each(mb.json) mm WHERE mb.id_licenciamento = l.id AND mb.recurso = 'marcos' AND 1 ORDER BY json_extract(mm.value, '$.dthMarco') DESC LIMIT 1) AS INTEGER) / 1000, 'unixepoch', 'localtime') AS data_ultimo_marco,
    (SELECT json_extract(mm.value, '$.descricao') FROM sol_bruto mb, json_each(mb.json) mm WHERE mb.id_licenciamento = l.id AND mb.recurso = 'marcos' AND 1 ORDER BY json_extract(mm.value, '$.dthMarco') DESC LIMIT 1) AS ultimo_marco,

    inf.coletado_em
FROM sol_lista l
LEFT JOIN inf ON inf.id = l.id;

CREATE VIEW v_riscos_especiais AS 
WITH inf AS (
    SELECT id_licenciamento AS id,
           json_extract(json, '$.licenciamentoDTO') AS d,
           json AS j,
           coletado_em
    FROM sol_bruto WHERE recurso = 'informacoes'
)
SELECT inf.id AS id_licenciamento,
       l.numero,
       json_extract(r.value, '$.risco.tipo') AS tipo,
       json_extract(r.value, '$.risco.descricao') AS descricao,
       json_extract(r.value, '$.recipiente') AS recipiente,
       json_extract(r.value, '$.centralGlp') AS central_glp,
       json_extract(r.value, '$.capacidade') AS capacidade,
       json_extract(r.value, '$.classe') AS classe,
       json_extract(r.value, '$.volume') AS volume,
       json_extract(r.value, '$.inviabilidade') AS inviabilidade,
       json_extract(r.value, '$.outros') AS outros
FROM inf JOIN sol_lista l ON l.id = inf.id, json_each(inf.d, '$.especsRiscos') r;

