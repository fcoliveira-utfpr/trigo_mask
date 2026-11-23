"""Figuras de resultados do projeto (gráficos, mapas, heatmaps e fluxograma).

Lê apenas resultados já salvos em dados/intermediarios/ e grava PNG (200 dpi) em 09_figuras/.
Cada figura é independente: se os dados de uma figura ainda não existirem, ela é pulada.
Rodar de novo a cada etapa concluída.

Paleta (validada com o validador de CVD do skill de visualização):
  UF:     PR #2a78d6, RS #eb6834, SC #1baf7a, SP #eda100, MG #e87ba4, demais #898781 (agrupadas)
  Classe: trigo #2a78d6, aveia #eb6834, cevada #1baf7a, canola #eda100, milho 2ª safra #e87ba4,
          irrigada de inverno #008300, outras de inverno #6250d6
  Sequencial: rampa azul (#cde2fb → #0d366b); divergente: vermelho ↔ cinza ↔ azul.
Cores de contraste < 3:1 sempre acompanhadas de rótulo direto.

Uso:
  python 09_figuras/gerar_figuras.py            # todas
  python 09_figuras/gerar_figuras.py fig02 fig05  # só algumas (pelo prefixo)
"""

from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch

RAIZ = Path(__file__).resolve().parents[1]
INT = RAIZ / "dados" / "intermediarios"
BRUTOS = RAIZ / "dados" / "brutos"
SAIDA = RAIZ / "09_figuras"

ESCOPO = ["PR", "RS", "SC", "SP", "MG"]
UF_COR = {"PR": "#2a78d6", "RS": "#eb6834", "SC": "#1baf7a", "SP": "#eda100", "MG": "#e87ba4", "Demais UFs": "#898781"}
CLASSE_COR = {"trigo": "#2a78d6", "aveia": "#eb6834", "cevada": "#1baf7a", "canola": "#eda100",
              "milho_2safra": "#e87ba4", "irrigada_inverno": "#008300", "outras_inverno": "#6250d6"}
CLASSE_NOME = {"trigo": "Trigo", "aveia": "Aveia", "cevada": "Cevada", "canola": "Canola",
               "milho_2safra": "Milho 2ª safra", "irrigada_inverno": "Irrigada de inverno",
               "outras_inverno": "Outras de inverno", "triticale": "Triticale"}
FASE_NOME = {"estabelecimento": "Estabelec.", "perfilhamento": "Perfilham.", "alongamento": "Alongam.",
             "espigamento": "Espigam.", "enchimento": "Enchim.", "maturacao": "Maturação"}
AZUL = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
VERMELHO = ["#f7c6c5", "#ee8a89", "#e34948", "#b8302f"]
CINZA_NEUTRO = "#f0efec"
TINTA, TINTA2, MUDO, GRADE, EIXO, FUNDO = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
ALBERS = "+proj=aea +lat_0=-12 +lon_0=-54 +lat_1=-2 +lat_2=-22 +x_0=5000000 +y_0=10000000 +ellps=GRS80 +units=m +no_defs"
EXT_ESCOPO = (-58.2, -34.0, -39.5, -13.6)

plt.rcParams.update({
    "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9, "axes.edgecolor": EIXO,
    "axes.labelcolor": TINTA2, "xtick.color": TINTA2, "ytick.color": TINTA2, "text.color": TINTA,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": False, "grid.color": GRADE,
    "grid.linewidth": 0.6, "figure.facecolor": FUNDO, "axes.facecolor": FUNDO, "savefig.facecolor": FUNDO,
    "legend.frameon": False, "legend.fontsize": 8,
})


def salvar(fig, nome: str) -> None:
    fig.savefig(SAIDA / f"{nome}.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  {nome}.png")


def fmt_pct(x: float, casas: int = 1) -> str:
    return f"{100 * x:.{casas}f}%".replace(".", ",")


# ------------------------------------------------------------------ dados base (cache)
_cache: dict = {}


def municipios() -> gpd.GeoDataFrame:
    if "mun" not in _cache:
        malha = gpd.read_file(BRUTOS / "ibge" / "malha_municipios.geojson")
        malha["cod_mun"] = malha["codarea"].astype(int)
        mun = pd.read_parquet(BRUTOS / "ibge" / "municipios.parquet")
        _cache["mun"] = malha[["cod_mun", "geometry"]].merge(mun, on="cod_mun").to_crs(ALBERS)
    return _cache["mun"]


def ufs() -> gpd.GeoDataFrame:
    if "ufs" not in _cache:
        arq = INT / "pam" / "ufs_albers.parquet"
        if arq.exists():
            _cache["ufs"] = gpd.read_parquet(arq)
        else:
            u = municipios()[["uf", "geometry"]].copy()
            u["geometry"] = u.make_valid().buffer(1)
            u = u.dissolve(by="uf").reset_index()
            u["geometry"] = u.buffer(-1)
            u.to_parquet(arq)
            _cache["ufs"] = u
    return _cache["ufs"]


def painel() -> pd.DataFrame:
    if "painel" not in _cache:
        _cache["painel"] = pd.read_parquet(INT / "pam" / "painel_trigo.parquet")
    return _cache["painel"]


def area_uf_ano() -> pd.DataFrame:
    p = pd.read_csv(INT / "pam" / "agregados_uf.csv").pivot_table(index="ano", columns="uf",
                                                                  values="area_plantada_ha", aggfunc="sum")
    return p.fillna(0)


def limites_escopo(ax, contorno_todas: bool = True) -> None:
    u = ufs()
    if contorno_todas:
        u.boundary.plot(ax=ax, color=EIXO, linewidth=0.4)
    u[u["uf"].isin(ESCOPO)].boundary.plot(ax=ax, color=TINTA, linewidth=0.9)


