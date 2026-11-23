"""Etapa 3 (piloto) - Séries temporais Sentinel-2 e Sentinel-1 por gleba do SICOR no GEE.

Amostra: glebas aptas do ano-safra e estrato escolhidos, com área após o buffer ≥ 1 ha,
estratificada por classe e espalhada pelos blocos de 50 km (peso inverso ao nº de glebas do bloco).

Sentinel-2 (COPERNICUS/S2_SR_HARMONIZED + GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED):
  pixel válido se cs_cdf ≥ 0,60; média por gleba das bandas B2-B8A, B11, B12 (reflectância)
  e `frac_valida` = fração de pixels válidos na gleba.
Sentinel-1 (COPERNICUS/S1_GRD, IW, VV+VH):
  máscara de borda (VV < −30 dB) e de ângulo (31°–45°); média por gleba em escala linear (eq. 12);
  registra órbita relativa, direção de passagem e ângulo médio. Sem correção de relevo no piloto
  (a comparação σ0 × γ0_flat é feita no E1).

Saídas (dados/intermediarios/series/<ano>_<estrato>/):
  amostra.parquet, s2.parquet, s1.parquet  (+ cache por lote em lotes/)

Uso:
  python 02_gee_compositos/01_series_glebas_piloto.py [--ano 2019] [--estrato S1] [--workers 6]
"""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import ee
import geopandas as gpd
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
ROTULOS = RAIZ / "dados" / "intermediarios" / "sicor" / "rotulos"
PROJETO = "mapbiomas-brazil"

TAMANHO_AMOSTRA = {"trigo": 1500, "milho_2safra": 600, "aveia": 600, "cevada": 600, "canola": 600,
                   "irrigada_inverno": 300, "outras_inverno": 300, "triticale": 300, "centeio": 300}
BANDAS_S2 = ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12"]
CS_LIMIAR = 0.60
ANG_MIN, ANG_MAX = 31.0, 45.0
BORDA_DB = -30.0
LOTE = 25
SEMENTE = 42


def amostrar(ano: int, estrato: str) -> gpd.GeoDataFrame:
    g = gpd.read_parquet(ROTULOS / f"rotulos_sicor_{ano}.parquet")
    g = g[g["apto"] & g["estrato"].eq(estrato) & (g["area_buffer_ha"] >= 1)].copy()
    g["gid"] = g["REF_BACEN"].astype(str) + "_" + g["NU_ORDEM"].astype(str)
    rng = np.random.default_rng(SEMENTE)
    partes = []
    for classe, n in TAMANHO_AMOSTRA.items():
        c = g[g["classe"] == classe]
        if len(c) <= n:
            partes.append(c)
            continue
        w = 1.0 / c.groupby("bloco_50km")["gid"].transform("size")
        idx = rng.choice(c.index, size=n, replace=False, p=(w / w.sum()).values)
        partes.append(c.loc[idx])
    a = pd.concat(partes)
    cols = ["gid", "classe", "produto", "variedade", "cod_mun", "uf_gleba", "estrato", "bloco_10km",
            "bloco_25km", "bloco_50km", "area_buffer_ha", "CD_TIPO_IRRIGACAO", "DT_INIC_PLANTIO",
            "DT_FIM_PLANTIO", "DT_INIC_COLHEITA", "DT_FIM_COLHEITA", "VL_PRODUTIV_OBTIDA", "geometry"]
    # lotes espacialmente compactos: ordenar pelos índices numéricos do bloco de 50 km (x, depois y)
    xy = a["bloco_50km"].str.split("_", expand=True).astype(int)
    a = a.assign(_bx=xy[0], _by=xy[1])
    return a.sort_values(["_bx", "_by", "gid"])[cols].reset_index(drop=True)


def fc_lote(lote: gpd.GeoDataFrame) -> ee.FeatureCollection:
    gj = json.loads(lote[["gid", "geometry"]].to_json())
    return ee.FeatureCollection([ee.Feature(f["geometry"], {"gid": f["properties"]["gid"]}) for f in gj["features"]])


def colecao_s2(regiao, inicio, fim) -> ee.ImageCollection:
    cs = ee.ImageCollection("GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED")
    s2 = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(regiao).filterDate(inicio, fim)
          .linkCollection(cs, ["cs_cdf"]))

    def prep(img):
        valido = img.select("cs_cdf").gte(CS_LIMIAR)
        refl = img.select(BANDAS_S2).divide(10000).updateMask(valido)
        return (refl.addBands(valido.rename("frac_valida"))
                .set({"data": img.date().format("YYYY-MM-dd"), "tile": img.get("MGRS_TILE")}))

    return s2.map(prep)


