"""Acesso a dado de equity via yfinance: valor de mercado, vol e passivo total."""

from __future__ import annotations

import math
from typing import Any, Protocol

_DIAS_UTEIS_ANO = 252
_LINHA_PASSIVO = "Total Liabilities Net Minority Interest"


class DadoInsuficiente(Exception):
    """Faltou histórico de preço ou linha de balanço suficiente."""


class TickerLike(Protocol):
    """O subconjunto de `yfinance.Ticker` usado aqui — injetável em teste."""

    fast_info: Any
    balance_sheet: Any

    def history(self, period: str) -> Any: ...


def valor_de_mercado(*, ticker: TickerLike) -> float:
    """Capitalização de mercado atual — o `E` do modelo de Merton."""
    return float(ticker.fast_info["marketCap"])


def vol_historica_anualizada(*, ticker: TickerLike) -> float:
    """Desvio-padrão anualizado dos log-retornos diários do último ano."""
    fechamentos = ticker.history(period="1y")["Close"]
    log_retornos = fechamentos.apply(math.log).diff().dropna()
    if len(log_retornos) < 2:
        raise DadoInsuficiente("histórico de preço insuficiente pra estimar vol")
    return float(log_retornos.std() * math.sqrt(_DIAS_UTEIS_ANO))


def passivo_total(*, ticker: TickerLike) -> float:
    """`Total Liabilities Net Minority Interest` mais recente do balanço."""
    balanco = ticker.balance_sheet
    if _LINHA_PASSIVO not in balanco.index:
        raise DadoInsuficiente(f"'{_LINHA_PASSIVO}' não encontrado no balanço")
    valores = balanco.loc[_LINHA_PASSIVO].dropna()
    if valores.empty:
        raise DadoInsuficiente(f"'{_LINHA_PASSIVO}' sem valor não-nulo no balanço")
    return float(valores.iloc[0])
