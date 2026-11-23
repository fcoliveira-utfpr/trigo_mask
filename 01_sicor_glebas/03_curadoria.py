"""Etapa (ii).3-10 - Curadoria das glebas do SICOR.

Para cada operação selecionada (02_filtrar_operacoes_glebas.py):
  - une os polígonos da operação (NU_INDICE) e corrige geometrias inválidas (make_valid);
  - calcula a área do polígono em projeção de área igual (Albers/IBGE) e R_g (eq. 7);
  - atribui município (centroide), UF, estrato e domínio (Etapa 1); separa S3/S4 pela irrigação;
  - marca duplicatas exatas e sobreposições entre produtos de inverno do mesmo ano-safra;
  - aplica o buffer negativo e registra a área remanescente;
  - atribui blocos espaciais (grades de 10, 25 e 50 km), estáveis entre anos.
Os filtros não removem registros: cada critério vira uma coluna booleana e `apto` combina todos.
O filtro de coerência temporal (eq. 8) é aplicado na Etapa 3 (séries no GEE).

Saídas (dados/intermediarios/sicor/):
  rotulos/rotulos_sicor_<ano>.parquet  GeoParquet (EPSG:4674) por ano-safra, geometria após o buffer negativo
  resumo_curadoria.csv             nº e área por classe × estrato × ano-safra × critério
  representatividade_municipal.csv área de glebas aptas de trigo × área plantada da PAM

Uso:
  python 01_sicor_glebas/03_curadoria.py [--inicio 2015] [--fim 2026]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

RAIZ = Path(__file__).resolve().parents[1]
SICOR = RAIZ / "dados" / "intermediarios" / "sicor"
PAM = RAIZ / "dados" / "intermediarios" / "pam"
IBGE = RAIZ / "dados" / "brutos" / "ibge"

ALBERS = "+proj=aea +lat_0=-12 +lon_0=-54 +lat_1=-2 +lat_2=-22 +x_0=5000000 +y_0=10000000 +ellps=GRS80 +units=m +no_defs"
AREA_MIN_HA = 2.0          # passo 4
R_MIN, R_MAX = 0.7, 1.3    # eq. 7
BUFFER_M = -20.0           # passo 6
SIMPLIFICA_M = 1.0
SOBREP_MIN = 0.10          # fração da menor gleba para considerar sobreposição
IRRIGADO = {"02", "03", "04", "05", "06", "07", "08", "09", "10", "11"}
INVERNO = {"trigo", "trigo_silagem", "aveia", "cevada", "triticale", "centeio", "canola",
           "outras_inverno", "irrigada_inverno"}
BLOCOS_KM = (10, 25, 50)


def carregar_ano(ano: int) -> gpd.GeoDataFrame:
    op = pd.read_parquet(SICOR / f"operacoes_{ano}.parquet")
    gl = gpd.read_parquet(SICOR / f"glebas_{ano}.parquet")
    gl = gl[gl.geometry.notna()].copy()
    gl["geometry"] = shapely.make_valid(gl.geometry.values)
    gl["geometry"] = gl.geometry.apply(
        lambda g: shapely.union_all([p for p in getattr(g, "geoms", [g]) if p.geom_type in ("Polygon", "MultiPolygon")])
        if g.geom_type == "GeometryCollection" else g)
    gl = gl[~gl.geometry.is_empty]
    por_op = gl.dissolve(by=["REF_BACEN", "NU_ORDEM"], aggfunc={"NU_INDICE": "count", "geom_valida": "all"})
    por_op = por_op.rename(columns={"NU_INDICE": "n_poligonos", "geom_valida": "geom_valida_original"}).reset_index()
    g = por_op.merge(op, on=["REF_BACEN", "NU_ORDEM"], how="inner")
    # datas de plantio com erro de digitação (ex.: ano 201): usar o ano do arquivo
    fora = (g["ano_safra"] - ano).abs() > 1
    g["ano_safra_corrigido"] = fora
    g.loc[fora, "ano_safra"] = ano
    return g


def municipios() -> tuple[gpd.GeoDataFrame, set[int]]:
    malha = gpd.read_file(IBGE / "malha_municipios.geojson")
    malha["cod_mun"] = malha["codarea"].astype(int)
    mun = pd.read_parquet(IBGE / "municipios.parquet")
    malha = malha[["cod_mun", "geometry"]].merge(mun[["cod_mun", "uf", "estrato"]], on="cod_mun")
    dominio = set(pd.read_csv(PAM / "dominio.csv")["cod_mun"])
    return malha, dominio


def sobreposicoes(g: gpd.GeoDataFrame) -> pd.Series:
    """Marca glebas de inverno com sobreposição (≥ SOBREP_MIN da menor) com outra de classe diferente."""
    inv = g[g["classe"].isin(INVERNO)][["uid", "classe", "ano_safra", "geometry"]]
    pares = gpd.sjoin(inv, inv, predicate="intersects", how="inner")
    pares = pares[(pares["uid_left"] < pares["uid_right"]) & (pares["ano_safra_left"] == pares["ano_safra_right"])]
    if pares.empty:
        return pd.Series(False, index=g.index)
    geo = inv.set_index("uid").geometry
    a, b = geo.loc[pares["uid_left"]].values, geo.loc[pares["uid_right"]].values
    frac = shapely.area(shapely.intersection(a, b)) / np.minimum(shapely.area(a), shapely.area(b))
    pares = pares.assign(frac=frac)
    conflito = pares[(pares["frac"] >= SOBREP_MIN) & (pares["classe_left"] != pares["classe_right"])]
    marcados = set(conflito["uid_left"]) | set(conflito["uid_right"])
    return g["uid"].isin(marcados)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inicio", type=int, default=2015)
    ap.add_argument("--fim", type=int, default=2026)
    args = ap.parse_args()

    malha, dominio = municipios()
    malha_a = malha.to_crs(ALBERS)
    partes = []
    for ano in range(args.inicio, args.fim + 1):
        if not (SICOR / f"glebas_{ano}.parquet").exists():
            continue
        g = carregar_ano(ano).to_crs(ALBERS)
        print(f"{ano}: {len(g)} operações com gleba")
        partes.append(g)
    g = gpd.GeoDataFrame(pd.concat(partes, ignore_index=True), crs=ALBERS)
    # a mesma operação pode aparecer em arquivos de anos diferentes: manter a mais recente
    g = g.sort_values("ano_arquivo").drop_duplicates(["REF_BACEN", "NU_ORDEM"], keep="last").reset_index(drop=True)
    g["uid"] = np.arange(len(g))

    # área e eq. 7
    g["area_pol_ha"] = g.geometry.area / 1e4
    g["R_g"] = g["VL_AREA_FINANC"] / g["area_pol_ha"]

    # município, estrato, domínio
    cent = gpd.GeoDataFrame(g[["uid"]], geometry=g.geometry.representative_point(), crs=ALBERS)
    j = gpd.sjoin(cent, malha_a, predicate="within", how="left").drop_duplicates("uid").set_index("uid")
    g["cod_mun"] = g["uid"].map(j["cod_mun"]).astype("Int64")
    g["uf_gleba"] = g["uid"].map(j["uf"])
    g["estrato"] = g["uid"].map(j["estrato"])
    irrig = g["CD_TIPO_IRRIGACAO"].isin(IRRIGADO)
    g.loc[g["estrato"].eq("S3_S4") & irrig, "estrato"] = "S4"
    g.loc[g["estrato"].eq("S3_S4") & ~irrig, "estrato"] = "S3"
    g["irrigado"] = irrig
    g["pivo"] = g["CD_TIPO_IRRIGACAO"].eq("06")
    g["no_dominio"] = g["cod_mun"].isin(list(dominio))
    g["uf_coerente"] = g["uf_gleba"].eq(g["CD_ESTADO"])

    # duplicatas exatas (mesma geometria, mesma classe e ano-safra)
    wkb = shapely.to_wkb(shapely.normalize(g.geometry.values))
    g["dup_exata"] = pd.Series(list(zip(wkb, g["classe"], g["ano_safra"]))).duplicated(keep="first").values
    g["sobreposicao_conflito"] = sobreposicoes(g)

    # buffer negativo
    # cantos em esquadria e simplificação de 1 m (bem abaixo do pixel de 10 m) evitam
    # a explosão de vértices do buffer arredondado
    g["geometry"] = g.geometry.buffer(BUFFER_M, join_style="mitre").simplify(SIMPLIFICA_M)
    g["area_buffer_ha"] = g.geometry.area / 1e4

    # blocos espaciais (pelo ponto representativo, estáveis entre anos)
    for km in BLOCOS_KM:
        x = (cent.geometry.x // (km * 1000)).astype(int)
        y = (cent.geometry.y // (km * 1000)).astype(int)
        g[f"bloco_{km}km"] = x.astype(str) + "_" + y.astype(str)

    # critérios
    g["ok_area"] = g["area_pol_ha"] >= AREA_MIN_HA
    g["ok_Rg"] = g["R_g"].between(R_MIN, R_MAX)
    g["ok_buffer"] = g["area_buffer_ha"] > 0
    g["apto"] = (g["ok_area"] & g["ok_Rg"] & g["ok_buffer"] & ~g["dup_exata"]
                 & ~g["sobreposicao_conflito"] & g["no_dominio"])

    criterios = ["ok_area", "ok_Rg", "ok_buffer", "dup_exata", "sobreposicao_conflito", "no_dominio", "apto"]
    resumo = (g.groupby(["classe", "estrato", "ano_safra"], dropna=False)
              .agg(n=("uid", "size"), area_financ_ha=("VL_AREA_FINANC", "sum"),
                   **{c: (c, "sum") for c in criterios},
                   area_apta_ha=("area_pol_ha", lambda s: s[g.loc[s.index, "apto"]].sum()))
              .reset_index())
    resumo.to_csv(SICOR / "resumo_curadoria.csv", index=False)

    # representatividade: glebas aptas de trigo × PAM, por município e ano
    painel = pd.read_parquet(PAM / "painel_trigo.parquet")[["cod_mun", "ano", "area_plantada_ha"]]
    rep = (g[g["apto"] & g["classe"].eq("trigo")]
           .groupby(["cod_mun", "ano_safra"])["area_pol_ha"].sum().reset_index()
           .rename(columns={"ano_safra": "ano", "area_pol_ha": "area_glebas_ha"}))
    rep["cod_mun"] = rep["cod_mun"].astype(int)
    rep["ano"] = rep["ano"].astype(int)
    rep = painel.merge(rep, on=["cod_mun", "ano"], how="outer").fillna({"area_glebas_ha": 0})
    rep["fracao_coberta"] = rep["area_glebas_ha"] / rep["area_plantada_ha"]
    rep[rep["ano"] >= args.inicio].to_csv(SICOR / "representatividade_municipal.csv", index=False)

    g = g.drop(columns=["uid"]).to_crs(4674)
    for c in ("cod_mun",):
        g[c] = g[c].astype("Int64")
    destino = SICOR / "rotulos"
    destino.mkdir(exist_ok=True)
    for ano, parte in g.groupby("ano_safra"):
        parte.to_parquet(destino / f"rotulos_sicor_{int(ano)}.parquet", index=False)
    (SICOR / "rotulos_sicor.parquet").unlink(missing_ok=True)

    tr = g[g["classe"] == "trigo"]
    print(f"\nTrigo: {len(tr)} operações com gleba; fora do domínio: {(~tr['no_dominio']).mean():.2%}; "
          f"aptas: {tr['apto'].sum()} ({tr['apto'].mean():.1%})")
    print("Perdas por critério (trigo, fração das operações):")
    for c in ["ok_area", "ok_Rg", "ok_buffer"]:
        print(f"  reprovadas em {c}: {(~tr[c]).mean():.1%}")
    for c in ["dup_exata", "sobreposicao_conflito"]:
        print(f"  {c}: {tr[c].mean():.1%}")
    print("\nGlebas aptas por classe e estrato (todas as safras):")
    print(pd.crosstab(g.loc[g["apto"], "classe"], g.loc[g["apto"], "estrato"], margins=True).to_string())
    print("\nGlebas aptas de trigo por ano-safra e estrato:")
    print(pd.crosstab(tr.loc[tr["apto"], "ano_safra"], tr.loc[tr["apto"], "estrato"], margins=True).to_string())


if __name__ == "__main__":
    main()
