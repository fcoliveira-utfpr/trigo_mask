"""Etapa (vi) piloto - Random Forest por gleba com validação cruzada em blocos espaciais.

Responde, no piloto, a três perguntas do planejamento:
  E2  ranking das fases (F1 do trigo com as variáveis de cada fase isolada) e acumulação progressiva (MAP);
      alinhamento à emergência × calendário
  E1  ganho do Sentinel-1 (óptico × óptico+radar)
  E9  confusão do trigo com a cevada e a aveia (matriz de confusão)

Unidade: gleba (compósitos por fase de 03_separabilidade/01_jm_por_fase.compositos).
Validação: GroupKFold (5 dobras) pelos blocos de 50 km; F1 da classe trigo (eq. 29).
Trigo: só glebas coerentes (eq. 8). Classes com < 30 glebas são descartadas.

Uso:
  python 04_selecao/01_rf_fases_piloto.py [--ano 2019] [--estrato S1]
"""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, f1_score
from sklearn.model_selection import GroupKFold

RAIZ = Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("jm", RAIZ / "03_separabilidade" / "01_jm_por_fase.py")
jm = importlib.util.module_from_spec(_s)
_s.loader.exec_module(jm)

OPTICO = ["NDVI", "EVI", "NDPI", "PSRI", "LSWI", "NDRE"]
RADAR = ["VV", "VH", "Rpol", "RVI"]
FASES = list(jm.FASES)
N_ARVORES = 300
SEMENTE = 42


def tabela(m, reg, s1, t0) -> pd.DataFrame:
    comp = jm.compositos(m, reg, s1, t0)
    w = comp.pivot_table(index=["gid", "classe"], columns="fase", values=OPTICO + RADAR)
    w.columns = [f"{v}|{f}" for v, f in w.columns]
    w = w.reset_index().merge(m[["gid", "bloco_50km"]], on="gid")
    return w


def avaliar(w: pd.DataFrame, cols: list[str], retornar_pred: bool = False):
    x = w[cols].fillna(w[cols].median())  # fases sem observação: mediana (sinalização fica para a versão final)
    y, grupos = w["classe"].values, w["bloco_50km"].values
    pred = np.empty(len(w), dtype=object)
    for tr, te in GroupKFold(n_splits=5).split(x, y, grupos):
        rf = RandomForestClassifier(n_estimators=N_ARVORES, class_weight="balanced", n_jobs=-1,
                                    min_samples_leaf=2, random_state=SEMENTE)
        rf.fit(x.iloc[tr], y[tr])
        pred[te] = rf.predict(x.iloc[te])
    f1 = f1_score(y == "trigo", pred == "trigo")
    return (f1, pred) if retornar_pred else f1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ano", type=int, default=2019)
    ap.add_argument("--estrato", default="S1")
    args = ap.parse_args()
    d = RAIZ / "dados" / "intermediarios" / "series" / f"{args.ano}_{args.estrato}"
    saida = RAIZ / "dados" / "intermediarios" / "selecao"
    saida.mkdir(parents=True, exist_ok=True)

    m = pd.read_parquet(d / "metricas_glebas.parquet")
    m = m[m["t_emergencia"].notna() & ((m["classe"] != "trigo") | m["coerente"])]
    n = m["classe"].value_counts()
    m = m[m["classe"].isin(n[n >= 30].index)]
    reg = pd.read_parquet(d / "series_regulares_s2.parquet")
    s1 = pd.read_parquet(d / "s1_preparado.parquet")
    t_em = m.set_index("gid")["t_emergencia"]
    t_cal = pd.Series(m.loc[m["classe"] == "trigo", "t_emergencia"].median(), index=t_em.index)
    print(m["classe"].value_counts().to_string())

    res = []
    tabelas = {"emergencia": tabela(m, reg, s1, t_em), "calendario": tabela(m, reg, s1, t_cal)}
    sel = lambda vs, fs: [f"{v}|{f}" for v in vs for f in fs]

    for al, w in tabelas.items():
        for nome_vs, vs in {"optico": OPTICO, "optico+radar": OPTICO + RADAR, "radar": RADAR}.items():
            # fase isolada
            for f in FASES:
                res.append({"alinhamento": al, "variaveis": nome_vs, "modelo": f"fase:{f}", "F1": avaliar(w, sel(vs, [f]))})
            res.append({"alinhamento": al, "variaveis": nome_vs, "modelo": "todas", "F1": avaliar(w, sel(vs, FASES))})
    r = pd.DataFrame(res)

    # MAP (acumulação progressiva) no alinhamento à emergência, óptico+radar
    rk = (r[(r["alinhamento"] == "emergencia") & (r["variaveis"] == "optico+radar") & r["modelo"].str.startswith("fase:")]
          .assign(fase=lambda t: t["modelo"].str[5:]).sort_values("F1", ascending=False)["fase"].tolist())
    w = tabelas["emergencia"]
    acum, anterior = [], 0.0
    print(f"\nRanking das fases (F1 isolado, óptico+radar, emergência): {rk}")
    print("MAP (acumulação progressiva):")
    for f in rk:
        acum.append(f)
        f1 = avaliar(w, sel(OPTICO + RADAR, acum))
        print(f"  + {f:15s} F1 = {f1:.3f} (ganho {f1 - anterior:+.3f})")
        res.append({"alinhamento": "emergencia", "variaveis": "optico+radar", "modelo": "MAP:" + "+".join(acum), "F1": f1})
        anterior = f1
    r = pd.DataFrame(res)
    r.to_csv(saida / f"rf_fases_{args.ano}_{args.estrato}.csv", index=False)

    print("\nF1 do trigo (validação por blocos de 50 km):")
    print(r[~r["modelo"].str.startswith("MAP")].pivot_table(index="modelo", columns=["alinhamento", "variaveis"], values="F1")
          .reindex([f"fase:{f}" for f in FASES] + ["todas"]).round(3).to_string())

    f1, pred = avaliar(w, sel(OPTICO + RADAR, FASES), retornar_pred=True)
    classes = sorted(w["classe"].unique())
    cm = pd.DataFrame(confusion_matrix(w["classe"], pred, labels=classes), index=classes, columns=classes)
    cm.index.name = "referência \\ predito"
    print(f"\nMatriz de confusão (óptico+radar, 6 fases, emergência; F1 trigo = {f1:.3f}):")
    print(cm.to_string())
    cm.to_csv(saida / f"rf_confusao_{args.ano}_{args.estrato}.csv")


if __name__ == "__main__":
    main()
