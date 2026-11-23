# Figuras de resultados

Geradas por `gerar_figuras.py` a partir dos resultados salvos em `dados/intermediarios/`. Rodar de novo a cada etapa concluída:

```bash
python 09_figuras/gerar_figuras.py           # todas
python 09_figuras/gerar_figuras.py fig09     # só uma (pelo prefixo)
```

Escopo geográfico: **PR, RS, SC, SP e MG = 97,5% da área de trigo em 2021–2025** (decisão em `docs/decisoes.md`).

| Figura | O que mostra | Para que serve |
|---|---|---|
| `fig01_fluxograma_metodo` | Dados → etapas (i)–(x) → resultados, com a situação de cada etapa | Visão geral do método |
| `fig02_mapa_area_trigo_municipios` | Área média municipal 2021–2025, Brasil e escopo, com a participação de cada UF | Justificativa do escopo |
| `fig03_pareto_area_uf` | Participação por UF e acumulada (2021–2025) | Justificativa do escopo: 5 UFs = 97,5% |
| `fig04_series_area_uf` | Área por UF 2000–2025; expansão de SP e MG | Justificativa da inclusão de SP e MG |
| `fig05_mapa_expansao_trigo` | Variação da área municipal (2021–25 menos 2010–14) | Onde a cultura cresce ou recua |
| `fig06_mapa_dominio_escopo` | Domínio de mapeamento (núcleo + vizinhos) no escopo | Etapa (i) |
| `fig07_glebas_sicor_cobertura` | Glebas de trigo aptas por ano e UF; área das glebas / PAM por UF e ano | Etapa (ii): rótulos concentrados no Sul |
| `fig08_mapa_cobertura_sicor` | Cobertura municipal dos rótulos do SICOR (2017–2024) | Etapa (ii): falta de rótulos em SP e MG |
| `fig09_curvas_classe_<ano>` | Assinaturas medianas por classe (óptico e radar) | Etapas (iii–iv) |
| `fig10_heatmap_jm_<ano>` | J-M trigo × classe por fase (óptico, radar, ambos) | Etapa (v), H2 |
| `fig11_rf_fases_map_<ano>` | F1 por fase isolada e acumulação progressiva (MAP) | Etapa (vi), E1, E2 |
| `fig12_matriz_confusao_<ano>` | Matriz de confusão do RF por gleba | E9 (cevada, aveia) |
| `fig13_cobertura_sentinel1` | Aquisições Sentinel-1 por safra (mapas e mediana nas glebas) | Lacuna de 2022–2024 |
| `fig14_transferencia_temporal` | F1 dentro da safra × treino nas demais safras (emergência × calendário) | E5, H3 |
| `fig15_validacao_datas_fenologicas` | Emergência e colheita detectadas × datas previstas no SICOR | Etapa (ix) |

Paleta validada para daltonismo (validador CVD); cores fixas por entidade: PR azul, RS laranja, SC verde-água, SP amarelo, MG magenta, demais UFs cinza; trigo sempre azul. Sequencial em azul; divergente vermelho ↔ cinza ↔ azul.