def enquadrar(ax, ext=EXT_ESCOPO) -> None:
    caixa = gpd.GeoSeries.from_xy([ext[0], ext[2]], [ext[1], ext[3]], crs=4326).to_crs(ALBERS)
    ax.set_xlim(caixa.x.min(), caixa.x.max())
    ax.set_ylim(caixa.y.min(), caixa.y.max())
    ax.set_axis_off()


def rotulos_uf(ax, textos: dict[str, str]) -> None:
    u = ufs().set_index("uf")
    desloc = {"SC": (60e3, 0), "RS": (0, -40e3), "SP": (90e3, 90e3)}
    for uf, txt in textos.items():
        p = u.loc[uf, "geometry"].representative_point()
        dx, dy = desloc.get(uf, (0, 0))
        ax.annotate(txt, (p.x + dx, p.y + dy), ha="center", va="center", fontsize=8, fontweight="bold",
                    color=TINTA, bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.85))


# ------------------------------------------------------------------ fig01 fluxograma
def fig01_fluxograma() -> None:
    fig, ax = plt.subplots(figsize=(11, 8.2))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 10.6)
    ax.set_axis_off()

    def caixa(x, y, w, h, texto, estilo="pendente", fs=8.2, bold=False):
        cores = {"concluido": ("#2a78d6", "white", "#2a78d6"), "andamento": ("#cde2fb", TINTA, "#2a78d6"),
                 "pendente": ("white", TINTA2, EIXO), "dado": ("#f0efec", TINTA, EIXO), "nota": ("white", TINTA2, "white")}
        fc, tc, ec = cores[estilo]
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12",
                                    fc=fc, ec=ec, lw=1.2))
        ax.text(x + w / 2, y + h / 2, texto, ha="center", va="center", fontsize=fs, color=tc,
                fontweight="bold" if bold else "normal", wrap=True)

    def seta(x0, y0, x1, y1):
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=10,
                                     color=MUDO, lw=1.0, shrinkA=2, shrinkB=2))

    ax.text(1.35, 10.35, "Dados", ha="center", fontsize=10, fontweight="bold")
    ax.text(5.0, 10.35, "Etapas do método", ha="center", fontsize=10, fontweight="bold")
    ax.text(9.05, 10.35, "Resultados até agora", ha="center", fontsize=10, fontweight="bold")

    dados = [("PAM/IBGE (SIDRA 1612)\nmalha e localidades IBGE", 9.35), ("SICOR/BCB\noperações + glebas", 8.25),
             ("Sentinel-2 SR\n+ Cloud Score+", 6.95), ("Sentinel-1 GRD\n(VV, VH)", 5.85),
             ("Landsat, HLS, MODIS", 2.95), ("Amostra de referência\n(interpretação visual)", 0.35)]
    for txt, y in dados:
        caixa(0.2, y, 2.3, 0.8, txt, "dado")

    etapas = [("(i) PAM e domínio de mapeamento", 9.45, "concluido"),
              ("(ii) Curadoria das glebas do SICOR", 8.35, "concluido"),
              ("(iii–iv) Séries, compósitos e variáveis\nS2 + S1 por gleba", 7.0, "andamento"),
              ("(v) Separabilidade J-M por fase", 5.95, "andamento"),
              ("(vi) Seleção de fases e variáveis", 4.95, "andamento"),
              ("(vii) Classificação C0–C4\ncalibração, priores, pós-proc.", 3.85, "pendente"),
              ("(viii) Retroação 2000–2016", 2.95, "pendente"),
              ("(ix) Fenologia (emergência,\npico, maturação, colheita)", 1.95, "pendente"),
              ("(x) Validação: gleba, amostra\nprobabilística, área (PAM/CONAB)", 0.75, "pendente")]
    alt = {0: 0.7, 2: 0.8, 5: 0.8, 7: 0.8, 8: 0.8}
    ys = []
    for i, (txt, y, est) in enumerate(etapas):
        h = alt.get(i, 0.6)
        caixa(3.2, y, 3.6, h, txt, est, bold=(est != "pendente"))
        ys.append((y, h))
    for (y0, h0), (y1, h1) in zip(ys[:-1], ys[1:]):
        seta(5.0, y0, 5.0, y1 + h1)
    for (_, yd), ye in zip(dados[:4], [0, 1, 2, 2]):
        y, h = ys[ye]
        seta(2.5, yd + 0.4, 3.2, y + h / 2)
    seta(2.5, 2.95 + 0.4, 3.2, ys[6][0] + 0.3)
    seta(2.5, 0.35 + 0.4, 3.2, ys[8][0] + 0.4)

    notas = [("Escopo PR, RS, SC, SP, MG = 97,5% da área\n(2021–25); domínio retém ~100%", 9.45),
             ("307 mil glebas de trigo aptas (2016–26);\n97% passam nos filtros; Cerrado sem rótulos", 8.35),
             ("Pilotos 2019, 2021, 2023, 2025 (S1):\n~4.200 glebas/safra; emergência ≈ plantio + 11 d", 7.0),
             ("Trigo × cevada ≤ 0,62 por fase;\n1,69 com fases + radar (mesmos blocos)", 5.95),
             ("RF por gleba: F1 = 0,85 (2019);\nradar +0,05; espigamento é a melhor fase", 4.95),
             ("Sentinel-1 ausente no Sul em 2022–24:\nessas safras serão só ópticas", 3.85)]
    for txt, y in notas:
        caixa(7.2, y, 3.7, 0.7 if y != 7.0 else 0.8, txt, "nota", fs=7.6)
        ax.plot([6.8, 7.2], [y + 0.35, y + 0.35], color=GRADE, lw=1, ls=":")

    caixa(7.6, 0.75, 2.9, 1.6, "Produtos: mapas anuais de trigo\n(30 m; 10 m desde 2017), probabilidade,\n"
          "datas fenológicas, área municipal\ncorrigida com IC, código aberto", "dado", fs=7.6)
    seta(6.8, ys[8][0] + 0.4, 7.6, 1.55)

    ax.legend(handles=[Patch(fc="#2a78d6", ec="#2a78d6", label="Concluída"),
                       Patch(fc="#cde2fb", ec="#2a78d6", label="Em andamento (piloto)"),
                       Patch(fc="white", ec=EIXO, label="Pendente")],
              loc="lower left", bbox_to_anchor=(0.0, -0.05), ncol=3, fontsize=8)
    ax.set_title("Fluxo metodológico do mapeamento anual do trigo e situação das etapas", loc="left", pad=14)
    salvar(fig, "fig01_fluxograma_metodo")


