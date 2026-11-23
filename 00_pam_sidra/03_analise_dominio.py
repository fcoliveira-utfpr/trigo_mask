"""Etapa (i).3-7 - Análise exploratória da PAM e delimitação do domínio de mapeamento.

Entradas:
  dados/brutos/pam/pam_1612_municipios.parquet   (01_download_pam.py)
  dados/brutos/ibge/municipios.parquet           (02_download_localidades.py)
  dados/brutos/ibge/malha_municipios.geojson     (02_download_localidades.py)

Saídas (dados/intermediarios/pam/):
  estatisticas_municipais.parquet  F_m (eq. 1), área média, P_m (eq. 3), 1ª/última safra, domínio
  painel_trigo.parquet             município × safra: áreas, produção, Y (eq. 4), z (eq. 5), L (eq. 6)
  dominio.csv                      lista de municípios do domínio (núcleo + vizinhos)
  sensibilidade_dominio.csv        nº de municípios e retenção de área por A_min × k
  agregados_<nivel>.csv            séries por região, UF, região intermediária e estrato
  safras_estresse.csv              safras candidatas ao E7 por estrato e por UF
Figuras: docs/figuras/etapa1_*.png

Uso:
  python 00_pam_sidra/03_analise_dominio.py [--amin 50] [--kmin 2]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
BRUTOS = RAIZ / "dados" / "brutos"
SAIDA = RAIZ / "dados" / "intermediarios" / "pam"
FIG = RAIZ / "docs" / "figuras"

ANO_RECENTE = 2016          # presença "apenas recente" (expansão no Cerrado)
MIN_SAFRAS_TENDENCIA = 8    # eq. 5
LIMIAR_Z = -1.0             # safra com estresse: z médio ponderado < -1
LIMIAR_L = 0.10             # ou perda de área > 0,10
RETENCAO_MIN = 0.99
CEREAIS_EQ3 = ["trigo", "aveia", "cevada", "triticale"]


# ---------------------------------------------------------------- leitura
def carregar():
    pam = pd.read_parquet(BRUTOS / "pam" / "pam_1612_municipios.parquet")
    larga = (
        pam.pivot_table(index=["cod_mun", "ano", "produto"], columns="variavel",
                        values="valor", aggfunc="first", observed=True)
        .reset_index()
    )
    larga.columns.name = None
    mun = pd.read_parquet(BRUTOS / "ibge" / "municipios.parquet")
    malha = gpd.read_file(BRUTOS / "ibge" / "malha_municipios.geojson")
    malha["cod_mun"] = malha["codarea"].astype(int)
    return larga, mun, malha[["cod_mun", "geometry"]]


# ---------------------------------------------------------------- domínio
def presenca(trigo: pd.DataFrame, amin: float) -> pd.DataFrame:
    """Matriz município × safra com a área plantada de trigo (NaN -> 0)."""
    m = trigo.pivot_table(index="cod_mun", columns="ano", values="area_plantada_ha",
                          aggfunc="sum").fillna(0.0)
    return m


def vizinhos(malha: gpd.GeoDataFrame) -> dict[int, set[int]]:
    """Vizinhos de 1ª ordem (fronteira comum), tolerando pequenas falhas da malha."""
    g = malha.to_crs(5880)
    g["geometry"] = g.buffer(100)  # 100 m de tolerância
    pares = gpd.sjoin(g, g, predicate="intersects", how="inner")
    pares = pares[pares["cod_mun_left"] != pares["cod_mun_right"]]
    viz: dict[int, set[int]] = {}
    for a, b in zip(pares["cod_mun_left"], pares["cod_mun_right"]):
        viz.setdefault(int(a), set()).add(int(b))
    return viz


def delimitar(area: pd.DataFrame, amin: float, kmin: int, viz: dict) -> tuple[set, set]:
    n_pres = (area >= amin).sum(axis=1)
    nucleo = set(n_pres[n_pres >= kmin].index.astype(int))
    expandido = set(nucleo)
    for m in nucleo:
        expandido |= viz.get(m, set())
    return nucleo, expandido


def retencao(area: pd.DataFrame, dominio: set) -> tuple[float, float]:
    """Retenção total (todas as safras) e mínima entre safras."""
    dentro = area.index.isin(list(dominio))
    total = area.sum().sum()
    ret_total = area[dentro].sum().sum() / total
    por_ano = area[dentro].sum() / area.sum()
    return float(ret_total), float(por_ano.min())


# ---------------------------------------------------------------- rendimento e estresse
def anomalias(painel: pd.DataFrame, amin: float) -> pd.DataFrame:
    painel = painel.copy()
    painel["z"] = np.nan
    validos = painel[(painel["area_colhida_ha"] >= amin) & painel["Y_kg_ha"].notna()]
    for cod, g in validos.groupby("cod_mun"):
        if len(g) < MIN_SAFRAS_TENDENCIA:
            continue
        coef = np.polyfit(g["ano"], g["Y_kg_ha"], 1)
        res = g["Y_kg_ha"] - np.polyval(coef, g["ano"])
        s = np.sqrt((res**2).sum() / (len(g) - 2))
        if s > 0:
            painel.loc[g.index, "z"] = res / s
    return painel


def safras_estresse(painel: pd.DataFrame, nivel: str) -> pd.DataFrame:
    def agrega(g):
        zg = g.dropna(subset=["z"])
        w = zg["area_colhida_ha"]
        z_pond = np.average(zg["z"], weights=w) if w.sum() > 0 else np.nan
        ap, ac = g["area_plantada_ha"].sum(), g["area_colhida_ha"].sum()
        l_agr = 1 - ac / ap if ap > 0 else np.nan
        return pd.Series({"z_ponderado": z_pond, "L_agregado": l_agr,
                          "area_plantada_ha": ap, "n_mun_z": len(zg)})

    t = painel.groupby([nivel, "ano"]).apply(agrega, include_groups=False).reset_index()
    t["estresse"] = (t["z_ponderado"] < LIMIAR_Z) | (t["L_agregado"] > LIMIAR_L)
    return t


# ---------------------------------------------------------------- figuras
def figuras(area, conc, est, agg_uf, malha, nucleo, dominio, amin, kmin):
    FIG.mkdir(parents=True, exist_ok=True)

    # concentração (eq. 2)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(np.arange(1, len(conc) + 1), conc.values, lw=1.5)
    for q in (0.5, 0.9, 0.99):
        k = int(np.searchsorted(conc.values, q) + 1)
        ax.axhline(q, ls=":", c="0.6", lw=0.8)
        ax.annotate(f"{q:.0%}: {k} mun.", (k, q), xytext=(5, -12), textcoords="offset points", fontsize=8)
    ax.set_xscale("log")
    ax.set_xlabel("Municípios ordenados pela área média (log)")
    ax.set_ylabel("Fração acumulada da área de trigo ($C_k$)")
    ax.set_title("Concentração espacial da área de trigo, 2000–2025")
    fig.tight_layout(); fig.savefig(FIG / "etapa1_concentracao.png", dpi=150); plt.close(fig)

    # séries por UF (área plantada e rendimento)
    tops = (agg_uf.groupby("uf")["area_plantada_ha"].sum().sort_values(ascending=False).head(8).index)
    fig, axs = plt.subplots(1, 2, figsize=(11, 4))
    for uf in tops:
        s = agg_uf[agg_uf["uf"] == uf].sort_values("ano")
        axs[0].plot(s["ano"], s["area_plantada_ha"] / 1e3, label=uf)
        axs[1].plot(s["ano"], s["Y_kg_ha"], label=uf)
    axs[0].set_ylabel("Área plantada (mil ha)"); axs[1].set_ylabel("Rendimento (kg ha⁻¹)")
    for a in axs: a.set_xlabel("Safra")
    axs[0].legend(ncol=2, fontsize=8)
    fig.suptitle("Trigo por UF (PAM/IBGE)")
    fig.tight_layout(); fig.savefig(FIG / "etapa1_series_uf.png", dpi=150); plt.close(fig)

    # mapa do domínio
    m = malha.copy()
    m["classe"] = "fora"
    m.loc[m["cod_mun"].isin(list(dominio)), "classe"] = "vizinho"
    m.loc[m["cod_mun"].isin(list(nucleo)), "classe"] = "núcleo"
    cores = {"fora": "#eeeeee", "vizinho": "#9ecae1", "núcleo": "#08519c"}
    fig, ax = plt.subplots(figsize=(7, 7))
    for c, cor in cores.items():
        m[m["classe"] == c].plot(ax=ax, color=cor, linewidth=0)
    ax.set_axis_off()
    ax.set_title(f"Domínio de mapeamento: núcleo (A ≥ {amin:.0f} ha em ≥ {kmin} safras) + vizinhos")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=v, label=k) for k, v in cores.items()], loc="lower left")
    fig.tight_layout(); fig.savefig(FIG / "etapa1_dominio.png", dpi=150); plt.close(fig)

    # safras com estresse por estrato
    fig, ax = plt.subplots(figsize=(8, 3.5))
    for e, g in est.groupby("estrato"):
        ax.plot(g["ano"], g["z_ponderado"], marker="o", ms=3, label=e)
    ax.axhline(LIMIAR_Z, c="r", ls="--", lw=0.8)
    ax.set_ylabel("z ponderado (eq. 5)"); ax.set_xlabel("Safra"); ax.legend(fontsize=8)
    ax.set_title("Anomalia de rendimento do trigo por estrato")
    fig.tight_layout(); fig.savefig(FIG / "etapa1_anomalias_estrato.png", dpi=150); plt.close(fig)


# ---------------------------------------------------------------- principal
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--amin", type=float, default=50.0)
    ap.add_argument("--kmin", type=int, default=2)
    args = ap.parse_args()
    SAIDA.mkdir(parents=True, exist_ok=True)

    larga, mun, malha = carregar()
    sem_cad = set(larga["cod_mun"]) - set(mun["cod_mun"])
    print(f"Códigos da PAM sem correspondência nas localidades: {len(sem_cad)}")

    trigo = larga[larga["produto"] == "trigo"].copy()
    area = presenca(trigo, args.amin)
    N = area.shape[1]

    # eq. 1 e eq. 2
    F = (area >= args.amin).sum(axis=1) / N
    a_media = area.mean(axis=1)
    conc = a_media.sort_values(ascending=False).cumsum() / a_media.sum()

    # domínio
    viz = vizinhos(malha)
    nucleo, dominio = delimitar(area, args.amin, args.kmin, viz)
    ret_t, ret_min = retencao(area, dominio)
    ret_nuc, _ = retencao(area, nucleo)
    print(f"\nDomínio (A_min={args.amin:.0f} ha, k={args.kmin}): núcleo {len(nucleo)}, "
          f"com vizinhos {len(dominio)} municípios")
    print(f"Retenção da área de trigo: núcleo {ret_nuc:.4f}; domínio {ret_t:.4f} "
          f"(mínima entre safras {ret_min:.4f}) -> critério ≥ {RETENCAO_MIN}: "
          f"{'OK' if ret_t >= RETENCAO_MIN else 'NÃO ATENDE'}")

    # sensibilidade
    sens = []
    for amin in (10, 50, 100, 200):
        for k in (1, 2, 3, 5):
            nuc, dom = delimitar(area, amin, k, viz)
            rt, rmin = retencao(area, dom)
            sens.append({"A_min": amin, "k": k, "n_nucleo": len(nuc), "n_dominio": len(dom),
                         "retencao_total": rt, "retencao_min_safra": rmin})
    sens = pd.DataFrame(sens)
    sens.to_csv(SAIDA / "sensibilidade_dominio.csv", index=False)
    print("\nSensibilidade do domínio:\n" + sens.round(4).to_string(index=False))

    # presença recente
    pres = area >= args.amin
    primeira = pres.idxmax(axis=1).where(pres.any(axis=1))
    ultima = pres.iloc[:, ::-1].idxmax(axis=1).where(pres.any(axis=1))
    recentes = [m for m in nucleo if primeira.get(m, 0) >= ANO_RECENTE]
    print(f"Municípios do núcleo com presença apenas a partir de {ANO_RECENTE}: {len(recentes)}")

    # eq. 3: participação do trigo nos cereais de inverno
    ap_cer = (larga[larga["produto"].isin(CEREAIS_EQ3)]
              .pivot_table(index="cod_mun", columns="produto", values="area_plantada_ha",
                           aggfunc="sum", observed=True).fillna(0.0))
    tot = ap_cer[CEREAIS_EQ3].sum(axis=1)
    P = (ap_cer["trigo"] / tot).where(tot > 0)

    est_mun = pd.DataFrame({"F_m": F, "area_media_ha": a_media, "P_m": P.reindex(F.index),
                            "primeira_safra": primeira, "ultima_safra": ultima})
    est_mun.index.name = "cod_mun"
    est_mun = est_mun.reset_index().merge(mun, on="cod_mun", how="left")
    est_mun["nucleo"] = est_mun["cod_mun"].isin(list(nucleo))
    est_mun["dominio"] = est_mun["cod_mun"].isin(list(dominio))
    # vizinhos sem trigo não aparecem em `area`: acrescentá-los
    faltam = dominio - set(est_mun["cod_mun"])
    if faltam:
        extra = mun[mun["cod_mun"].isin(list(faltam))].assign(nucleo=False, dominio=True, F_m=0.0, area_media_ha=0.0)
        est_mun = pd.concat([est_mun, extra], ignore_index=True)
    est_mun.to_parquet(SAIDA / "estatisticas_municipais.parquet", index=False)
    est_mun[est_mun["dominio"]][["cod_mun", "nome_mun", "uf", "estrato", "nucleo", "F_m", "area_media_ha", "P_m"]] \
        .sort_values("area_media_ha", ascending=False).to_csv(SAIDA / "dominio.csv", index=False)

    # eq. 4-6: painel do trigo
    painel = trigo.merge(mun[["cod_mun", "uf", "regiao", "nome_rgint", "estrato"]], on="cod_mun", how="left")
    painel["Y_kg_ha"] = (1000 * painel["producao_t"] / painel["area_colhida_ha"]).where(painel["area_colhida_ha"] > 0)
    painel["L"] = (1 - painel["area_colhida_ha"] / painel["area_plantada_ha"]).where(painel["area_plantada_ha"] > 0)
    painel = anomalias(painel, args.amin)
    painel.to_parquet(SAIDA / "painel_trigo.parquet", index=False)

    # agregados
    for nivel in ("regiao", "uf", "nome_rgint", "estrato"):
        g = painel.groupby([nivel, "ano"])[["area_plantada_ha", "area_colhida_ha", "producao_t"]].sum().reset_index()
        g["Y_kg_ha"] = 1000 * g["producao_t"] / g["area_colhida_ha"]
        g["L"] = 1 - g["area_colhida_ha"] / g["area_plantada_ha"]
        if nivel == "uf":
            agg_uf = g
        g.to_csv(SAIDA / f"agregados_{nivel}.csv", index=False)

    # safras com estresse
    est_e = safras_estresse(painel, "estrato")
    est_uf = safras_estresse(painel, "uf")
    pd.concat([est_e.rename(columns={"estrato": "unidade"}).assign(nivel="estrato"),
               est_uf.rename(columns={"uf": "unidade"}).assign(nivel="uf")]) \
        .to_csv(SAIDA / "safras_estresse.csv", index=False)
    print("\nSafras com estresse por estrato (E7):")
    print(est_e[est_e["estresse"]][["estrato", "ano", "z_ponderado", "L_agregado"]].round(3).to_string(index=False))

    figuras(area, conc, est_e, agg_uf, malha, nucleo, dominio, args.amin, args.kmin)
    k50, k90, k99 = (int(np.searchsorted(conc.values, q) + 1) for q in (0.5, 0.9, 0.99))
    print(f"\nConcentração: 50% da área em {k50}, 90% em {k90}, 99% em {k99} municípios")
    print(f"Saídas em {SAIDA} e {FIG}")


if __name__ == "__main__":
    main()
