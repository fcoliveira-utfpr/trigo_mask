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

## Verificações (§12.3)

| Item | Situação | Observação |
|---|---|---|
| PAM 2025 publicada no SIDRA | Confirmado (2026-11-23) | Tabela 1612 com período 1974–2025 |
