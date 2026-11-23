"""Etapa 4 (v) - Separabilidade de Jeffries-Matusita (eq. 19-20) entre o trigo e cada classe, por fase.

Fases em dias após a emergência (DAE), estrato S1 (calibradas no piloto 2019: pico ~50 DAE,
maturação ~105 DAE, colheita pelo radar ~138 DAE):
  estabelecimento 0-20, perfilhamento 20-40, alongamento 40-55, espigamento 55-75,
  enchimento 75-95, maturação 95-125
Dois alinhamentos:
  emergencia  janelas a partir da emergência detectada em cada gleba (eq. 26-27)
  calendario  mesmas janelas a partir da emergência mediana do trigo no estrato/ano (data fixa)
Valores por fase: média da série regular suavizada (óptico) e média linear das aquisições (radar, eq. 12).
Trigo: apenas glebas coerentes (eq. 8). Demais classes: todas as glebas com emergência detectada.

Saídas:
  dados/intermediarios/separabilidade/jm_<ano>_<estrato>.csv
  docs/figuras/etapa4_jm_<ano>_<estrato>.png

Uso:
  python 03_separabilidade/01_jm_por_fase.py [--ano 2019] [--estrato S1]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
FIG = RAIZ / "docs" / "figuras"

FASES = {"estabelecimento": (0, 20), "perfilhamento": (20, 40), "alongamento": (40, 55),
         "espigamento": (55, 75), "enchimento": (75, 95), "maturacao": (95, 125)}
OPTICO = ["NDVI", "NDPI", "PSRI", "LSWI", "NDRE"]
RADAR = ["VV", "VH", "Rpol"]
GRUPOS = {"optico": OPTICO, "radar": RADAR, "optico+radar": OPTICO + RADAR,
          **{v: [v] for v in OPTICO + RADAR + ["EVI", "RVI"]}}
CLASSES = ["aveia", "cevada", "canola", "milho_2safra", "irrigada_inverno", "outras_inverno", "triticale"]
N_MIN = 30


def jm(a: np.ndarray, b: np.ndarray) -> float:
    """Eq. 19-20, com pequena regularização da covariância."""
    if len(a) < N_MIN or len(b) < N_MIN:
        return np.nan
    m1, m2 = a.mean(0), b.mean(0)
    k = a.shape[1]
    s1 = np.atleast_2d(np.cov(a, rowvar=False)) + 1e-6 * np.eye(k)
    s2 = np.atleast_2d(np.cov(b, rowvar=False)) + 1e-6 * np.eye(k)
    s = (s1 + s2) / 2
    d = m1 - m2
    _, ld = np.linalg.slogdet(s)
    _, ld1 = np.linalg.slogdet(s1)
    _, ld2 = np.linalg.slogdet(s2)
    bh = d @ np.linalg.solve(s, d) / 8 + 0.5 * (ld - 0.5 * (ld1 + ld2))
    return float(2 * (1 - np.exp(-bh)))


def compositos(m: pd.DataFrame, reg: pd.DataFrame, s1: pd.DataFrame, t0: pd.Series) -> pd.DataFrame:
    """Valor médio de cada variável em cada fase, por gleba, a partir da data t0 (por gleba)."""
    reg = reg.merge(t0.rename("t0"), left_on="gid", right_index=True)
    s1 = s1.merge(t0.rename("t0"), left_on="gid", right_index=True)
    reg["dae"] = (reg["data"] - reg["t0"]).dt.days
    s1["dae"] = (s1["data"] - s1["t0"]).dt.days
    partes = []
    for fase, (a, b) in FASES.items():
        o = reg[(reg["dae"] >= a) & (reg["dae"] < b)].groupby("gid")[OPTICO + ["EVI"]].mean()
        r = s1[(s1["dae"] >= a) & (s1["dae"] < b)].groupby("gid")[["VV_lin", "VH_lin"]].mean()
        r["VV"], r["VH"] = 10 * np.log10(r["VV_lin"]), 10 * np.log10(r["VH_lin"])
        r["Rpol"] = r["VH"] - r["VV"]
        r["RVI"] = 4 * r["VH_lin"] / (r["VV_lin"] + r["VH_lin"])
        partes.append(o.join(r[RADAR + ["RVI"]], how="outer").assign(fase=fase))
    comp = pd.concat(partes).reset_index()
    return comp.merge(m[["gid", "classe", "coerente"]], on="gid")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ano", type=int, default=2019)
    ap.add_argument("--estrato", default="S1")
    args = ap.parse_args()
    d = RAIZ / "dados" / "intermediarios" / "series" / f"{args.ano}_{args.estrato}"
    saida = RAIZ / "dados" / "intermediarios" / "separabilidade"
    saida.mkdir(parents=True, exist_ok=True)

    m = pd.read_parquet(d / "metricas_glebas.parquet")
    m = m[m["t_emergencia"].notna() & ((m["classe"] != "trigo") | m["coerente"])]
    reg = pd.read_parquet(d / "series_regulares_s2.parquet")
    s1 = pd.read_parquet(d / "s1_preparado.parquet")

    t_emerg = m.set_index("gid")["t_emergencia"]
    t_cal = m.loc[m["classe"] == "trigo", "t_emergencia"].median()
    print(f"Emergência mediana do trigo (calendário): {t_cal.date()}")
    alinhamentos = {"emergencia": t_emerg, "calendario": pd.Series(t_cal, index=t_emerg.index)}

    linhas = []
    for nome, t0 in alinhamentos.items():
        comp = compositos(m, reg, s1, t0)
        for fase in FASES:
            cf = comp[comp["fase"] == fase]
            tr = cf[cf["classe"] == "trigo"]
            for classe in CLASSES:
                oc = cf[cf["classe"] == classe]
                for grupo, vs in GRUPOS.items():
                    a, b = tr[vs].dropna().values, oc[vs].dropna().values
                    linhas.append({"alinhamento": nome, "fase": fase, "classe": classe, "grupo": grupo,
                                   "JM": jm(a, b), "n_trigo": len(a), "n_classe": len(b)})
    res = pd.DataFrame(linhas)
    res.to_csv(saida / f"jm_{args.ano}_{args.estrato}.csv", index=False)

    # tabela resumo e figura
    ordem = list(FASES)
    for grupo in ("optico", "radar", "optico+radar"):
        t = res[(res["grupo"] == grupo) & (res["alinhamento"] == "emergencia")] \
            .pivot(index="classe", columns="fase", values="JM")[ordem]
        print(f"\nJ-M trigo × classe, {grupo}, alinhado à emergência:\n{t.round(2).to_string()}")
    comp_al = res[res["grupo"] == "optico+radar"].groupby("alinhamento")["JM"].mean()
    print(f"\nJ-M médio (óptico+radar): {comp_al.round(3).to_dict()}")
    best = (res[(res["alinhamento"] == "emergencia") & res["grupo"].isin(OPTICO + RADAR + ["EVI", "RVI"])]
            .sort_values("JM", ascending=False).groupby("classe").head(3))
    print("\nMelhores variáveis isoladas por classe (fase):")
    print(best[["classe", "grupo", "fase", "JM"]].round(2).to_string(index=False))

    FIG.mkdir(parents=True, exist_ok=True)
    fig, axs = plt.subplots(2, 3, figsize=(15, 7), sharey=True)
    for i, al in enumerate(("emergencia", "calendario")):
        for j, grupo in enumerate(("optico", "radar", "optico+radar")):
            t = res[(res["grupo"] == grupo) & (res["alinhamento"] == al)].pivot(index="classe", columns="fase", values="JM")[ordem]
            ax = axs[i, j]
            im = ax.imshow(t.values, vmin=0, vmax=2, cmap="viridis", aspect="auto")
            for (r, c), v in np.ndenumerate(t.values):
                if np.isfinite(v):
                    ax.text(c, r, f"{v:.2f}", ha="center", va="center", fontsize=7, color="w" if v < 1.4 else "k")
            ax.set_xticks(range(len(ordem)), ordem, rotation=35, ha="right", fontsize=8)
            ax.set_yticks(range(len(t.index)), t.index, fontsize=8)
            ax.set_title(f"{grupo} | {al}", fontsize=9)
    fig.colorbar(im, ax=axs, shrink=0.6, label="J-M (0–2)")
    fig.suptitle(f"Separabilidade trigo × classe por fase, safra {args.ano}, {args.estrato}")
    fig.savefig(FIG / f"etapa4_jm_{args.ano}_{args.estrato}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