# ------------------------------------------------------------------ fig02 mapa da área municipal
def fig02_mapa_area_municipal() -> None:
    p = painel()
    media = p[p["ano"].between(2021, 2025)].groupby("cod_mun")["area_plantada_ha"].apply(lambda s: s.fillna(0).sum() / 5)
    m = municipios().merge(media.rename("area").reset_index(), on="cod_mun", how="left").fillna({"area": 0})
    limites = [0, 1, 500, 2000, 5000, 15000, 1e9]
    cores = [FUNDO, AZUL[1], AZUL[2], AZUL[3], AZUL[5], AZUL[6]]
    cmap, norm = ListedColormap(cores), BoundaryNorm(limites, len(cores))
    a = area_uf_ano().loc[2021:2025].sum()
    part = (a / a.sum())

    fig, axs = plt.subplots(1, 2, figsize=(12, 7), gridspec_kw={"width_ratios": [0.75, 1.25]})
    for ax, zoom in zip(axs, (False, True)):
        m.plot(ax=ax, column="area", cmap=cmap, norm=norm, linewidth=0)
        limites_escopo(ax)
        if zoom:
            enquadrar(ax)
            rotulos_uf(ax, {uf: f"{uf} {fmt_pct(part[uf], 0)}" for uf in ESCOPO})
        else:
            ax.set_axis_off()
            ax.set_title("Brasil", loc="left")
    axs[1].set_title(f"Escopo (contorno preto): PR, RS, SC, SP e MG = {fmt_pct(part[ESCOPO].sum())} da área",
                     loc="left")
    nomes = ["sem trigo", "1–500", "500–2.000", "2.000–5.000", "5.000–15.000", "> 15.000"]
    fig.legend(handles=[Patch(fc=c, ec=EIXO, lw=0.5, label=n) for c, n in zip(cores, nomes)],
               title="Área plantada média de trigo, 2021–2025 (ha)", loc="lower center", ncol=6,
               bbox_to_anchor=(0.5, 0.02))
    fig.suptitle("Distribuição municipal do trigo no Brasil (PAM/IBGE)", x=0.01, ha="left", fontsize=12)
    salvar(fig, "fig02_mapa_area_trigo_municipios")


# ------------------------------------------------------------------ fig03 Pareto por UF
def fig03_pareto_uf() -> None:
    a = area_uf_ano().loc[2021:2025].sum()
    s = a / a.sum()
    # UFs do escopo primeiro (ordem decrescente), depois as demais
    top = pd.concat([s[ESCOPO].sort_values(ascending=False), s.drop(ESCOPO).sort_values(ascending=False).head(5)])
    acum = top.cumsum()
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    x = np.arange(len(top))
    cores = [UF_COR.get(u, UF_COR["Demais UFs"]) for u in top.index]
    ax.bar(x, 100 * top.values, color=cores, width=0.68, edgecolor=FUNDO, linewidth=2)
    for i, v in enumerate(top.values):
        if v > 0.15:
            ax.text(i, 100 * v - 3, fmt_pct(v), ha="center", va="top", fontsize=8.5, color="white", fontweight="bold")
        else:
            ax.text(i, 100 * v + 1.2, fmt_pct(v), ha="center", fontsize=8, color=TINTA)
    ax.plot(x, 100 * acum.values, color=TINTA, lw=2, marker="o", ms=5, zorder=3)
    k = len(ESCOPO) - 1
    ax.annotate(f"Escopo (5 UFs): {fmt_pct(acum.iloc[k])}", (k, 100 * acum.iloc[k]), xytext=(15, -32),
                textcoords="offset points", fontsize=9, fontweight="bold",
                arrowprops=dict(arrowstyle="-", color=TINTA2, lw=0.8))
    ax.axvspan(-0.5, k + 0.5, color="#cde2fb", alpha=0.35, lw=0, zorder=0)
    ax.text(len(top) - 1, 100 * acum.iloc[-1] - 7, "% acumulado", ha="right", fontsize=8, color=TINTA2)
    ax.set_xticks(x, top.index)
    ax.set_ylim(0, 108)
    ax.set_ylabel("Participação na área plantada de trigo (%)")
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)
    ax.set_title("Participação das UFs na área de trigo, 2021–2025 (barras) e participação acumulada (linha)", loc="left")
    salvar(fig, "fig03_pareto_area_uf")


