"""Interface de linha de comando. A lógica vive no pacote; aqui só coordena."""

import argparse
import sys
from datetime import UTC, datetime

import psycopg
import yfinance as yf

from distancia_ao_default.config import Settings
from distancia_ao_default.fontes.equity import (
    DadoInsuficiente,
    passivo_total,
    valor_de_mercado,
    vol_historica_anualizada,
)
from distancia_ao_default.merton import resolver
from distancia_ao_default.taxa_livre_risco import TaxaIndisponivel, taxa_3_meses


def _argumentos(argv: list[str] | None) -> argparse.Namespace:
    principal = argparse.ArgumentParser(prog="distancia-ao-default")
    comandos = principal.add_subparsers(dest="comando", required=True)

    avaliar = comandos.add_parser("avaliar", help="distância-ao-default de um ticker")
    avaliar.add_argument("--ticker", required=True)

    return principal.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    argumentos = _argumentos(argv)
    config = Settings()
    hoje = datetime.now(UTC).date()

    try:
        with psycopg.connect(config.dados_mercado_publico_dsn) as conexao:
            taxa = taxa_3_meses(conexao, em=hoje)
    except TaxaIndisponivel as erro:
        print(str(erro), file=sys.stderr)
        return 2
    except psycopg.OperationalError as erro:
        print(
            f"não foi possível conectar ao Postgres do dados-mercado-publico: {erro}",
            file=sys.stderr,
        )
        return 2

    ticker = yf.Ticker(argumentos.ticker)
    try:
        equity = valor_de_mercado(ticker=ticker)
        vol_equity = vol_historica_anualizada(ticker=ticker)
        passivo = passivo_total(ticker=ticker)
    except DadoInsuficiente as erro:
        print(f"dado insuficiente para {argumentos.ticker}: {erro}", file=sys.stderr)
        return 2

    resultado = resolver(
        equity=equity, vol_equity=vol_equity, passivo=passivo, taxa=taxa
    )
    if resultado is None:
        print(
            f"o solver de Merton não convergiu para {argumentos.ticker} "
            f"(equity={equity:.0f}, vol_equity={vol_equity:.4f}, "
            f"passivo={passivo:.0f})",
            file=sys.stderr,
        )
        return 1

    print("campo,valor")
    print(f"equity,{equity:.2f}")
    print(f"vol_equity,{vol_equity:.6f}")
    print(f"passivo,{passivo:.2f}")
    print(f"taxa_livre_risco,{taxa:.6f}")
    print(f"valor_ativos,{resultado.valor_ativos:.2f}")
    print(f"vol_ativos,{resultado.vol_ativos:.6f}")
    print(f"distancia_ao_default,{resultado.distancia_ao_default:.4f}")
    print(f"pd_implicita,{resultado.pd_implicita:.6f}")
    return 0
