# Registro de decisões

Valores adotados para os campos [INSERIR] do `planejamento.md` e outras escolhas de execução.
Cada decisão pode ser revista; a análise de sensibilidade indicada deve acompanhar a escolha.

| Data | Etapa | Parâmetro | Valor adotado | Justificativa / sensibilidade |
|---|---|---|---|---|
| 2026-11-23 | Infra | Repositório | `trigo_mask` com a estrutura do §12.1 | Evita renomear o repositório existente |
| 2026-11-23 | Infra | Projeto GEE | `mapbiomas-brazil` | Indicado pelo responsável |
| 2026-11-23 | Infra | Armazenamento de dados | GitHub Releases do repositório (tag por etapa) | `dados/` fora do git; repo público, sem dados de beneficiários |
| 2026-11-23 | (i) | $A_{min}$ (eq. 1) | 50 ha | Sensibilidade: 10, 50, 100, 200 ha |
| 2026-11-23 | (i) | Safras mínimas com presença | 2 | Sensibilidade: 1, 2, 3, 5 |
| 2026-11-23 | (i) | Retenção mínima de área do domínio | 99% da área nacional de trigo | Critério do §12.2, passo 1 |
| 2026-11-23 | (i) | Presença recente | safras a partir de 2016 | Captura expansão no Cerrado |
| 2026-11-23 | (i) | Mínimo de safras para tendência (eq. 5) | 8 | — |
| 2026-11-23 | (i) | Limiar de perda de área $L$ (eq. 6) | 0,10 | — |
| 2026-11-23 | (iii) | Safra-piloto (Etapa 3) | 2019 (S1A + S1B, revisita 6 dias) e depois 2022 (só S1A) | Testa primeiro o caso favorável, depois o pessimista |
| 2026-11-23 | (i) | Produtos baixados da PAM | trigo, aveia, cevada, triticale, centeio | Centeio incluído além do plano (classe "outras de inverno") |

| 2026-11-23 | (i) | Nível para identificar safras com estresse (E7) | **UF** (não estrato) | No estrato, anomalias de UFs se compensam (ex.: 2023: RS z = −1,47, SC −1,57, mas S1 −0,89) |
| 2026-11-23 | Infra | Solver do conda | libmamba | O solver clássico travou (>4 h) |

## Resultados da Etapa 1 (A_min = 50 ha, k = 2)

- Núcleo: 1.202 municípios; domínio com vizinhos: 1.894. Retenção da área de trigo: 99,97% no núcleo, ~100% no domínio (mínima por safra 99,97%). Critério ≥ 99% atendido; a escolha é robusta (todas as combinações da sensibilidade retêm ≥ 99,6%).
- 130 municípios do núcleo só têm presença a partir de 2016 (expansão; mantidos pelo critério k = 2).
- Concentração: 50% da área em 109 municípios; 90% em 433; 99% em 813.
- Safras candidatas ao E7 (por UF, z < −1 ou L > 0,10), período com Sentinel (2017–2025): RS 2017, RS 2023, SC 2023, PR 2024, MS 2021, MS 2024, GO 2019, BA 2017. Período anterior: PR/RS 2006, RS 2014, RS/SC 2015, MS 2013, PR/MS/SP 2000.
- Ressalva: a perda de área $L$ da PAM é quase sempre zero (área colhida = plantada), então o indicador de estresse depende sobretudo de $z$. Valores altos de $L$ em 2000 podem ser artefato do levantamento.
- Triticale tem valores só a partir de 2005 na PAM; centeio 2025 está zerado (conferir).

## Decisões da Etapa 2 (SICOR)