# ------------------------------------------------------------------ fig04 série por UF
def fig04_series_uf() -> None:
    p = area_uf_ano()
    d = pd.DataFrame({uf: p[uf] for uf in ESCOPO})
    d["Demais UFs"] = p.drop(columns=ESCOPO).sum(axis=1)
    d = d / 1e3
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.3), gridspec_kw={"width_ratios": [1.6, 1]})
    ax = axs[0]
    ax.stackplot(d.index, d.T.values, colors=[UF_COR[c] for c in d.columns], edgecolor=FUNDO, linewidth=0.8)
    base = d.cumsum(axis=1)
    for c in d.columns:
        y = base[c].iloc[-1] - d[c].iloc[-1] / 2
        ax.text(d.index[-1] + 0.4, y, c, va="center", fontsize=8, color=TINTA)
    ax.set_xlim(d.index[0], d.index[-1] + 2.2)
    ax.set_ylabel("Área plantada (mil ha)")
    ax.yaxis.grid(True); ax.set_axisbelow(True)
    ax.set_title("Área plantada de trigo por UF, 2000–2025", loc="left")

    ax = axs[1]
    for c in ["SP", "MG", "Demais UFs"]:
        ax.plot(d.index, d[c], color=UF_COR[c], lw=2)
        ax.text(d.index[-1] + 0.4, d[c].iloc[-1], c, va="center", fontsize=8)
    ax.set_xlim(d.index[0], d.index[-1] + 3.5)
    ax.yaxis.grid(True); ax.set_axisbelow(True)
    ax.set_ylabel("Área plantada (mil ha)")
    ax.set_title("Fora do Sul: SP e MG concentram a expansão", loc="left")
    salvar(fig, "fig04_series_area_uf")


# ------------------------------------------------------------------ fig05 expansão
def fig05_mapa_expansao() -> None:
    p = painel()
    def media(a, b):
        return p[p["ano"].between(a, b)].groupby("cod_mun")["area_plantada_ha"].apply(lambda s: s.fillna(0).sum() / (b - a + 1))
    dif = (media(2021, 2025) - media(2010, 2014).reindex(media(2021, 2025).index, fill_value=0)).rename("dif")
    m = municipios().merge(dif.reset_index(), on="cod_mun", how="left").fillna({"dif": 0})
    limites = [-1e9, -5000, -1000, -100, 100, 1000, 5000, 1e9]
    cores = [VERMELHO[3], VERMELHO[2], VERMELHO[0], CINZA_NEUTRO, AZUL[1], AZUL[3], AZUL[5]]
    fig, ax = plt.subplots(figsize=(7.5, 7.8))
    m.plot(ax=ax, column="dif", cmap=ListedColormap(cores), norm=BoundaryNorm(limites, len(cores)), linewidth=0)
    limites_escopo(ax)
    enquadrar(ax)
    nomes = ["< −5.000", "−5.000 a −1.000", "−1.000 a −100", "−100 a 100", "100 a 1.000", "1.000 a 5.000", "> 5.000"]
    ax.legend(handles=[Patch(fc=c, ec=EIXO, lw=0.5, label=n) for c, n in zip(cores, nomes)],
              title="Variação da área média (ha)", loc="lower right")
    ax.set_title("Variação da área de trigo: média 2021–2025 menos média 2010–2014", loc="left")
    salvar(fig, "fig05_mapa_expansao_trigo")


# ------------------------------------------------------------------ fig06 domínio no escopo
def fig06_mapa_dominio() -> None:
    dom = pd.read_csv(INT / "pam" / "dominio.csv")
    dom = dom[dom["uf"].isin(ESCOPO)]
    m = municipios()
    m = m.assign(classe=np.where(m["cod_mun"].isin(dom.loc[dom["nucleo"], "cod_mun"]), "núcleo",
                                 np.where(m["cod_mun"].isin(dom["cod_mun"]), "vizinho", "fora")))
    m.loc[~m["uf"].isin(ESCOPO), "classe"] = "fora do escopo"
    cores = {"fora do escopo": "#e9e8e3", "fora": FUNDO, "vizinho": AZUL[1], "núcleo": AZUL[4]}
    a = painel()
    a = a[a["ano"] >= 2000]
    esc = a[a["uf"].isin(ESCOPO)]
    ret = esc[esc["cod_mun"].isin(dom["cod_mun"])]["area_plantada_ha"].sum() / esc["area_plantada_ha"].sum()
    fig, ax = plt.subplots(figsize=(7.5, 7.8))
    for c, cor in cores.items():
        sub = m[m["classe"] == c]
        if len(sub):
            sub.plot(ax=ax, color=cor, linewidth=0)
    limites_escopo(ax)
    enquadrar(ax)
    n_nuc, n_dom = int(dom["nucleo"].sum()), len(dom)
    rot = {"núcleo": f"núcleo: ≥ 50 ha em ≥ 2 safras ({n_nuc} mun.)", "vizinho": f"vizinhos de 1ª ordem ({n_dom - n_nuc} mun.)",
           "fora": "fora do domínio", "fora do escopo": "UF fora do escopo"}
    ax.legend(handles=[Patch(fc=cores[k], ec=EIXO, lw=0.5, label=v) for k, v in rot.items()], loc="lower right")
    ret_txt = f"{np.floor(ret * 1e4) / 100:.2f}%".replace(".", ",")  # truncado: não arredondar para 100%
    ax.set_title(f"Domínio de mapeamento no escopo: {n_dom:,} municípios, {ret_txt} da área de trigo 2000–2025".replace(",", "X", 1).replace("X", ".", 1),
                 loc="left")
    salvar(fig, "fig06_mapa_dominio_escopo")


