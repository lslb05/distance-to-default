"""Taxa livre de risco lida do Postgres do dados-mercado-publico (série DGS3MO).

Lê pela interface pública `series_vintage` daquele projeto — mesma tabela,
sem importar código de lá. Mesmo padrão do vol-implicita-spx e do
nowcasting-inflacao.
"""

from datetime import date

import psycopg


class TaxaIndisponivel(Exception):
    """A série DGS3MO ainda não foi ingerida no Postgres vizinho."""


def taxa_3_meses(conexao: psycopg.Connection, *, em: date) -> float:
    """Devolve a taxa DGS3MO (decimal, ex.: 0.0533) como era conhecida em `em`."""
    linha = conexao.execute(
        """
        SELECT valor
        FROM series_vintage
        WHERE fonte = 'fred' AND serie = 'DGS3MO'
          AND data_publicacao <= %s AND vigente_ate >= %s
          AND valor IS NOT NULL
        ORDER BY data_evento DESC
        LIMIT 1
        """,
        (em, em),
    ).fetchone()
    if linha is None:
        raise TaxaIndisponivel(
            "série DGS3MO não encontrada em series_vintage; rode "
            "'ingerir --fonte fred --serie DGS3MO' no dados-mercado-publico"
        )
    return float(linha[0]) / 100