| Data | Parâmetro | Valor adotado | Justificativa |
|---|---|---|---|
| 2026-11-23 | Fonte | `htms/sicor/DadosBrutos/SICOR_OPERACAO_BASICA_ESTADO_<ano>.gz` + `SICOR_GLEBAS_WKT_<ano>.gz`, junção por REF_BACEN + NU_ORDEM | Arquivos anuais públicos do BCB |
| 2026-11-23 | Anos | 2015–2026 | Glebas praticamente inexistentes antes de 2015 (2013: 17 kB) |
| 2026-11-23 | Classe trigo | PRODUTO = TRIGO, excluindo variedade SARRACENO/MOURISCO | Trigo-mourisco é outra espécie; "Duplo Propósito" mantido e identificável pela variedade |
| 2026-11-23 | Classes extras | azevém e outras culturas da cesta de inverno (`outras_inverno`); irrigadas com plantio previsto mar–jul (`irrigada_inverno`) | Azevém é confundidor não previsto no plano |
| 2026-11-23 | Ano-safra | ano da data prevista de início do plantio; se diferir mais de 1 ano do arquivo, ano do arquivo | Corrige datas digitadas com erro (ex.: ano 201) |
| 2026-11-23 | Área mínima | 2 ha | Passo 4 |
| 2026-11-23 | $R_g$ (eq. 7) | 0,7–1,3 | Reprova só 2,4% das operações de trigo |
| 2026-11-23 | Buffer negativo | −20 m, cantos em esquadria, simplificação 1 m | Compatível com o pixel de 10 m e a resolução efetiva de ~20 m do Sentinel-1 |
| 2026-11-23 | Sobreposição | conflito = ≥ 10% da menor gleba, classes de inverno diferentes, mesmo ano-safra | Passo 3 |
| 2026-11-23 | S3 × S4 | S4 = estado do Cerrado e `CD_TIPO_IRRIGACAO` irrigado (02–11); pivô (06) marcado à parte | Atributo do próprio SICOR |
| 2026-11-23 | Blocos espaciais | grades de 10, 25 e 50 km pelo ponto representativo (estáveis entre anos) | Tamanho final escolhido pelo semivariograma na Etapa 3 |
| 2026-11-23 | Release | apenas a base curada; brutos do BCB não são republicados | Brutos já públicos na fonte (2,5 GB) |

## Resultados da Etapa 2

- Operações de custeio de trigo com gleba: 9 mil (2017) → 54 mil (2023) → 23 mil (2025). Entre 2019 e 2024, 81–90% das operações de trigo têm gleba.
- **Queda de 2025–2026 é real** (todos os meses de emissão e todos os estados), não arquivo incompleto: área financiada de trigo 1,69 Mha (2023) → 0,80 Mha (2025). 2026 ainda é parcial.
- Glebas de trigo aptas (2016–2026): **S1 306.721; S2 1.039; S3 131; S4 29.** O SICOR resolve os rótulos no Sul, mas não no Cerrado.
- Confundidores no S1: milho 2ª safra 192 mil, aveia 19 mil, canola 7,7 mil, cevada 6,2 mil, triticale 654, centeio 44. Aveia preta de cobertura praticamente ausente (como previsto).
- Cobertura das glebas sobre a área da PAM (2017–2024): RS 48–64%, PR 22–34%, SC 21–32%; SP, MS, MG, GO, DF, BA < 5% (GO e BA ~0).
- Correlação município × safra entre área das glebas e área da PAM: 0,62 (municípios ≥ 500 ha). Em 10% dos municípios a área das glebas supera a da PAM.
- O arquivo de operações traz datas previstas de plantio e colheita, tipo de irrigação, tipo de cultivo, ciclo da cultivar, tipo de solo e **produtividade obtida** (`VL_PRODUTIV_OBTIDA`), útil para os modelos de produtividade.

**Consequência para o plano (recomendação adotada):** no Cerrado (S3/S4) os rótulos virão de (1) interpretação visual de pivôs da ANA com ciclo de inverno e de lavouras de sequeiro, (2) transferência a partir do S1 (E6) e (3) pontos de cooperativas e da Embrapa, se obtidos. A meta de amostras por estrato do passo 11 passa a valer também para trigo em S3 e S4.

## Verificações (§12.3)

| Item | Situação | Observação |
|---|---|---|
| PAM 2025 publicada no SIDRA | Confirmado (2026-11-23) | Tabela 1612 com período 1974–2025 |
| Disponibilidade e formato das glebas do SICOR | Confirmado | Arquivos anuais 2013–2026; WKT em SIRGAS 2000, com coordenada Z = 0 |
| Datas de plantio/colheita, irrigação e cultivo no SICOR | Confirmado | Datas são **previstas** (no contrato), não observadas |
| Datas de colheita para calibrar κ (eq. 28) | Parcial | Só a janela prevista; calibração principal pelas quedas de NDVI |
| Comunicações de perda do Proagro por operação | Pendente | |
| Earth Engine | Confirmado | Projeto `mapbiomas-brazil` inicializa |