# ------------------------------------------------------------------ fig07 glebas SICOR
def fig07_glebas_sicor() -> None:
    arqs = sorted((INT / "sicor" / "rotulos").glob("rotulos_sicor_*.parquet"))
    if not arqs:
        return
    g = pd.concat([pd.read_parquet(a, columns=["classe", "uf_gleba", "ano_safra", "apto"]) for a in arqs])
    g = g[(g["classe"] == "trigo") & g["apto"] & g["ano_safra"].between(2016, 2026)]
    g["uf"] = np.where(g["uf_gleba"].isin(ESCOPO), g["uf_gleba"], "Demais UFs")
    c = g.groupby(["ano_safra", "uf"]).size().unstack(fill_value=0).reindex(columns=list(UF_COR), fill_value=0)

    rep = pd.read_csv(INT / "sicor" / "representatividade_municipal.csv")
    rep = rep.merge(pd.read_parquet(BRUTOS / "ibge" / "municipios.parquet")[["cod_mun", "uf"]], on="cod_mun")
    rep = rep[rep["ano"].between(2017, 2025) & rep["uf"].isin(ESCOPO)]
    h = rep.groupby(["uf", "ano"])[["area_glebas_ha", "area_plantada_ha"]].sum()
    h = (h["area_glebas_ha"] / h["area_plantada_ha"]).unstack().reindex(ESCOPO)

    fig, axs = plt.subplots(1, 2, figsize=(13, 4.4), gridspec_kw={"width_ratios": [1.25, 1]})
    ax = axs[0]
    base = np.zeros(len(c))
    for uf in c.columns:
        ax.bar(c.index, c[uf] / 1e3, bottom=base / 1e3, color=UF_COR[uf], width=0.7, edgecolor=FUNDO, linewidth=1, label=uf)
        base += c[uf].values
    for x, v in zip(c.index, base):
        txt = f"{v / 1e3:.1f}" if v < 1e3 else f"{v / 1e3:.0f}"
        ax.text(x, v / 1e3 + 0.8, txt.replace(".", ","), ha="center", fontsize=7.5, color=TINTA2)
    ax.set_ylabel("Glebas de trigo aptas (mil)")
    ax.set_xticks(c.index, [str(int(a)) for a in c.index], rotation=0, fontsize=8)
    ax.yaxis.grid(True); ax.set_axisbelow(True)
    ax.set_ylim(0, base.max() / 1e3 * 1.12)
    ax.legend(ncol=3, loc="upper left")
    n_sp, n_mg, n_sul = int(c["SP"].sum()), int(c["MG"].sum()), int(c[["PR", "RS", "SC"]].values.sum())
    ax.text(0.02, 0.80, f"Total 2016–2026: Sul {n_sul:,} | SP {n_sp:,} | MG {n_mg:,}".replace(",", "."),
            transform=ax.transAxes, fontsize=8, color=TINTA, fontweight="bold")
    ax.set_title("Glebas de trigo do SICOR aptas por ano-safra (após curadoria)", loc="left")

    ax = axs[1]
    lim = [0, 0.01, 0.05, 0.1, 0.2, 0.3, 0.45, 0.7]
    cmap, norm = ListedColormap(AZUL), BoundaryNorm(lim, len(AZUL))
    ax.imshow(h.values, cmap=cmap, norm=norm, aspect="auto")
    for (i, j), v in np.ndenumerate(h.values):
        ax.text(j, i, f"{100 * v:.0f}", ha="center", va="center", fontsize=8, color="white" if v >= 0.2 else TINTA)
    ax.set_xticks(range(h.shape[1]), h.columns)
    ax.set_yticks(range(h.shape[0]), h.index)
    ax.spines[:].set_visible(False)
    ax.set_title("Área das glebas / área plantada da PAM (%)", loc="left")
    salvar(fig, "fig07_glebas_sicor_cobertura")


# ------------------------------------------------------------------ fig08 mapa cobertura SICOR
def fig08_mapa_cobertura_sicor() -> None:
    arq = INT / "sicor" / "representatividade_municipal.csv"
    if not arq.exists():
        return
    rep = pd.read_csv(arq)
    rep = rep[rep["ano"].between(2017, 2024)].groupby("cod_mun")[["area_glebas_ha", "area_plantada_ha"]].sum()
    rep["frac"] = np.where(rep["area_plantada_ha"] >= 8 * 50, rep["area_glebas_ha"] / rep["area_plantada_ha"], np.nan)
    m = municipios().merge(rep["frac"].reset_index(), on="cod_mun", how="left")
    lim = [0, 0.05, 0.15, 0.3, 0.5, 0.75, 10]
    cores = AZUL[1:]
    fig, ax = plt.subplots(figsize=(7.5, 7.8))
    m[m["frac"].isna()].plot(ax=ax, color="#e9e8e3", linewidth=0)
    m[m["frac"].notna()].plot(ax=ax, column="frac", cmap=ListedColormap(cores), norm=BoundaryNorm(lim, len(cores)), linewidth=0)
    limites_escopo(ax)
    enquadrar(ax)
    nomes = ["< 5%", "5–15%", "15–30%", "30–50%", "50–75%", "> 75%"]
    ax.legend(handles=[Patch(fc=c, ec=EIXO, lw=0.5, label=n) for c, n in zip(cores, nomes)]
              + [Patch(fc="#e9e8e3", ec=EIXO, lw=0.5, label="< 50 ha/ano de trigo")],
              title="Área das glebas / área da PAM", loc="lower right")
    ax.set_title("Cobertura dos rótulos do SICOR por município, 2017–2024", loc="left")
    salvar(fig, "fig08_mapa_cobertura_sicor")


