"""Etapa (ii).1-2 - Seleção das operações de custeio de interesse e extração das glebas.

Classes (a partir da tabela Empreendimento do BCB; apenas Custeio / Agrícola / LAVOURA):
  trigo            PRODUTO = TRIGO, exceto variedade SARRACENO/MOURISCO (trigo-mourisco é outra espécie)
  trigo_silagem    PRODUTO = TRIGO SILAGEM (mantido à parte; não entra como rótulo de trigo grão)
  aveia, cevada, triticale, centeio, canola
  milho_2safra     PRODUTO = MILHO, cesta Safrinha (2ª Safra)
  sorgo_2safra     PRODUTO = SORGO, cesta Safrinha (2ª Safra)
  outras_inverno   demais produtos da cesta Safra de Inverno (3ª Safra)
  irrigada_inverno demais produtos da cesta Irrigadas, com plantio previsto entre março e julho

Ano-safra: ano da data prevista de início do plantio; na ausência, ano da emissão.
Não são mantidos campos de identificação (CNPJ da IF, cadastrante) nem valores financeiros.

Saídas (dados/intermediarios/sicor/):
  operacoes_<ano>.parquet   operações selecionadas, com atributos agronômicos
  glebas_<ano>.parquet      GeoParquet (EPSG:4674) com os polígonos das operações selecionadas

Uso:
  python 01_sicor_glebas/02_filtrar_operacoes_glebas.py [--inicio 2015] [--fim 2026]
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

RAIZ = Path(__file__).resolve().parents[1]
BRUTOS = RAIZ / "dados" / "brutos" / "sicor"
SAIDA = RAIZ / "dados" / "intermediarios" / "sicor"

COLUNAS_OPER = [
    "REF_BACEN", "NU_ORDEM", "DT_EMISSAO", "CD_ESTADO", "CD_EMPREENDIMENTO", "CD_PROGRAMA",
    "CD_SUBPROGRAMA", "CD_FONTE_RECURSO", "CD_TIPO_SEGURO", "CD_TIPO_IRRIGACAO", "CD_TIPO_AGRICULTURA",
    "CD_FASE_CICLO_PRODUCAO", "CD_TIPO_CULTIVO", "CD_TIPO_GRAO_SEMENTE", "CD_CICLO_CULTIVAR",
    "CD_TIPO_SOLO", "VL_AREA_FINANC", "VL_AREA_INFORMADA", "VL_PREV_PROD", "VL_PRODUTIV_OBTIDA",
    "DT_INIC_PLANTIO", "DT_FIM_PLANTIO", "DT_INIC_COLHEITA", "DT_FIM_COLHEITA",
]
DATAS = ["DT_EMISSAO", "DT_INIC_PLANTIO", "DT_FIM_PLANTIO", "DT_INIC_COLHEITA", "DT_FIM_COLHEITA"]
NUMEROS = ["VL_AREA_FINANC", "VL_AREA_INFORMADA", "VL_PREV_PROD", "VL_PRODUTIV_OBTIDA"]
PRODUTOS_DIRETOS = {"AVEIA": "aveia", "CEVADA": "cevada", "TRITICALE": "triticale",
                    "CENTEIO": "centeio", "CANOLA": "canola", "TRIGO SILAGEM": "trigo_silagem"}


def ler_csv_bcb(caminho: Path, **kw) -> pd.DataFrame:
    df = pd.read_csv(caminho, sep=";", encoding="latin1", dtype=str, **kw)
    df.columns = [c.lstrip("#") for c in df.columns]
    return df


def tabela_empreendimentos() -> pd.DataFrame:
    """Mapeia CD_EMPREENDIMENTO -> classe."""
    e = ler_csv_bcb(BRUTOS / "dominios" / "Empreendimento.csv")
    e = e[(e["FINALIDADE"] == "Custeio") & (e["ATIVIDADE"] == "Agrícola") & (e["MODALIDADE"] == "LAVOURA")]
    prod, var, cesta = e["PRODUTO"].str.upper(), e["VARIEDADE"].fillna("").str.upper(), e["CESTA"].fillna("")
    classe = pd.Series(pd.NA, index=e.index, dtype="object")
    classe[(prod == "TRIGO") & ~var.str.contains("SARRACENO")] = "trigo"
    for p, c in PRODUTOS_DIRETOS.items():
        classe[prod == p] = c
    classe[(prod == "MILHO") & cesta.str.startswith("Safrinha")] = "milho_2safra"
    classe[(prod == "SORGO") & cesta.str.startswith("Safrinha")] = "sorgo_2safra"
    livre = classe.isna()
    classe[livre & cesta.str.startswith("Safra de Inverno")] = "outras_inverno"
    classe[livre & (cesta == "Irrigadas")] = "irrigada_inverno"  # filtrado por data de plantio depois
    e = e.assign(classe=classe, produto=e["PRODUTO"], cesta=cesta).dropna(subset=["classe"])
    return e[["CODIGO", "classe", "produto", "VARIEDADE", "cesta", "ZONEAMENTO"]].rename(
        columns={"CODIGO": "CD_EMPREENDIMENTO", "VARIEDADE": "variedade", "ZONEAMENTO": "zoneamento"})


def filtrar_operacoes(ano: int, emp: pd.DataFrame) -> pd.DataFrame:
    op = ler_csv_bcb(BRUTOS / f"SICOR_OPERACAO_BASICA_ESTADO_{ano}.gz", usecols=lambda c: c.lstrip("#") in COLUNAS_OPER)
    op = op.merge(emp, on="CD_EMPREENDIMENTO", how="inner")
    for c in DATAS:
        op[c] = pd.to_datetime(op[c], format="%d/%m/%Y", errors="coerce")
    for c in NUMEROS:
        op[c] = pd.to_numeric(op[c], errors="coerce")
    mes = op["DT_INIC_PLANTIO"].dt.month
    op = op[(op["classe"] != "irrigada_inverno") | mes.between(3, 7)]
    op["ano_safra"] = op["DT_INIC_PLANTIO"].dt.year.fillna(op["DT_EMISSAO"].dt.year).astype("Int64")
    op["ano_arquivo"] = ano
    op = op.drop_duplicates(subset=["REF_BACEN", "NU_ORDEM"], keep="last")
    return op.reset_index(drop=True)


def extrair_glebas(ano: int, chaves: set[tuple[str, str]]) -> gpd.GeoDataFrame:
    refs = {r for r, _ in chaves}
    partes = []
    leitor = pd.read_csv(BRUTOS / f"SICOR_GLEBAS_WKT_{ano}.gz", sep=";", encoding="latin1",
                         dtype=str, chunksize=200_000)
    for bloco in leitor:
        bloco.columns = [c.lstrip("#") for c in bloco.columns]
        bloco = bloco[bloco["REF_BACEN"].isin(refs)]
        if len(bloco):
            k = list(zip(bloco["REF_BACEN"], bloco["NU_ORDEM"]))
            partes.append(bloco[[x in chaves for x in k]])
    if not partes:
        return gpd.GeoDataFrame(columns=["REF_BACEN", "NU_ORDEM", "NU_INDICE", "geometry"], crs=4674)
    g = pd.concat(partes, ignore_index=True)
    geom = shapely.force_2d(shapely.from_wkt(g["GT_GEOMETRIA"], on_invalid="ignore"))
    g = gpd.GeoDataFrame(g.drop(columns="GT_GEOMETRIA"), geometry=geom, crs=4674)
    g["geom_valida"] = g.geometry.notna() & shapely.is_valid(g.geometry.values)
    return g


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inicio", type=int, default=2015)
    ap.add_argument("--fim", type=int, default=2026)
    args = ap.parse_args()
    SAIDA.mkdir(parents=True, exist_ok=True)

    emp = tabela_empreendimentos()
    emp.to_csv(SAIDA / "empreendimentos_selecionados.csv", index=False)
    print(emp.groupby("classe").size().to_string(), "\n")

    resumo = []
    for ano in range(args.inicio, args.fim + 1):
        t0 = time.time()
        op = filtrar_operacoes(ano, emp)
        chaves = set(zip(op["REF_BACEN"], op["NU_ORDEM"]))
        gl = extrair_glebas(ano, chaves)
        com_gleba = set(zip(gl["REF_BACEN"], gl["NU_ORDEM"]))
        op["tem_gleba"] = [k in com_gleba for k in zip(op["REF_BACEN"], op["NU_ORDEM"])]
        op.to_parquet(SAIDA / f"operacoes_{ano}.parquet", index=False)
        gl.to_parquet(SAIDA / f"glebas_{ano}.parquet", index=False)

        r = op.groupby("classe").agg(n_oper=("REF_BACEN", "size"), n_com_gleba=("tem_gleba", "sum"),
                                     area_financ_ha=("VL_AREA_FINANC", "sum")).reset_index()
        r["ano_arquivo"] = ano
        resumo.append(r)
        print(f"{ano}: {len(op)} operações, {op['tem_gleba'].sum()} com gleba, "
              f"{len(gl)} polígonos ({time.time() - t0:.0f}s)")

    resumo = pd.concat(resumo, ignore_index=True)
    resumo.to_csv(SAIDA / "resumo_operacoes.csv", index=False)
    print("\nOperações de trigo por ano (arquivo):")
    print(resumo[resumo["classe"] == "trigo"].to_string(index=False))


if __name__ == "__main__":
    main()
