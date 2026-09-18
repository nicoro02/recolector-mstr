#!/usr/bin/env python3
"""
recolector.py — Acumula velas de 1 minuto semana a semana.

EL PROBLEMA QUE RESUELVE
    Yahoo solo sirve velas de 1 minuto de los ultimos 7 dias. Con eso no
    se puede investigar nada. Pero si se guardan cada semana, en tres
    meses hay 60 dias de mercado propios.

IDEMPOTENTE
    Ejecutarlo dos veces el mismo dia no duplica nada: fusiona por
    (ticker, timestamp) y se queda con la ultima version de cada barra.
    Eso importa porque el cron puede repetirse y porque las ventanas de
    7 dias se solapan entre ejecuciones.

USO
    python recolector.py                  # tickers por defecto
    python recolector.py MSTR COIN        # los que se indiquen
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

TICKERS = ["MSTR", "COIN", "MARA", "RIOT", "CLSK", "BTC-USD", "SPY"]
DIR_DATOS = Path(__file__).parent / "datos"
DIAS = 7                     # el maximo que da Yahoo para velas de 1m


def descargar(ticker: str) -> pd.DataFrame:
    import yfinance as yf

    df = yf.download(ticker, period=f"{DIAS}d", interval="1m",
                     progress=False, auto_adjust=False)
    if df.empty:
        raise ValueError("sin datos")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.rename(columns=str.lower)
    cols = [c for c in ("open", "high", "low", "close", "volume") if c in df.columns]
    df = df[cols].dropna(subset=["close"])

    idx = pd.to_datetime(df.index)
    df.index = idx.tz_localize("UTC") if idx.tz is None else idx.tz_convert("UTC")
    df.index.name = "ts"
    return df.reset_index()


def acumular(ticker: str, nuevo: pd.DataFrame) -> tuple[int, int]:
    """
    Fusiona con lo que ya hay. Devuelve (filas nuevas, total).

    auto_adjust=False a proposito: se guarda el precio SIN ajustar, que es
    el que se opera de verdad. El ajuste por dividendos y splits se aplica
    despues si hace falta, y asi el historico no cambia hacia atras cada
    vez que hay un dividendo.
    """
    DIR_DATOS.mkdir(exist_ok=True)
    f = DIR_DATOS / f"{ticker.replace('-', '_')}.csv"

    if f.exists():
        viejo = pd.read_csv(f, parse_dates=["ts"])
        viejo["ts"] = pd.to_datetime(viejo["ts"], utc=True)
        n_antes = len(viejo)
        junto = pd.concat([viejo, nuevo], ignore_index=True)
    else:
        n_antes = 0
        junto = nuevo.copy()

    junto = (junto.drop_duplicates(subset="ts", keep="last")
                  .sort_values("ts")
                  .reset_index(drop=True))
    junto.to_csv(f, index=False)
    return len(junto) - n_antes, len(junto)


def main() -> int:
    tickers = sys.argv[1:] or TICKERS
    ahora = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"recoleccion {ahora}\n")

    fallos = 0
    resumen = []
    for t in tickers:
        try:
            nuevas, total = acumular(t, descargar(t))
            resumen.append((t, nuevas, total))
            print(f"  {t:9} +{nuevas:>6} nuevas  ->  {total:>8,} barras")
        except Exception as e:
            fallos += 1
            print(f"  {t:9} FALLO: {type(e).__name__} {str(e)[:60]}")

    if resumen:
        dias = []
        for t, _, _ in resumen:
            f = DIR_DATOS / f"{t.replace('-', '_')}.csv"
            d = pd.read_csv(f, usecols=["ts"], parse_dates=["ts"])
            dias.append(d["ts"].dt.date.nunique())
        print(f"\ndias distintos acumulados: min {min(dias)}, max {max(dias)}")
        print("(hacen falten unos 60 dias de mercado para investigar algo)")

    # fallar solo si TODO falla: un ticker deslistado no debe romper el cron
    return 1 if resumen == [] and fallos else 0


if __name__ == "__main__":
    sys.exit(main())