# ------------------------------------------------------------------ fig09 curvas por classe
def fig09_curvas_classe() -> None:
    for d in sorted((INT / "series").glob("*_S1")):
        arq = d / "curvas_classe.csv"
        if not arq.exists():
            continue
        ano = d.name.split("_")[0]
        cur = pd.read_csv(arq, parse_dates=["data"])
        vs = [("NDVI", "NDVI"), ("NDPI", "NDPI"), ("PSRI", "PSRI"), ("LSWI", "LSWI"),
              ("VH", "VH (dB)"), ("VV", "VV (dB)"), ("Rpol", "R_pol = VH − VV (dB)"), ("RVI", "RVI")]
        fig, axs = plt.subplots(2, 4, figsize=(15, 6.6), sharex=True)
        for ax, (v, titulo) in zip(axs.flat, vs):
            for classe, cor in CLASSE_COR.items():
                s = cur[(cur["classe"] == classe) & (cur["var"] == v)].sort_values("data")
                if s.empty:
                    continue
                if classe == "trigo":
                    ax.fill_between(s["data"], s["q25"], s["q75"], color=cor, alpha=0.18, lw=0)
                ax.plot(s["data"], s["q50"], color=cor, lw=2.2 if classe == "trigo" else 1.3)
            ax.set_title(titulo, loc="left")
            ax.yaxis.grid(True); ax.set_axisbelow(True)
            ax.tick_params(axis="x", labelrotation=30, labelsize=7.5)
        n = cur.groupby("classe")["n"].first()
        fig.legend(handles=[plt.Line2D([], [], color=c, lw=2.2 if k == "trigo" else 1.5,
                                       label=f"{CLASSE_NOME[k]} (n = {int(n.get(k, 0))})") for k, c in CLASSE_COR.items() if k in n],
                   loc="lower center", ncol=7, bbox_to_anchor=(0.5, -0.03))
        radar_ok = int(ano) not in (2022, 2023, 2024)
        aviso = "" if radar_ok else " — Sentinel-1 quase ausente nesta safra (curvas de radar com poucas glebas)"
        fig.suptitle(f"Assinaturas medianas por classe, glebas do SICOR, safra {ano}, Sul (faixa = IQR do trigo){aviso}",
                     x=0.01, ha="left", fontsize=11)
        fig.tight_layout(rect=(0, 0.03, 1, 0.97))
        salvar(fig, f"fig09_curvas_classe_{ano}")


# ------------------------------------------------------------------ fig10 heatmap J-M
def fig10_heatmap_jm() -> None:
    for arq in sorted((INT / "separabilidade").glob("jm_*_S1.csv")):
        ano = arq.stem.split("_")[1]
        r = pd.read_csv(arq)
        r = r[r["alinhamento"] == "emergencia"]
        classes = [c for c in ["aveia", "cevada", "canola", "milho_2safra", "irrigada_inverno", "outras_inverno"]
                   if r.loc[r["classe"] == c, "JM"].notna().any()]
        fases = list(FASE_NOME)
        lim = [0, 0.5, 1.0, 1.4, 1.8, 1.95, 2.01]
        cmap, norm = ListedColormap(AZUL[:6]), BoundaryNorm(lim, 6)
        fig, axs = plt.subplots(1, 3, figsize=(14, 4.2), sharey=True)
        for ax, (g, titulo) in zip(axs, [("optico", "Óptico (NDVI, NDPI, PSRI, LSWI, NDRE)"),
                                         ("radar", "Radar (VV, VH, R_pol)"), ("optico+radar", "Óptico + radar")]):
            t = r[r["grupo"] == g].pivot(index="classe", columns="fase", values="JM").reindex(index=classes, columns=fases)
            ax.imshow(t.values, cmap=cmap, norm=norm, aspect="auto")
            for (i, j), v in np.ndenumerate(t.values):
                if np.isfinite(v):
                    ax.text(j, i, f"{v:.2f}".replace(".", ","), ha="center", va="center", fontsize=8,
                            color="white" if v >= 1.4 else TINTA, fontweight="bold" if v >= 1.8 else "normal")
            ax.set_xticks(range(len(fases)), [FASE_NOME[f] for f in fases], rotation=35, ha="right")
            ax.set_yticks(range(len(classes)), [f"Trigo × {CLASSE_NOME[c].lower()}" for c in classes])
            ax.spines[:].set_visible(False)
            ax.set_title(titulo, loc="left")
        fig.legend(handles=[Patch(fc=AZUL[i], label=f"{lim[i]:.2f}–{min(lim[i + 1], 2):.2f}".replace(".", ",")) for i in range(6)],
                   title="Jeffries-Matusita (0–2; negrito ≥ 1,8)", loc="lower center", ncol=6, bbox_to_anchor=(0.5, -0.12))
        fig.suptitle(f"Separabilidade do trigo por fase (alinhada à emergência), safra {ano}, Sul", x=0.01, ha="left", fontsize=11)
        fig.tight_layout(rect=(0, 0.02, 1, 0.95))
        salvar(fig, f"fig10_heatmap_jm_{ano}")


# ------------------------------------------------------------------ fig11 RF por fase e MAP
def fig11_rf_fases() -> None:
    for arq in sorted((INT / "selecao").glob("rf_fases_*_S1.csv")):
        ano = arq.stem.split("_")[2]
        r = pd.read_csv(arq)
        e = r[r["alinhamento"] == "emergencia"]
        fases = list(FASE_NOME)
        fig, axs = plt.subplots(1, 2, figsize=(12.5, 4.2), gridspec_kw={"width_ratios": [1.4, 1]})
        ax = axs[0]
        series = [("optico", "Óptico", "#2a78d6"), ("optico+radar", "Óptico + radar", "#eb6834"), ("radar", "Radar", "#1baf7a")]
        larg = 0.26
        for k, (v, nome, cor) in enumerate(series):
            s = e[(e["variaveis"] == v) & e["modelo"].str.startswith("fase:")].set_index("modelo")["F1"]
            y = [s.get(f"fase:{f}", np.nan) for f in fases]
            t = e[(e["variaveis"] == v) & (e["modelo"] == "todas")]["F1"]
            rot = f"{nome} — todas as fases: {t.iloc[0]:.3f}".replace(".", ",") if len(t) else nome
            ax.bar(np.arange(6) + (k - 1) * larg, y, width=larg, color=cor, edgecolor=FUNDO, linewidth=1.5, label=rot)
            if len(t):
                ax.axhline(t.iloc[0], color=cor, ls="--", lw=1.2)
        ax.set_xticks(range(6), [FASE_NOME[f] for f in fases])
        ax.set_ylim(0.35, 0.95)
        ax.set_ylabel("F1 do trigo (validação por blocos de 50 km)")
        ax.yaxis.grid(True); ax.set_axisbelow(True)
        ax.legend(loc="upper left", ncol=2, fontsize=7.5, title="Barras: fase isolada; tracejado: todas as fases",
                  title_fontsize=7.5)
        ax.set_title("Cada fase isolada (alinhada à emergência)", loc="left")

        ax = axs[1]
        mp = e[e["modelo"].str.startswith("MAP:")].copy()
        mp["n"] = mp["modelo"].str.count(r"\+") + 1
        mp["ultima"] = mp["modelo"].str.split("+").str[-1].str.replace("MAP:", "")
        ax.plot(mp["n"], mp["F1"], color=TINTA, lw=2, marker="o", ms=6)
        for _, row in mp.iterrows():
            ax.annotate(f"+ {FASE_NOME[row['ultima']]}", (row["n"], row["F1"]), xytext=(4, -12),
                        textcoords="offset points", fontsize=7.5, color=TINTA2)
        ax.set_xticks(mp["n"])
        lo, hi = mp["F1"].min(), mp["F1"].max()
        ax.set_ylim(lo - 0.25 * (hi - lo), hi + 0.1 * (hi - lo))
        ax.set_xlim(0.7, mp["n"].max() + 0.8)
        ax.set_xlabel("Número de fases acumuladas (ordem do ranking)")
        ax.set_ylabel("F1 do trigo")
        ax.yaxis.grid(True); ax.set_axisbelow(True)
        ax.set_title("Acumulação progressiva (MAP), óptico + radar", loc="left")
        fig.suptitle(f"Random Forest por gleba, safra {ano}, Sul", x=0.01, ha="left", fontsize=11)
        fig.tight_layout(rect=(0, 0, 1, 0.94))
        salvar(fig, f"fig11_rf_fases_map_{ano}")


