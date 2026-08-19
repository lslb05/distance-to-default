import math

import pytest

from distancia_ao_default.merton import _cdf, _d1_d2, preco_equity, resolver

_TAXA = 0.05
_HORIZONTE = 1.0


def _gerar_equity_e_vol(
    *, valor_ativos: float, vol_ativos: float, passivo: float
) -> tuple[float, float]:
    """Deriva (E, sigma_E) de um (V, sigma_V) conhecido — o problema direto."""
    equity = preco_equity(valor_ativos, passivo, _TAXA, _HORIZONTE, vol_ativos)
    d1, _ = _d1_d2(valor_ativos, passivo, _TAXA, _HORIZONTE, vol_ativos)
    vol_equity = _cdf(d1) * vol_ativos * valor_ativos / equity
    return equity, vol_equity


@pytest.mark.parametrize(
    ("valor_ativos", "vol_ativos", "passivo"),
    [
        (1_000.0, 0.25, 400.0),  # alavancagem moderada
        (1_000.0, 0.15, 150.0),  # baixa alavancagem, baixa vol
        (1_000.0, 0.45, 800.0),  # alta alavancagem, alta vol
    ],
)
def test_solver_recupera_v_e_sigma_v_originais(
    valor_ativos: float, vol_ativos: float, passivo: float
) -> None:
    equity, vol_equity = _gerar_equity_e_vol(
        valor_ativos=valor_ativos, vol_ativos=vol_ativos, passivo=passivo
    )

    resultado = resolver(
        equity=equity, vol_equity=vol_equity, passivo=passivo, taxa=_TAXA
    )

    assert resultado is not None
    assert resultado.valor_ativos == pytest.approx(valor_ativos, rel=1e-4)
    assert resultado.vol_ativos == pytest.approx(vol_ativos, rel=1e-4)


def test_distancia_ao_default_e_pd_sao_consistentes_com_d2() -> None:
    valor_ativos, vol_ativos, passivo = 1_000.0, 0.3, 500.0
    equity, vol_equity = _gerar_equity_e_vol(
        valor_ativos=valor_ativos, vol_ativos=vol_ativos, passivo=passivo
    )

    resultado = resolver(
        equity=equity, vol_equity=vol_equity, passivo=passivo, taxa=_TAXA
    )

    assert resultado is not None
    _, d2_esperado = _d1_d2(valor_ativos, passivo, _TAXA, _HORIZONTE, vol_ativos)
    assert resultado.distancia_ao_default == pytest.approx(d2_esperado, rel=1e-3)
    assert resultado.pd_implicita == pytest.approx(
        0.5 * (1 - math.erf(d2_esperado / math.sqrt(2))), rel=1e-3
    )


def test_alavancagem_maior_produz_pd_maior() -> None:
    baixa_alavancagem, _ = _gerar_equity_e_vol(
        valor_ativos=1_000.0, vol_ativos=0.3, passivo=200.0
    )
    alta_alavancagem, _ = _gerar_equity_e_vol(
        valor_ativos=1_000.0, vol_ativos=0.3, passivo=800.0
    )

    _, vol_baixa = _gerar_equity_e_vol(
        valor_ativos=1_000.0, vol_ativos=0.3, passivo=200.0
    )
    _, vol_alta = _gerar_equity_e_vol(
        valor_ativos=1_000.0, vol_ativos=0.3, passivo=800.0
    )

    resultado_baixa = resolver(
        equity=baixa_alavancagem, vol_equity=vol_baixa, passivo=200.0, taxa=_TAXA
    )
    resultado_alta = resolver(
        equity=alta_alavancagem, vol_equity=vol_alta, passivo=800.0, taxa=_TAXA
    )

    assert resultado_baixa is not None
    assert resultado_alta is not None
    assert resultado_alta.pd_implicita > resultado_baixa.pd_implicita


@pytest.mark.parametrize(
    ("equity", "vol_equity", "passivo"),
    [(0.0, 0.3, 500.0), (1000.0, 0.0, 500.0), (1000.0, 0.3, 0.0)],
)
def test_input_invalido_devolve_none(
    equity: float, vol_equity: float, passivo: float
) -> None:
    assert (
        resolver(equity=equity, vol_equity=vol_equity, passivo=passivo, taxa=_TAXA)
        is None
    )
