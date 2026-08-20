import pandas as pd
import psycopg
import pytest

from distance_to_default.cli import main


class _FakeTicker:
    def __init__(self, *, prices: list[float], balance_sheet: pd.DataFrame) -> None:
        self.fast_info = {"marketCap": 50_000.0}
        self._prices = prices
        self.balance_sheet = balance_sheet

    def history(self, period: str) -> pd.DataFrame:
        return pd.DataFrame({"Close": self._prices})


def _valid_ticker() -> _FakeTicker:
    prices = [100.0 + (i % 5) for i in range(60)]
    balance_sheet = pd.DataFrame(
        {"2025-12-31": [20_000.0]}, index=["Total Liabilities Net Minority Interest"]
    )
    return _FakeTicker(prices=prices, balance_sheet=balance_sheet)


@pytest.fixture(autouse=True)
def dsn_in_environment(monkeypatch: pytest.MonkeyPatch, dsn: str) -> None:
    monkeypatch.setenv("DADOS_MERCADO_PUBLICO_POSTGRES_DSN", dsn)


def _seed_rate(connection: psycopg.Connection) -> None:
    connection.execute(
        """
        INSERT INTO series_vintage
            (fonte, serie, data_evento, data_publicacao, vigente_ate, valor,
             data_disponibilidade)
        VALUES ('fred', 'DGS3MO', CURRENT_DATE, CURRENT_DATE, CURRENT_DATE + 7,
                5.0, CURRENT_DATE)
        """
    )


def test_missing_rate_guides_and_exits_with_code_two() -> None:
    assert main(["evaluate", "--ticker", "F"]) == 2


def test_evaluate_prints_the_model_fields(
    connection: psycopg.Connection,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed_rate(connection)
    monkeypatch.setattr("distance_to_default.cli.yf.Ticker", lambda _: _valid_ticker())

    code = main(["evaluate", "--ticker", "F"])

    output = capsys.readouterr().out
    assert code == 0
    assert "distance_to_default" in output
    assert "implied_pd" in output