# ------------------------------------------------------------------ fig12 matriz de confusão
def fig12_confusao() -> None:
    for arq in sorted((INT / "selecao").glob("rf_confusao_*_S1.csv")):
        ano = arq.stem.split("_")[2]
        cm = pd.read_csv(arq, index_col=0)
        ordem = [c for c in CLASSE_COR if c in cm.index]
        cm = cm.loc[ordem, ordem]
        norm_cm = cm.div(cm.sum(axis=1), axis=0)
        lim = [0, 0.02, 0.05, 0.1, 0.2, 0.4, 0.7, 1.01]
        fig, ax = plt.subplots(figsize=(7.2, 5.8))
        ax.imshow(norm_cm.values, cmap=ListedColormap(AZUL), norm=BoundaryNorm(lim, 7), aspect="auto")
        for (i, j), v in np.ndenumerate(norm_cm.values):
            ax.text(j, i, f"{100 * v:.0f}\n({cm.values[i, j]})", ha="center", va="center", fontsize=7.2,
                    color="white" if v >= 0.2 else TINTA)
        nomes = [CLASSE_NOME[c] for c in ordem]
        ax.set_xticks(range(len(ordem)), nomes, rotation=35, ha="right")
        ax.set_yticks(range(len(ordem)), nomes)
        ax.set_xlabel("Classe predita")
        ax.set_ylabel("Classe de referência (SICOR)")
        ax.spines[:].set_visible(False)
        ax.set_title(f"Matriz de confusão (% da linha e nº de glebas), safra {ano}, Sul\n"
                     "RF óptico + radar, 6 fases; validação por blocos de 50 km", loc="left")
        salvar(fig, f"fig12_matriz_confusao_{ano}")


# ------------------------------------------------------------------ fig13 cobertura Sentinel-1
def fig13_cobertura_s1() -> None:
    d = INT / "cobertura_s1"
    if not (d / "resumo.csv").exists():
        return
    anos_mapa = [a for a in (2019, 2021, 2023, 2025) if (d / f"grade_{a}.npz").exists()]
    res = pd.read_csv(d / "resumo.csv")
    fig = plt.figure(figsize=(14, 8.6))
    gs = fig.add_gridspec(3, len(anos_mapa), height_ratios=[1.6, 0.16, 1])
    lim = [0, 1, 5, 10, 20, 30, 45, 200]
    cores = ["#e9e8e3"] + AZUL[1:]
    cmap, norm = ListedColormap(cores), BoundaryNorm(lim, len(cores))
    u = ufs().to_crs(4326)
    for k, ano in enumerate(anos_mapa):
        z = np.load(d / f"grade_{ano}.npz")
        n, (x0, y0, x1, y1) = z["n"], z["extensao"]
        ax = fig.add_subplot(gs[0, k])
        ax.imshow(n, extent=(x0, x1, y0, y1), cmap=cmap, norm=norm, interpolation="nearest")
        u.boundary.plot(ax=ax, color=EIXO, lw=0.4)
        u[u["uf"].isin(ESCOPO)].boundary.plot(ax=ax, color=TINTA, lw=0.8)
        ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)
        ax.set_axis_off()
        ax.set_title(str(ano), loc="left", fontsize=11, fontweight="bold")
    ax_leg = fig.add_subplot(gs[1, :])
    ax_leg.set_axis_off()
    ax_leg.legend(handles=[Patch(fc=c, ec=EIXO, lw=0.5, label=n_) for c, n_ in
                           zip(cores, ["0", "1–4", "5–9", "10–19", "20–29", "30–44", "≥ 45"])],
                  title="Aquisições Sentinel-1 IW (VV+VH) por pixel, 1/abr–30/nov", loc="center", ncol=7)
    ax = fig.add_subplot(gs[2, :])
    cores_b = [AZUL[4] if m >= 10 else "#e34948" for m in res["mediana"]]
    ax.bar(res["ano"], res["mediana"], color=cores_b, width=0.65, edgecolor=FUNDO, linewidth=2)
    for a, v, f in zip(res["ano"], res["mediana"], res["frac_lt5"]):
        ax.text(a, v + 0.8, f"{v:.0f}", ha="center", fontsize=9)
        if f > 0.2:
            ax.text(a, 3, f"{fmt_pct(f, 0)} das\nglebas < 5", ha="center", fontsize=7.5, color=TINTA)
    ax.set_xticks(res["ano"])
    ax.set_ylabel("Aquisições (mediana)")
    ax.yaxis.grid(True); ax.set_axisbelow(True)
    ax.set_title("Mediana de aquisições por gleba de trigo da amostra do Sul (1.500 glebas)", loc="left")
    fig.suptitle("Cobertura do Sentinel-1 na janela do trigo: lacuna em 2022–2024 após a falha do Sentinel-1B",
                 x=0.01, ha="left", fontsize=12)
    fig.subplots_adjust(hspace=0.3, top=0.92)
    salvar(fig, "fig13_cobertura_sentinel1")


