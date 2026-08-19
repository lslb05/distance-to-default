import math

import pandas as pd
import pytest

from distancia_ao_default.fontes.equity import (
    DadoInsuficiente,
    passivo_total,
    valor_de_mercado,
    vol_historica_anualizada,
)


class _TickerFalso:
    def __init__(
        self,
        *,
        market_cap: float = 1.0,
        precos: list[float] | None = None,
        balanco: pd.DataFrame | None = None,
    ) -> None:
        self.fast_info = {"marketCap": market_cap}
        self._precos = precos or []
        self.balance_sheet = balanco if balanco is not None else pd.DataFrame()

    def history(self, period: str) -> pd.DataFrame:
        return pd.DataFrame({"Close": self._precos})


def test_valor_de_mercado_le_o_market_cap() -> None:
    ticker = _TickerFalso(market_cap=57_800_198_736.82)

    assert valor_de_mercado(ticker=ticker) == pytest.approx(57_800_198_736.82)


def test_vol_historica_de_serie_constante_e_zero() -> None:
    ticker = _TickerFalso(precos=[100.0] * 30)

    assert vol_historica_anualizada(ticker=ticker) == pytest.approx(0.0, abs=1e-9)


def test_vol_historica_recupera_vol_conhecida_de_serie_sintetica() -> None:
    # Log-retorno diário constante de 1% em módulo, alternando sinal — desvio
    # padrão amostral é exatamente 0.01 antes de anualizar.
    precos = [100.0]
    for i in range(60):
        retorno = 0.01 if i % 2 == 0 else -0.01
        precos.append(precos[-1] * math.exp(retorno))
    ticker = _TickerFalso(precos=precos)

    resultado = vol_historica_anualizada(ticker=ticker)

    assert resultado == pytest.approx(0.01 * math.sqrt(252), rel=2e-2)


def test_vol_historica_com_poucos_precos_levanta_erro() -> None:
    ticker = _TickerFalso(precos=[100.0])

    with pytest.raises(DadoInsuficiente):
        vol_historica_anualizada(ticker=ticker)


def test_passivo_total_pega_a_coluna_mais_recente() -> None:
    balanco = pd.DataFrame(
        {"2025-12-31": [253_180.0], "2024-12-31": [240_000.0]},
        index=["Total Liabilities Net Minority Interest"],
    )
    ticker = _TickerFalso(balanco=balanco)

    assert passivo_total(ticker=ticker) == pytest.approx(253_180.0)


def test_passivo_total_sem_a_linha_levanta_erro() -> None:
    balanco = pd.DataFrame({"2025-12-31": [1.0]}, index=["Outra Linha"])
    ticker = _TickerFalso(balanco=balanco)

    with pytest.raises(DadoInsuficiente):
        passivo_total(ticker=ticker)
