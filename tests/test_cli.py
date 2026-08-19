import pandas as pd
import psycopg
import pytest

from distancia_ao_default.cli import main


class _TickerFalso:
    def __init__(self, *, precos: list[float], balanco: pd.DataFrame) -> None:
        self.fast_info = {"marketCap": 50_000.0}
        self._precos = precos
        self.balance_sheet = balanco

    def history(self, period: str) -> pd.DataFrame:
        return pd.DataFrame({"Close": self._precos})


def _ticker_valido() -> _TickerFalso:
    precos = [100.0 + (i % 5) for i in range(60)]
    balanco = pd.DataFrame(
        {"2025-12-31": [20_000.0]}, index=["Total Liabilities Net Minority Interest"]
    )
    return _TickerFalso(precos=precos, balanco=balanco)


@pytest.fixture(autouse=True)
def dsn_no_ambiente(monkeypatch: pytest.MonkeyPatch, dsn: str) -> None:
    monkeypatch.setenv("DADOS_MERCADO_PUBLICO_POSTGRES_DSN", dsn)


def _semear_taxa(conexao: psycopg.Connection) -> None:
    conexao.execute(
        """
        INSERT INTO series_vintage
            (fonte, serie, data_evento, data_publicacao, vigente_ate, valor,
             data_disponibilidade)
        VALUES ('fred', 'DGS3MO', CURRENT_DATE, CURRENT_DATE, CURRENT_DATE + 7,
                5.0, CURRENT_DATE)
        """
    )


def test_sem_taxa_ingerida_orienta_e_sai_com_codigo_dois() -> None:
    assert main(["avaliar", "--ticker", "F"]) == 2


def test_avaliar_imprime_os_campos_do_modelo(
    conexao: psycopg.Connection,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _semear_taxa(conexao)
    monkeypatch.setattr(
        "distancia_ao_default.cli.yf.Ticker", lambda _: _ticker_valido()
    )

    codigo = main(["avaliar", "--ticker", "F"])

    saida = capsys.readouterr().out
    assert codigo == 0
    assert "distancia_ao_default" in saida
    assert "pd_implicita" in saida
