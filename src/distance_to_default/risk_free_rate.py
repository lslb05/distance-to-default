"""Risk-free rate read from the public-market-data Postgres (DGS3MO series).

Reads through that project's public `series_vintage` interface — same table,
without importing its code. Same pattern used by spx-implied-vol and
inflation-nowcasting.
"""

from datetime import date

import psycopg


class RateUnavailable(Exception):
    """The DGS3MO series has not been ingested into the neighboring Postgres yet."""


def rate_3_months(connection: psycopg.Connection, *, at: date) -> float:
    """Returns the DGS3MO rate (decimal, e.g. 0.0533) as known on `at`."""
    row = connection.execute(
        """
        SELECT valor
        FROM series_vintage
        WHERE fonte = 'fred' AND serie = 'DGS3MO'
          AND data_publicacao <= %s AND vigente_ate >= %s
          AND valor IS NOT NULL
        ORDER BY data_evento DESC
        LIMIT 1
        """,
        (at, at),
    ).fetchone()
    if row is None:
        raise RateUnavailable(
            "DGS3MO series not found in series_vintage; run "
            "'ingest --source fred --series DGS3MO' in dados-mercado-publico"
        )
    return float(row[0]) / 100