def colecao_s1(regiao, inicio, fim) -> ee.ImageCollection:
    s1 = (ee.ImageCollection("COPERNICUS/S1_GRD").filterBounds(regiao).filterDate(inicio, fim)
          .filter(ee.Filter.eq("instrumentMode", "IW"))
          .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
          .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH")))

    def prep(img):
        ang = img.select("angle")
        m = ang.gte(ANG_MIN).And(ang.lte(ANG_MAX)).And(img.select("VV").gte(BORDA_DB))
        lin = ee.Image(10).pow(img.select(["VV", "VH"]).divide(10)).rename(["VV_lin", "VH_lin"])
        return (lin.addBands(ang).updateMask(m)
                .set({"data": img.date().format("YYYY-MM-dd'T'HH:mm"),
                      "orbita": img.get("relativeOrbitNumber_start"),
                      "passagem": img.get("orbitProperties_pass"),
                      "plataforma": img.get("platform_number")}))

    return s1.map(prep)


def extrair(colecao: ee.ImageCollection, fc: ee.FeatureCollection, escala: int, props: list[str],
            campo_nao_nulo: str) -> pd.DataFrame:
    def por_imagem(img):
        r = img.reduceRegions(collection=fc, reducer=ee.Reducer.mean(), scale=escala, tileScale=2)
        return r.map(lambda f: f.set({p: img.get(p) for p in props}))

    res = colecao.map(por_imagem).flatten().filter(ee.Filter.notNull([campo_nao_nulo]))
    linhas = [f["properties"] for f in res.getInfo()["features"]]
    return pd.DataFrame(linhas)


def processar_lote(i: int, lote: gpd.GeoDataFrame, inicio: str, fim: str, dir_lotes: Path) -> str:
    arq_s2, arq_s1 = dir_lotes / f"s2_{i:04d}.parquet", dir_lotes / f"s1_{i:04d}.parquet"
    if arq_s2.exists() and arq_s1.exists():
        return f"lote {i}: cache"
    fc = fc_lote(lote)
    regiao = fc.geometry().bounds()
    for tentativa in range(1, 5):
        try:
            if not arq_s2.exists():
                extrair(colecao_s2(regiao, inicio, fim), fc, 10, ["data", "tile"], "B4").to_parquet(arq_s2)
            if not arq_s1.exists():
                extrair(colecao_s1(regiao, inicio, fim), fc, 10, ["data", "orbita", "passagem", "plataforma"],
                        "VH_lin").to_parquet(arq_s1)
            return f"lote {i}: ok"
        except ee.EEException as erro:
            time.sleep(20 * tentativa)
            ultimo = erro
    return f"lote {i}: FALHOU ({ultimo})"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ano", type=int, default=2019)
    ap.add_argument("--estrato", default="S1")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--max-lotes", type=int, default=None, help="para teste")
    args = ap.parse_args()

    ee.Initialize(project=PROJETO)
    saida = RAIZ / "dados" / "intermediarios" / "series" / f"{args.ano}_{args.estrato}"
    dir_lotes = saida / "lotes"
    dir_lotes.mkdir(parents=True, exist_ok=True)

    arq_amostra = saida / "amostra.parquet"
    if arq_amostra.exists():
        amostra = gpd.read_parquet(arq_amostra)
    else:
        amostra = amostrar(args.ano, args.estrato)
        amostra.to_parquet(arq_amostra)
    print(amostra["classe"].value_counts().to_string())

    inicio, fim = f"{args.ano}-03-01", f"{args.ano + 1}-01-15"
    lotes = [amostra.iloc[i:i + LOTE] for i in range(0, len(amostra), LOTE)]
    if args.max_lotes:
        lotes = lotes[: args.max_lotes]
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futuros = [ex.submit(processar_lote, i, l, inicio, fim, dir_lotes) for i, l in enumerate(lotes)]
        for n, f in enumerate(as_completed(futuros), 1):
            msg = f.result()
            if "FALHOU" in msg or n % 10 == 0 or n == len(lotes):
                print(f"[{n}/{len(lotes)} {time.time() - t0:.0f}s] {msg}", flush=True)

    for sensor in ("s2", "s1"):
        arqs = sorted(dir_lotes.glob(f"{sensor}_*.parquet"))
        df = pd.concat([pd.read_parquet(a) for a in arqs], ignore_index=True)
        df.to_parquet(saida / f"{sensor}.parquet", index=False)
        print(f"{sensor}: {len(df)} observações, {df['gid'].nunique()} glebas")


if __name__ == "__main__":
    main()
