"""E5 (piloto) - Transferência temporal do Random Forest por gleba, só óptico + fenologia.

Para cada safra de teste disponível em dados/intermediarios/series/<ano>_S1/:
  - validação dentro da safra (GroupKFold por blocos de 50 km);
  - treino em cada outra safra e teste nesta;
  - treino em todas as outras safras juntas (leave-one-year-out), quando houver ≥ 2.
Dois alinhamentos: emergência e calendário. Rótulos: classes de inverno coerentes (eq. 8).

Saída: dados/intermediarios/selecao/transferencia_temporal.csv

Uso:
  python 04_selecao/02_transferencia_temporal.py
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score

RAIZ = Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("rf", RAIZ / "04_selecao" / "01_rf_fases_piloto.py")
rf_mod = importlib.util.module_from_spec(_s)
_s.loader.exec_module(rf_mod)

INVERNO = ["trigo", "aveia", "cevada", "canola", "triticale", "centeio"]
CLASSES = ["trigo", "aveia", "cevada", "canola", "milho_2safra", "irrigada_inverno", "triticale"]
FEN = ["t_emergencia_doy", "t_pico_doy", "t_maturacao_doy", "dur", "delta_NDVI", "NDVI_max"]
COLS = [f"{v}|{f}" for v in rf_mod.OPTICO for f in rf_mod.FASES] + FEN


def preparar(ano: int, alinhamento: str) -> pd.DataFrame:
    d = RAIZ / "dados" / "intermediarios" / "series" / f"{ano}_S1"
    m = pd.read_parquet(d / "metricas_glebas.parquet")
    m = m[m["t_emergencia"].notna() & (~m["classe"].isin(INVERNO) | m["coerente"]) & m["classe"].isin(CLASSES)]
    reg = pd.read_parquet(d / "series_regulares_s2.parquet")
    s1 = pd.read_parquet(d / "s1_preparado.parquet")
    t_em = m.set_index("gid")["t_emergencia"]
    t0 = t_em if alinhamento == "emergencia" else pd.Series(m.loc[m["classe"] == "trigo", "t_emergencia"].median(), index=t_em.index)
    w = rf_mod.tabela(m, reg, s1, t0)
    fen = m[["gid", "t_emergencia", "t_pico", "t_maturacao", "delta_NDVI", "NDVI_max"]].copy()
    for c in ("t_emergencia", "t_pico", "t_maturacao"):
        fen[f"{c}_doy"] = fen[c].dt.dayofyear
    fen["dur"] = (fen["t_maturacao"] - fen["t_emergencia"]).dt.days
    return w.merge(fen[["gid"] + FEN], on="gid").assign(ano=ano)


def treinar_testar(treino: pd.DataFrame, teste: pd.DataFrame) -> float:
    med = treino[COLS].median()
    rf = RandomForestClassifier(n_estimators=300, class_weight="balanced", min_samples_leaf=2,
                                n_jobs=-1, random_state=42)
    rf.fit(treino[COLS].fillna(med), treino["classe"])
    p = rf.predict(teste[COLS].fillna(med))
    return f1_score(teste["classe"] == "trigo", p == "trigo")


def main() -> None:
    anos = sorted(int(p.name.split("_")[0]) for p in (RAIZ / "dados" / "intermediarios" / "series").glob("*_S1")
                  if (p / "series_regulares_s2.parquet").exists())
    print(f"Safras disponíveis: {anos}")
    res = []
    for al in ("emergencia", "calendario"):
        dados = {a: preparar(a, al) for a in anos}
        for teste in anos:
            res.append({"alinhamento": al, "teste": teste, "treino": "mesma safra (CV blocos)",
                        "F1": rf_mod.avaliar(dados[teste], COLS)})
            for treino in anos:
                if treino != teste:
                    res.append({"alinhamento": al, "teste": teste, "treino": str(treino),
                                "F1": treinar_testar(dados[treino], dados[teste])})
            outros = [a for a in anos if a != teste]
            if len(outros) >= 2:
                res.append({"alinhamento": al, "teste": teste, "treino": "demais safras",
                            "F1": treinar_testar(pd.concat([dados[a] for a in outros]), dados[teste])})
            print(f"{al} teste {teste} ok", flush=True)
    r = pd.DataFrame(res)
    saida = RAIZ / "dados" / "intermediarios" / "selecao"
    saida.mkdir(parents=True, exist_ok=True)
    r.to_csv(saida / "transferencia_temporal.csv", index=False)
    print(r.pivot_table(index=["teste", "treino"], columns="alinhamento", values="F1").round(3).to_string())


if __name__ == "__main__":
    main()