# ------------------------------------------------------------------ fig14 transferência temporal
def fig14_transferencia() -> None:
    arq = INT / "selecao" / "transferencia_temporal.csv"
    if not arq.exists():
        return
    r = pd.read_csv(arq)
    r["teste"] = r["teste"].astype(int)
    anos = sorted(r["teste"].unique())
    series = [("emergencia", "mesma safra (CV blocos)", "Mesma safra (validação por blocos)", "#898781"),
              ("emergencia", "demais safras", "Treino nas demais safras, alinhado à emergência", "#2a78d6"),
              ("calendario", "demais safras", "Treino nas demais safras, calendário fixo", "#eb6834")]
    fig, ax = plt.subplots(figsize=(9, 4.2))
    larg = 0.26
    for k, (al, tr, nome, cor) in enumerate(series):
        y = [r[(r["alinhamento"] == al) & (r["treino"] == tr) & (r["teste"] == a)]["F1"].mean() for a in anos]
        x = np.arange(len(anos)) + (k - 1) * larg
        ax.bar(x, y, width=larg, color=cor, edgecolor=FUNDO, linewidth=1.5, label=nome)
        for xi, yi in zip(x, y):
            if np.isfinite(yi):
                ax.text(xi, yi + 0.005, f"{yi:.2f}".replace(".", ","), ha="center", fontsize=7.5)
    ax.set_xticks(range(len(anos)), [f"{a}" + ("\n(sem radar)" if a in (2022, 2023, 2024) else "") for a in anos])
    ax.set_xlabel("Safra de teste")
    ax.set_ylim(0.5, 0.98)
    ax.set_ylabel("F1 do trigo")
    ax.yaxis.grid(True); ax.set_axisbelow(True)
    ax.legend(loc="upper left", fontsize=7.5)
    ax.set_title("Transferência temporal do classificador (óptico + fenologia), Sul", loc="left")
    salvar(fig, "fig14_transferencia_temporal")


# ------------------------------------------------------------------ fig15 validação das datas
def fig15_datas_fenologicas() -> None:
    dirs = [d for d in sorted((INT / "series").glob("*_S1")) if (d / "metricas_glebas.parquet").exists()]
    if not dirs:
        return
    cores = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6"]
    fig, axs = plt.subplots(1, 2, figsize=(12, 4))
    for d, cor in zip(dirs, cores):
        ano = d.name.split("_")[0]
        m = pd.read_parquet(d / "metricas_glebas.parquet")
        t = m[(m["classe"] == "trigo") & m["coerente"]]
        e = (t["t_emergencia"] - t["plantio_previsto"]).dt.days.dropna().clip(-60, 90)
        axs[0].hist(e, bins=np.arange(-60, 95, 5), histtype="step", lw=1.8, color=cor, density=True,
                    label=f"{ano} (mediana {e.median():.0f} d)")
        col = t["DT_INIC_COLHEITA"] + (t["DT_FIM_COLHEITA"] - t["DT_INIC_COLHEITA"]) / 2
        c = (t["t_colheita_radar"] - col).dt.days.dropna().clip(-90, 90)
        if len(c) > 50:
            axs[1].hist(c, bins=np.arange(-90, 95, 5), histtype="step", lw=1.8, color=cor, density=True,
                        label=f"{ano} (n = {len(c)}, mediana {c.median():.0f} d)")
    axs[0].axvline(0, color=TINTA2, lw=0.8, ls=":")
    axs[1].axvline(0, color=TINTA2, lw=0.8, ls=":")
    axs[0].set_xlabel("Emergência detectada (eq. 26) − plantio previsto no SICOR (dias)")
    axs[1].set_xlabel("Colheita detectada pelo radar (eq. 28) − colheita prevista no SICOR (dias)")
    for ax in axs:
        ax.set_ylabel("Densidade")
        ax.legend(fontsize=7.5)
        ax.yaxis.grid(True); ax.set_axisbelow(True)
    axs[0].set_title("Emergência: validação independente pelas datas do SICOR", loc="left")
    axs[1].set_title("Colheita pelo radar (κ = 2 dB, a recalibrar)", loc="left")
    fig.suptitle("Trigo coerente (eq. 8), Sul", x=0.01, ha="left", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    salvar(fig, "fig15_validacao_datas_fenologicas")


FIGURAS = [fig01_fluxograma, fig02_mapa_area_municipal, fig03_pareto_uf, fig04_series_uf, fig05_mapa_expansao,
           fig06_mapa_dominio, fig07_glebas_sicor, fig08_mapa_cobertura_sicor, fig09_curvas_classe,
           fig10_heatmap_jm, fig11_rf_fases, fig12_confusao, fig13_cobertura_s1, fig14_transferencia,
           fig15_datas_fenologicas]


def main() -> None:
    filtro = sys.argv[1:]
    for f in FIGURAS:
        if filtro and not any(f.__name__.startswith(p) for p in filtro):
            continue
        print(f.__name__)
        try:
            f()
        except FileNotFoundError as erro:
            print(f"  pulada (dados ausentes: {erro.filename})")


if __name__ == "__main__":
    main()
