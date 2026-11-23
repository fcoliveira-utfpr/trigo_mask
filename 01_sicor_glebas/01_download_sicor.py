"""Etapa (ii).1 - Download dos dados brutos do SICOR (Banco Central do Brasil).

Arquivos (https://www.bcb.gov.br/htms/sicor/DadosBrutos/):
  SICOR_OPERACAO_BASICA_ESTADO_<ano>.gz  operações de crédito rural (sem identificação de beneficiários)
  SICOR_GLEBAS_WKT_<ano>.gz              geometrias das glebas (REF_BACEN, NU_ORDEM, NU_INDICE, WKT)
Tabelas de domínio (https://www.bcb.gov.br/htms/sicor/<nome>.csv):
  Empreendimento, TipoIrrigacao, TipoCultivo, FaseCicloProducao, Programa, CategoriaEmitente

Saída: dados/brutos/sicor/ (não versionado; os brutos já são públicos no BCB e não vão para o Release).

Uso:
  python 01_sicor_glebas/01_download_sicor.py [--inicio 2015] [--fim 2026]
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parents[1]
SAIDA = RAIZ / "dados" / "brutos" / "sicor"
BASE = "https://www.bcb.gov.br/htms/sicor"
CABECALHO = {"User-Agent": "Mozilla/5.0 (pesquisa academica)"}
DOMINIOS = ["Empreendimento", "TipoIrrigacao", "TipoCultivo", "FaseCicloProducao",
            "Programa", "CategoriaEmitente"]


def baixar(url: str, destino: Path, tentativas: int = 5) -> None:
    for i in range(1, tentativas + 1):
        try:
            cab = requests.head(url, headers=CABECALHO, timeout=60)
            tamanho = int(cab.headers.get("content-length", -1))
            if destino.exists() and destino.stat().st_size == tamanho:
                print(f"  já existe: {destino.name}")
                return
            tmp = destino.with_suffix(destino.suffix + ".part")
            t0 = time.time()
            with requests.get(url, headers=CABECALHO, stream=True, timeout=600) as r:
                r.raise_for_status()
                with open(tmp, "wb") as f:
                    for bloco in r.iter_content(chunk_size=1 << 20):
                        f.write(bloco)
            tmp.rename(destino)
            print(f"  {destino.name}: {destino.stat().st_size / 1e6:.0f} MB em {time.time() - t0:.0f}s")
            return
        except requests.RequestException as erro:
            print(f"  {destino.name}: tentativa {i} falhou ({erro})")
            time.sleep(15 * i)
    raise RuntimeError(f"Falha: {url}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inicio", type=int, default=2015)
    ap.add_argument("--fim", type=int, default=2026)
    args = ap.parse_args()
    (SAIDA / "dominios").mkdir(parents=True, exist_ok=True)

    print("Tabelas de domínio")
    for nome in DOMINIOS:
        baixar(f"{BASE}/{nome}.csv", SAIDA / "dominios" / f"{nome}.csv")

    for ano in range(args.inicio, args.fim + 1):
        print(f"Ano {ano}")
        for prefixo in ("SICOR_OPERACAO_BASICA_ESTADO", "SICOR_GLEBAS_WKT"):
            nome = f"{prefixo}_{ano}.gz"
            baixar(f"{BASE}/DadosBrutos/{nome}", SAIDA / nome)


if __name__ == "__main__":
    main()
