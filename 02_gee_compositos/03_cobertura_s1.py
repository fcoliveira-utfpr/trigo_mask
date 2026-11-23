"""Cobertura do Sentinel-1 por safra no escopo (PR, RS, SC, SP, MG).

Conta as aquisições IW com VV+VH entre 1/abr e 30/nov (janela do trigo) em:
  - uma grade de 0,05° (≈ 5 km) cobrindo o escopo -> mapa;
  - os pontos das glebas de trigo aptas da amostra do piloto -> estatísticas por safra.

Saídas (dados/intermediarios/cobertura_s1/):
  grade_<ano>.npz       contagem, extensão (lon/lat)
  pontos_trigo.csv      ano, gid, n_aquisicoes
  resumo.csv            mediana, P10, fração com ≥ 10 e < 5 aquisições por safra

Uso:
  python 02_gee_compositos/03_cobertura_s1.py [--inicio 2017] [--fim 2025]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import ee
import geopandas as gpd
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
SAIDA = RAIZ / "dados" / "intermediarios" / "cobertura_s1"
EXTENSAO = (-58.0, -34.0, -39.5, -14.0)  # lon_min, lat_min, lon_max, lat_max (PR, RS, SC, SP, MG)
PASSO = 0.05


def colecao(ano: int) -> ee.ImageCollection:
    return (ee.ImageCollection("COPERNICUS/S1_GRD").filterDate(f"{ano}-04-01", f"{ano}-11-30")
            .filter(ee.Filter.eq("instrumentMode", "IW"))
            .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
            .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH")))


def grade(ano: int) -> np.ndarray:
    lon0, lat0, lon1, lat1 = EXTENSAO
    nx, ny = int(round((lon1 - lon0) / PASSO)), int(round((lat1 - lat0) / PASSO))
    img = colecao(ano).select("VH").count().unmask(0).toInt16().rename("n")
    req = {
        "expression": img,
        "fileFormat": "NUMPY_NDARRAY",
        "grid": {
            "dimensions": {"width": nx, "height": ny},
            "affineTransform": {"scaleX": PASSO, "shearX": 0, "translateX": lon0,
                                "shearY": 0, "scaleY": -PASSO, "translateY": lat1},
            "crsCode": "EPSG:4326",
        },
    }
    return ee.data.computePixels(req)["n"]


def pontos(ano: int, fc: ee.FeatureCollection) -> pd.DataFrame:
    n = colecao(ano).select("VH").count().unmask(0).rename("n")
    feats = n.sampleRegions(fc, scale=100, geometries=False).getInfo()["features"]
    return pd.DataFrame([f["properties"] for f in feats]).assign(ano=ano)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inicio", type=int, default=2017)
    ap.add_argument("--fim", type=int, default=2025)
    args = ap.parse_args()
    ee.Initialize(project="mapbiomas-brazil")
    SAIDA.mkdir(parents=True, exist_ok=True)

    a = gpd.read_parquet(RAIZ / "dados" / "intermediarios" / "series" / "2019_S1" / "amostra.parquet")
    a = a[a["classe"] == "trigo"]
    pts = a.geometry.representative_point()
    fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([p.x, p.y]), {"gid": g}) for g, p in zip(a["gid"], pts)])

    tabelas, resumo = [], []
    for ano in range(args.inicio, args.fim + 1):
        g = grade(ano)
        np.savez_compressed(SAIDA / f"grade_{ano}.npz", n=g, extensao=np.array(EXTENSAO), passo=PASSO)
        p = pontos(ano, fc)
        tabelas.append(p)
        resumo.append({"ano": ano, "mediana": p["n"].median(), "P10": p["n"].quantile(0.1),
                       "frac_ge10": (p["n"] >= 10).mean(), "frac_lt5": (p["n"] < 5).mean()})
        print(f"{ano}: mediana {p['n'].median():.0f} aquisições nas glebas de trigo; grade {g.shape}")
    pd.concat(tabelas).to_csv(SAIDA / "pontos_trigo.csv", index=False)
    pd.DataFrame(resumo).to_csv(SAIDA / "resumo.csv", index=False)


if __name__ == "__main__":
    main()
