# trigo_mask

Mapeamento anual do trigo no Brasil (2000–2025) com glebas do SICOR e séries temporais de sensoriamento remoto. Ver [planejamento.md](planejamento.md) e o registro de decisões em [docs/decisoes.md](docs/decisoes.md).

## Ambiente

```bash
conda env create -f environment.yml --solver=libmamba
conda activate trigo
earthengine authenticate   # projeto GEE: mapbiomas-brazil
```

## Dados

Os dados não ficam no git (`dados/` está no `.gitignore`). Eles são publicados como assets em
[Releases](https://github.com/fcoliveira-utfpr/trigo_mask/releases), com uma tag por etapa:

| Tag | Conteúdo |
|---|---|
| `dados-etapa1-v1` | PAM/IBGE tabela 1612 (2000–2025, trigo, aveia, cevada, triticale, centeio), localidades e malha municipal do IBGE, saídas da Etapa 1 |
| `dados-etapa2-v1` | Glebas curadas do SICOR por ano-safra (2015–2027), operações selecionadas e resumos da curadoria |

Para reproduzir localmente, extraia os assets em `dados/` respeitando os caminhos, ou rode os scripts.

## Etapa 1: PAM e domínio de mapeamento

```bash
python 00_pam_sidra/01_download_pam.py          # SIDRA 1612 -> dados/brutos/pam/
python 00_pam_sidra/02_download_localidades.py  # IBGE -> dados/brutos/ibge/
python 00_pam_sidra/03_analise_dominio.py       # eq. 1-6 -> dados/intermediarios/pam/, docs/figuras/
```

## Etapa 2: glebas do SICOR

```bash
python 01_sicor_glebas/01_download_sicor.py            # BCB -> dados/brutos/sicor/ (~2,5 GB)
python 01_sicor_glebas/02_filtrar_operacoes_glebas.py  # classes de interesse + glebas
python 01_sicor_glebas/03_curadoria.py                 # eq. 7, buffer, município, estrato, blocos
```
