"""Etapa (i).1 - Download da PAM/IBGE (SIDRA, tabela 1612) por município.

Variáveis: área plantada (109), área colhida (216), quantidade produzida (214).
Produtos (classificação 81): trigo, aveia, cevada, triticale e centeio (em grão).
Período: 2000-2025.

Saídas (em dados/brutos/pam/):
  json/pam_1612_<ano>.json   resposta bruta da API, um arquivo por ano
  pam_1612_municipios.parquet  tabela longa (municipio, ano, produto, variavel, valor)

Códigos especiais do SIDRA, preservados na coluna `flag`:
  "-"   zero absoluto (valor = 0)
  ".."  não se aplica (valor = NaN)
  "..." dado não disponível (valor = NaN)
  "X"   dado omitido por sigilo (valor = NaN)

Uso:
  python 00_pam_sidra/01_download_pam.py [--inicio 2000] [--fim 2025] [--forcar]
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import pandas as pd
import requests

RAIZ = Path(__file__).resolve().parents[1]
SAIDA = RAIZ / "dados" / "brutos" / "pam"
SAIDA_JSON = SAIDA / "json"

URL = "https://servicodados.ibge.gov.br/api/v3/agregados/1612/periodos/{ano}/variaveis/{vars}"

VARIAVEIS = {
    "109": "area_plantada_ha",
    "216": "area_colhida_ha",
    "214": "producao_t",
}

PRODUTOS = {
    "2716": "trigo",
    "2693": "aveia",
    "2699": "cevada",
    "109180": "triticale",
    "2698": "centeio",
}

CODIGOS_ESPECIAIS = {"-": 0.0, "..": None, "...": None, "X": None}


def baixar_ano(ano: int, forcar: bool = False, tentativas: int = 5) -> list:
    destino = SAIDA_JSON / f"pam_1612_{ano}.json"
    if destino.exists() and not forcar:
        return json.loads(destino.read_text(encoding="utf-8"))

    url = URL.format(ano=ano, vars="|".join(VARIAVEIS))
    params = {
        "localidades": "N6[all]",
        "classificacao": f"81[{','.join(PRODUTOS)}]",
    }
    for i in range(1, tentativas + 1):
        try:
            r = requests.get(url, params=params, timeout=300)
            r.raise_for_status()
            dados = r.json()
            destino.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
            return dados
        except (requests.RequestException, ValueError) as erro:
            espera = 10 * i
            print(f"  {ano}: tentativa {i} falhou ({erro}); nova tentativa em {espera}s")
            time.sleep(espera)
    raise RuntimeError(f"Falha ao baixar o ano {ano}")


def achatar(dados: list) -> pd.DataFrame:
    linhas = []
    for var in dados:
        nome_var = VARIAVEIS[var["id"]]
        for res in var["resultados"]:
            cod_prod = next(iter(res["classificacoes"][0]["categoria"]))
            produto = PRODUTOS[cod_prod]
            for s in res["series"]:
                loc = s["localidade"]
                for ano, bruto in s["serie"].items():
                    if bruto in CODIGOS_ESPECIAIS:
                        valor, flag = CODIGOS_ESPECIAIS[bruto], bruto
                    else:
                        valor, flag = float(bruto), ""
                    linhas.append(
                        {
                            "cod_mun": int(loc["id"]),
                            "nome_mun": loc["nome"],
                            "ano": int(ano),
                            "produto": produto,
                            "variavel": nome_var,
                            "valor": valor,
                            "flag": flag,
                        }
                    )
    return pd.DataFrame(linhas)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inicio", type=int, default=2000)
    ap.add_argument("--fim", type=int, default=2025)
    ap.add_argument("--forcar", action="store_true", help="baixa de novo mesmo se o JSON existir")
    args = ap.parse_args()

    SAIDA_JSON.mkdir(parents=True, exist_ok=True)
    tabelas = []
    for ano in range(args.inicio, args.fim + 1):
        t0 = time.time()
        df = achatar(baixar_ano(ano, args.forcar))
        tabelas.append(df)
        print(f"{ano}: {len(df):>7} registros ({time.time() - t0:.1f}s)")

    pam = pd.concat(tabelas, ignore_index=True)
    pam["produto"] = pam["produto"].astype("category")
    pam["variavel"] = pam["variavel"].astype("category")
    arq = SAIDA / "pam_1612_municipios.parquet"
    pam.to_parquet(arq, index=False)

    # resumo de controle: totais nacionais de área plantada por produto e ano
    resumo = (
        pam[pam["variavel"] == "area_plantada_ha"]
        .pivot_table(index="ano", columns="produto", values="valor", aggfunc="sum", observed=True)
        .round(0)
    )
    print("\nÁrea plantada total (ha), soma dos municípios:")
    print(resumo.to_string())
    print(f"\nSalvo: {arq} ({len(pam)} registros)")


if __name__ == "__main__":
    main()
