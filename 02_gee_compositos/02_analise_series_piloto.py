"""Etapa 3 (piloto) - Análise das séries por gleba: índices, coerência temporal, assinaturas por classe.

Entradas: dados/intermediarios/series/<ano>_<estrato>/{amostra,s2,s1}.parquet

Passos:
  1. Índices S2: NDVI, EVI, NDPI (eq. 13, α = 0,74), PSRI (eq. 14), LSWI (eq. 15), NDRE.
     Observação válida: frac_valida ≥ 0,8; datas repetidas (tiles sobrepostos) são agregadas.
  2. Série de 10 dias (mediana no intervalo), interpolação linear e Savitzky–Golay (janela 5, ordem 2).
  3. Coerência temporal (eq. 8): ΔNDVI ≥ 0,30 e |t_pico − t_ref| ≤ 30 dias, com
     t_ref = meio da janela de plantio prevista (SICOR) + 65 dias.
     Glebas com < 3 observações ópticas válidas entre plantio e colheita previstos: verificação pelo
     radar (máximo de R_pol a até 30 dias de t_ref e colheita detectada depois, eq. 28).
  4. Emergência (eq. 26, p_e = 0,20) e colheita pelo radar (eq. 28, κ = 2 dB).
  5. Observações ópticas válidas no espigamento + enchimento (t_ref − 10 a t_ref + 50 dias).
  6. Curvas medianas por classe (S2 e S1) e figuras.

Saídas:
  dados/intermediarios/series/<ano>_<estrato>/metricas_glebas.parquet
  dados/intermediarios/series/<ano>_<estrato>/curvas_classe.csv
  docs/figuras/etapa3_<ano>_<estrato>_*.png

Uso:
  python 02_gee_compositos/02_analise_series_piloto.py [--ano 2019] [--estrato S1]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter

RAIZ = Path(__file__).resolve().parents[1]
FIG = RAIZ / "docs" / "figuras"

FRAC_VALIDA_MIN = 0.8
ALFA_NDPI = 0.74
DELTA_MIN = 0.30          # δ (eq. 8)
TAU = 30                  # τ (eq. 8), dias
DIAS_PICO = 65            # plantio previsto (meio da janela) -> pico do NDVI (calibrado no piloto 2019: mediana 59 d)
JANELA_PRE, JANELA_POS = 15, 150   # busca do pico: plantio − 15 a plantio + 150 dias
P_E = 0.20                # eq. 26
KAPPA = 2.0               # eq. 28, dB
MIN_OBS_OPTICAS = 3
PASSO = 10                # dias

CLASSES_FIG = ["trigo", "aveia", "cevada", "canola", "milho_2safra", "irrigada_inverno", "outras_inverno"]
CORES = dict(zip(CLASSES_FIG, ["#1b5e20", "#e65100", "#1565c0", "#f9a825", "#6a1b9a", "#00838f", "#757575"]))


# ------------------------------------------------------------------ Sentinel-2
def indices(s2: pd.DataFrame) -> pd.DataFrame:
    s2 = s2[s2["frac_valida"] >= FRAC_VALIDA_MIN].copy()
    s2["data"] = pd.to_datetime(s2["data"])
    s2 = s2.groupby(["gid", "data"], as_index=False).mean(numeric_only=True)
    b = {k: s2[k] for k in ["B2", "B4", "B5", "B6", "B8", "B8A", "B11"]}
    s2["NDVI"] = (b["B8"] - b["B4"]) / (b["B8"] + b["B4"])
    s2["EVI"] = 2.5 * (b["B8"] - b["B4"]) / (b["B8"] + 6 * b["B4"] - 7.5 * b["B2"] + 1)
    mix = ALFA_NDPI * b["B4"] + (1 - ALFA_NDPI) * b["B11"]
    s2["NDPI"] = (b["B8"] - mix) / (b["B8"] + mix)
    s2["PSRI"] = (b["B4"] - b["B2"]) / b["B6"]
    s2["LSWI"] = (b["B8"] - b["B11"]) / (b["B8"] + b["B11"])
    s2["NDRE"] = (b["B8A"] - b["B5"]) / (b["B8A"] + b["B5"])
    return s2


def grade(inicio: pd.Timestamp, fim: pd.Timestamp) -> pd.DatetimeIndex:
    return pd.date_range(inicio, fim, freq=f"{PASSO}D")


def serie_regular(df: pd.DataFrame, var: str, g: pd.DatetimeIndex) -> np.ndarray:
    """Mediana por intervalo de 10 dias, interpolação linear e Savitzky–Golay."""
    if df.empty:
        return np.full(len(g), np.nan)
    pos = np.searchsorted(g.values, df["data"].values, side="right") - 1
    s = pd.Series(df[var].values).groupby(pos).median()
    s = s[(s.index >= 0) & (s.index < len(g))]
    y = np.full(len(g), np.nan)
    y[s.index.values] = s.values
    ok = ~np.isnan(y)
    if ok.sum() < 4:
        return y
    x = np.arange(len(g))
    y = np.interp(x, x[ok], y[ok])
    return savgol_filter(y, 5, 2)


# ------------------------------------------------------------------ Sentinel-1
def preparar_s1(s1: pd.DataFrame) -> pd.DataFrame:
    s1 = s1.copy()
    s1["data"] = pd.to_datetime(s1["data"]).dt.normalize()
    s1 = s1.groupby(["gid", "data", "orbita", "passagem"], as_index=False)[["VV_lin", "VH_lin", "angle"]].mean()
    # órbita dominante por gleba (série homogênea em geometria; a normalização angular é tratada no E1)
    dom = s1.groupby(["gid", "orbita"]).size().reset_index(name="n").sort_values("n").drop_duplicates("gid", keep="last")
    s1 = s1.merge(dom[["gid", "orbita"]], on=["gid", "orbita"])
    s1["VV"] = 10 * np.log10(s1["VV_lin"])
    s1["VH"] = 10 * np.log10(s1["VH_lin"])
    s1["Rpol"] = s1["VH"] - s1["VV"]                                   # eq. 16
    s1["RVI"] = 4 * s1["VH_lin"] / (s1["VV_lin"] + s1["VH_lin"])       # eq. 17
    return s1.sort_values(["gid", "data"])


def colheita_radar(s: pd.DataFrame, t_inicio: pd.Timestamp) -> tuple[pd.Timestamp | None, pd.Timestamp | None]:
    """Máximo de R_pol após t_inicio e primeira queda abrupta e persistente (eq. 28)."""
    s = s[s["data"] >= t_inicio].reset_index(drop=True)
    if len(s) < 4:
        return None, None
    r = s["Rpol"].rolling(3, center=True, min_periods=1).median()   # robustez a datas isoladas
    k_max = int(r.idxmax())
    t_max = s.loc[k_max, "data"]
    v = s["Rpol"].values
    for k in range(max(k_max + 1, 1), len(s) - 1):
        if v[k] - v[k - 1] <= -KAPPA and v[k + 1] - v[k - 1] <= -KAPPA:
            return t_max, s.loc[k, "data"]
    return t_max, None


# ------------------------------------------------------------------ métricas por gleba
def metricas(amostra: pd.DataFrame, s2: pd.DataFrame, s1: pd.DataFrame, ano: int) -> tuple[pd.DataFrame, dict]:
    g = grade(pd.Timestamp(f"{ano}-03-01"), pd.Timestamp(f"{ano + 1}-01-10"))
    s2g, s1g = dict(tuple(s2.groupby("gid"))), dict(tuple(s1.groupby("gid")))
    vars_s2 = ["NDVI", "EVI", "NDPI", "PSRI", "LSWI", "NDRE"]
    curvas = {v: {} for v in vars_s2}
    linhas = []
    for _, a in amostra.iterrows():
        gid = a["gid"]
        plantio = a["DT_INIC_PLANTIO"] + (a["DT_FIM_PLANTIO"] - a["DT_INIC_PLANTIO"]) / 2 \
            if pd.notna(a["DT_FIM_PLANTIO"]) else a["DT_INIC_PLANTIO"]
        t_ref = plantio + pd.Timedelta(days=DIAS_PICO) if pd.notna(plantio) else pd.NaT
        d2 = s2g.get(gid, pd.DataFrame(columns=["data"] + vars_s2))
        for v in vars_s2:
            curvas[v][gid] = serie_regular(d2, v, g)
        ndvi = curvas["NDVI"][gid]
        lin = {"gid": gid, "t_ref": t_ref, "plantio_previsto": plantio}

        # observações ópticas válidas
        if pd.notna(t_ref):
            ini_c = a["DT_INIC_PLANTIO"]
            fim_c = a["DT_FIM_COLHEITA"] if pd.notna(a["DT_FIM_COLHEITA"]) else t_ref + pd.Timedelta(days=90)
            lin["n_opt_ciclo"] = int(d2["data"].between(ini_c, fim_c).sum())
            lin["n_opt_esp_ench"] = int(d2["data"].between(t_ref - pd.Timedelta(days=10), t_ref + pd.Timedelta(days=50)).sum())

        # eq. 8 (óptico)
        if np.isfinite(ndvi).sum() >= 4:
            # ciclo de inverno ancorado no plantio previsto da gleba, para não capturar o fim da
            # cultura de verão (sem data: abril a novembro)
            if pd.notna(plantio):
                ini_j, fim_j = plantio - pd.Timedelta(days=JANELA_PRE), plantio + pd.Timedelta(days=JANELA_POS)
                ini_min = plantio - pd.Timedelta(days=30)
            else:
                ini_j, fim_j = pd.Timestamp(f"{ano}-04-01"), pd.Timestamp(f"{ano}-11-30")
                ini_min = pd.Timestamp(f"{ano}-03-01")
            inv = (g >= ini_j) & (g <= fim_j)
            k_max = int(np.nanargmax(np.where(inv, ndvi, -np.inf)))
            pre = ndvi[: k_max + 1][g[: k_max + 1] >= ini_min]
            if pre.size == 0:
                pre = ndvi[k_max:k_max + 1]
            pos = ndvi[k_max:]
            x_max, x_min_pre, x_min_pos = ndvi[k_max], np.nanmin(pre), np.nanmin(pos)
            lin.update(NDVI_max=x_max, NDVI_min_pre=x_min_pre, delta_NDVI=x_max - x_min_pre, t_pico=g[k_max])
            # eq. 26: emergência e maturação
            lim_e = x_min_pre + P_E * (x_max - x_min_pre)
            ke = np.where(ndvi[: k_max + 1] <= lim_e)[0]
            lin["t_emergencia"] = g[ke[-1]] + pd.Timedelta(days=PASSO / 2) if len(ke) else pd.NaT
            lim_m = x_min_pos + 0.5 * (x_max - x_min_pos)
            km = np.where(pos <= lim_m)[0]
            lin["t_maturacao"] = g[k_max + km[0]] if len(km) else pd.NaT

        # radar
        d1 = s1g.get(gid)
        if d1 is not None and pd.notna(plantio):
            t_rmax, t_c = colheita_radar(d1, plantio)
            lin.update(t_Rpol_max=t_rmax, t_colheita_radar=t_c, n_s1=len(d1),
                       passagem_s1=d1["passagem"].iloc[0], orbita_s1=d1["orbita"].iloc[0])
        linhas.append(lin)

    m = amostra.drop(columns="geometry").merge(pd.DataFrame(linhas), on="gid")
    dias = lambda a, b: (m[a] - m[b]).dt.days.abs()
    m["coerente_optico"] = (m["delta_NDVI"] >= DELTA_MIN) & (dias("t_pico", "t_ref") <= TAU)
    m["verificavel_optico"] = m["n_opt_ciclo"] >= MIN_OBS_OPTICAS
    m["coerente_radar"] = (dias("t_Rpol_max", "t_ref") <= TAU) & m["t_colheita_radar"].notna()
    m["coerente"] = np.where(m["verificavel_optico"], m["coerente_optico"], m["coerente_radar"])
    m["via_radar"] = ~m["verificavel_optico"]
    return m, {"grade": g, **curvas}


def curvas_classe(m: pd.DataFrame, c: dict, s1: pd.DataFrame, ano: int) -> pd.DataFrame:
    g = c["grade"]
    ok = m[(m["classe"] != "trigo") | m["coerente"]]  # trigo: só glebas coerentes
    linhas = []
    for classe, gr in ok.groupby("classe"):
        for v in ["NDVI", "EVI", "NDPI", "PSRI", "LSWI", "NDRE"]:
            arr = np.vstack([c[v][gid] for gid in gr["gid"]])
            q = np.nanpercentile(arr, [25, 50, 75], axis=0)
            for i, d in enumerate(g):
                linhas.append({"classe": classe, "var": v, "data": d, "q25": q[0, i], "q50": q[1, i], "q75": q[2, i], "n": len(gr)})
        s = s1[s1["gid"].isin(gr["gid"])].copy()
        s["bin"] = g[np.clip(np.searchsorted(g.values, s["data"].values, side="right") - 1, 0, len(g) - 1)]
        for v in ["VV", "VH", "Rpol", "RVI"]:
            q = s.groupby("bin")[v].quantile([0.25, 0.5, 0.75]).unstack()
            for d, row in q.iterrows():
                linhas.append({"classe": classe, "var": v, "data": d, "q25": row[0.25], "q50": row[0.5], "q75": row[0.75], "n": len(gr)})
    return pd.DataFrame(linhas)


def figuras(cur: pd.DataFrame, m: pd.DataFrame, ano: int, estrato: str) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    pref = FIG / f"etapa3_{ano}_{estrato}"
    for grupo, vs in {"optico": ["NDVI", "NDPI", "PSRI", "LSWI"], "radar": ["VH", "VV", "Rpol", "RVI"]}.items():
        fig, axs = plt.subplots(2, 2, figsize=(11, 7), sharex=True)
        for ax, v in zip(axs.flat, vs):
            for classe in CLASSES_FIG:
                d = cur[(cur["classe"] == classe) & (cur["var"] == v)]
                if d.empty:
                    continue
                n = int(d["n"].iloc[0])
                ax.plot(d["data"], d["q50"], c=CORES[classe], lw=1.6 if classe == "trigo" else 1.1, label=f"{classe} (n={n})")
                ax.fill_between(d["data"], d["q25"], d["q75"], color=CORES[classe], alpha=0.12 if classe == "trigo" else 0.06, lw=0)
            ax.set_title(v + (" (dB)" if v in ("VV", "VH", "Rpol") else ""))
            ax.grid(alpha=0.3)
        axs[0, 0].legend(fontsize=7, ncol=2)
        fig.suptitle(f"Mediana e intervalo interquartil por classe, safra {ano}, estrato {estrato} (glebas SICOR)")
        fig.autofmt_xdate(); fig.tight_layout()
        fig.savefig(f"{pref}_curvas_{grupo}.png", dpi=150); plt.close(fig)

    tr = m[m["classe"] == "trigo"]
    fig, axs = plt.subplots(1, 3, figsize=(13, 3.8))
    axs[0].hist(tr["n_opt_esp_ench"].clip(upper=15), bins=np.arange(17) - 0.5, color="#1b5e20")
    axs[0].set_xlabel("Obs. ópticas válidas no espigamento + enchimento"); axs[0].set_ylabel("Glebas de trigo")
    e = (tr["t_emergencia"] - tr["plantio_previsto"]).dt.days.dropna()
    axs[1].hist(e.clip(-60, 90), bins=30, color="#1565c0")
    axs[1].set_xlabel("Emergência detectada − plantio previsto (dias)")
    c = (tr["t_colheita_radar"] - (tr["DT_INIC_COLHEITA"] + (tr["DT_FIM_COLHEITA"] - tr["DT_INIC_COLHEITA"]) / 2)).dt.days.dropna()
    axs[2].hist(c.clip(-90, 90), bins=30, color="#e65100")
    axs[2].set_xlabel("Colheita pelo radar − colheita prevista (dias)")
    fig.suptitle(f"Trigo, safra {ano}, {estrato}")
    fig.tight_layout(); fig.savefig(f"{pref}_trigo_datas.png", dpi=150); plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ano", type=int, default=2019)
    ap.add_argument("--estrato", default="S1")
    args = ap.parse_args()
    d = RAIZ / "dados" / "intermediarios" / "series" / f"{args.ano}_{args.estrato}"

    amostra = pd.read_parquet(d / "amostra.parquet")
    s2 = indices(pd.read_parquet(d / "s2.parquet"))
    s1 = preparar_s1(pd.read_parquet(d / "s1.parquet"))
    m, c = metricas(amostra, s2, s1, args.ano)
    m.to_parquet(d / "metricas_glebas.parquet", index=False)
    # séries regulares (10 dias, suavizadas) por gleba, para a separabilidade (Etapa 4)
    reg = pd.concat([pd.DataFrame({"gid": gid, "data": c["grade"], **{v: c[v][gid] for v in c if v != "grade"}})
                     for gid in amostra["gid"]], ignore_index=True)
    reg.to_parquet(d / "series_regulares_s2.parquet", index=False)
    s1.to_parquet(d / "s1_preparado.parquet", index=False)
    cur = curvas_classe(m, c, s1, args.ano)
    cur.to_csv(d / "curvas_classe.csv", index=False)
    figuras(cur, m, args.ano, args.estrato)

    print("Coerência temporal (eq. 8) por classe:")
    r = m.groupby("classe").agg(n=("gid", "size"), coerente=("coerente", "mean"), via_radar=("via_radar", "mean"),
                                delta_med=("delta_NDVI", "median"))
    print(r.round(3).to_string())
    tr = m[m["classe"] == "trigo"]
    print("\nTrigo - obs. ópticas válidas no espigamento + enchimento:")
    print(tr["n_opt_esp_ench"].clip(upper=3).value_counts(normalize=True).sort_index().rename({3: "≥3"}).round(3).to_string())
    e = (tr["t_emergencia"] - tr["plantio_previsto"]).dt.days
    print(f"\nEmergência − plantio previsto (dias): mediana {e.median():.0f}, IQR {e.quantile(.25):.0f} a {e.quantile(.75):.0f}")
    col_prev = tr["DT_INIC_COLHEITA"] + (tr["DT_FIM_COLHEITA"] - tr["DT_INIC_COLHEITA"]) / 2
    c_ = (tr["t_colheita_radar"] - col_prev).dt.days
    print(f"Colheita radar detectada em {tr['t_colheita_radar'].notna().mean():.1%} das glebas de trigo; "
          f"− prevista: mediana {c_.median():.0f}, IQR {c_.quantile(.25):.0f} a {c_.quantile(.75):.0f}")
    print(f"Pico NDVI − t_ref (dias): mediana {(tr['t_pico'] - tr['t_ref']).dt.days.median():.0f}")
    print("\nColheita detectada pelo radar por classe:")
    print(m.groupby("classe")["t_colheita_radar"].apply(lambda s: s.notna().mean()).round(3).to_string())


if __name__ == "__main__":
    main()
