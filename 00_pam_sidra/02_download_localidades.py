"""Etapa (i).2 - Localidades e malha municipal do IBGE.

Saídas (em dados/brutos/ibge/):
  municipios.parquet         cod_mun, nome, UF, grande região, regiões intermediária e imediata, estrato
  malha_municipios.geojson   malha municipal vigente (API de malhas do IBGE, qualidade intermediária)

Estratos (seção 4 do planejamento), atribuídos por UF:
  S1 = PR, RS, SC | S2 = SP, MS | S3/S4 = MG, GO, DF, BA (Cerrado; S4 = irrigado, separado em nível de pixel)
  Demais UFs: "outro" (alocadas depois ao estrato mais próximo em calendário, conforme o ZARC).

Uso:
  python 00_pam_sidra/02_download_localidades.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import requests

RAIZ = Path(__file__).resolve().parents[1]
SAIDA = RAIZ / "dados" / "brutos" / "ibge"

URL_MUN = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
URL_MALHA = "https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR"

ESTRATO_UF = {
    "PR": "S1", "RS": "S1", "SC": "S1",
    "SP": "S2", "MS": "S2",
    "MG": "S3_S4", "GO": "S3_S4", "DF": "S3_S4", "BA": "S3_S4",
}


def municipios() -> pd.DataFrame:
    r = requests.get(URL_MUN, timeout=120)
    r.raise_for_status()
    linhas = []
    for m in r.json():
        ri = m.get("regiao-imediata") or {}
        rint = ri.get("regiao-intermediaria") or {}
        uf = rint.get("UF") or (m.get("microrregiao") or {}).get("mesorregiao", {}).get("UF", {})
        linhas.append(
            {
                "cod_mun": int(m["id"]),
                "nome_mun": m["nome"],
                "cod_uf": uf.get("id"),
                "uf": uf.get("sigla"),
                "regiao": (uf.get("regiao") or {}).get("nome"),
                "cod_rgint": rint.get("id"),
                "nome_rgint": rint.get("nome"),
                "cod_rgi": ri.get("id"),
                "nome_rgi": ri.get("nome"),
            }
        )
    df = pd.DataFrame(linhas)
    df["estrato"] = df["uf"].map(ESTRATO_UF).fillna("outro")
    return df


def malha() -> bytes:
    params = {
        "intrarregiao": "municipio",
        "formato": "application/vnd.geo+json",
        "qualidade": "intermediaria",
    }
    r = requests.get(URL_MALHA, params=params, timeout=600)
    r.raise_for_status()
    return r.content


def main() -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)

    df = municipios()
    df.to_parquet(SAIDA / "municipios.parquet", index=False)
    print(f"Municípios: {len(df)}")
    print(df.groupby("estrato").size().to_string())

    conteudo = malha()
    (SAIDA / "malha_municipios.geojson").write_bytes(conteudo)
    print(f"Malha: {len(conteudo) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
