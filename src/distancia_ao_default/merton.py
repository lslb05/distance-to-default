"""Modelo estrutural de Merton: distância-ao-default por iteração de ponto fixo.

O equity é uma call sobre o valor dos ativos da firma (Black-Scholes-Merton).
Duas equações, duas incógnitas (valor e vol dos ativos), sem solução fechada:

    E = V * N(d1) - D * exp(-r*T) * N(d2)
    sigma_E * E = N(d1) * sigma_V * V

Resolve pela iteração clássica (Vassalou-Xing / KMV): fixado sigma_V, acha o
V que precifica o equity certo (root-finding 1D por bisseção); daí atualiza
sigma_V pela segunda equação; repete até os dois pararem de mudar.
"""

import math
from dataclasses import dataclass

_TOLERANCIA_RELATIVA = 1e-8
_MAX_ITERACOES_EXTERNAS = 100
_MAX_ITERACOES_INTERNAS = 100
_LIMITE_INFERIOR_V = 1e-6
_MULTIPLICADOR_LIMITE_SUPERIOR = 50.0


def _cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _d1_d2(
    v: float, passivo: float, taxa: float, horizonte: float, sigma_v: float
) -> tuple[float, float]:
    d1 = (math.log(v / passivo) + (taxa + 0.5 * sigma_v * sigma_v) * horizonte) / (
        sigma_v * math.sqrt(horizonte)
    )
    return d1, d1 - sigma_v * math.sqrt(horizonte)


def preco_equity(
    v: float, passivo: float, taxa: float, horizonte: float, sigma_v: float
) -> float:
    """Valor do equity como call europeia sobre os ativos, strike = passivo."""
    d1, d2 = _d1_d2(v, passivo, taxa, horizonte, sigma_v)
    return v * _cdf(d1) - passivo * math.exp(-taxa * horizonte) * _cdf(d2)


@dataclass(frozen=True)
class Merton:
    valor_ativos: float
    vol_ativos: float
    distancia_ao_default: float
    pd_implicita: float


def resolver(
    *,
    equity: float,
    vol_equity: float,
    passivo: float,
    taxa: float,
    horizonte: float = 1.0,
) -> Merton | None:
    """Resolve o sistema de Merton. `None` se não convergir.

    Alavancagem ou vol de equity extremas podem não ter ponto fixo estável
    dentro do limite de iterações — melhor reportar isso do que devolver um
    número que só pareceu ter convergido.
    """
    if equity <= 0 or vol_equity <= 0 or passivo <= 0 or horizonte <= 0:
        return None

    v = equity + passivo
    sigma_v = vol_equity * equity / v

    for _ in range(_MAX_ITERACOES_EXTERNAS):
        v_novo = _resolver_v(equity, passivo, taxa, horizonte, sigma_v)
        if v_novo is None:
            return None

        d1, _ = _d1_d2(v_novo, passivo, taxa, horizonte, sigma_v)
        densidade_d1 = _cdf(d1)
        if densidade_d1 < 1e-12:
            return None
        sigma_v_novo = vol_equity * equity / (densidade_d1 * v_novo)

        convergiu = (
            abs(v_novo - v) < _TOLERANCIA_RELATIVA * v_novo
            and abs(sigma_v_novo - sigma_v) < _TOLERANCIA_RELATIVA
        )
        v, sigma_v = v_novo, sigma_v_novo
        if convergiu:
            break
    else:
        return None

    _, d2 = _d1_d2(v, passivo, taxa, horizonte, sigma_v)
    return Merton(
        valor_ativos=v,
        vol_ativos=sigma_v,
        distancia_ao_default=d2,
        pd_implicita=_cdf(-d2),
    )


def _resolver_v(
    equity: float, passivo: float, taxa: float, horizonte: float, sigma_v: float
) -> float | None:
    """V que precifica o equity corretamente, para um `sigma_v` fixo — bisseção."""
    baixo = _LIMITE_INFERIOR_V
    alto = (equity + passivo) * _MULTIPLICADOR_LIMITE_SUPERIOR
    f_baixo = preco_equity(baixo, passivo, taxa, horizonte, sigma_v) - equity
    f_alto = preco_equity(alto, passivo, taxa, horizonte, sigma_v) - equity
    if f_baixo * f_alto > 0:
        return None

    meio = baixo
    tolerancia_absoluta = _TOLERANCIA_RELATIVA * max(equity, 1.0)
    for _ in range(_MAX_ITERACOES_INTERNAS):
        meio = (baixo + alto) / 2
        f_meio = preco_equity(meio, passivo, taxa, horizonte, sigma_v) - equity
        if abs(f_meio) < tolerancia_absoluta:
            return meio
        if f_baixo * f_meio < 0:
            alto = meio
        else:
            baixo, f_baixo = meio, f_meio
    return meio
