# distancia-ao-default

Distância-ao-default e PD implícita (1 ano) de uma firma pública, via modelo
estrutural de Merton — o equity tratado como uma call sobre o valor dos
ativos da firma, exatamente como uma opção.

## O problema

Rating de agência é caixa-preta e atualiza devagar. Um classificador
estatístico genérico sobre dado tabular de terceiro nem sempre generaliza
pra firma real. O modelo de Merton (base do KMV, usado por mesa de risco de
crédito de verdade) faz outra coisa: deriva probabilidade de default da
estrutura de capital e da vol de mercado do próprio equity — dado que
qualquer firma pública já disponibiliza.

## Resultado

```console
$ uv run python -m distancia_ao_default avaliar --ticker F
campo,valor
equity,57800198736.82
vol_equity,0.373805
passivo,253180000000.00
taxa_livre_risco,0.051000
valor_ativos,298383480893.35
vol_ativos,0.072506
distancia_ao_default,2.9329
pd_implicita,0.001679

$ uv run python -m distancia_ao_default avaliar --ticker AAPL | grep -E 'distancia|pd_'
distancia_ao_default,12.0741
pd_implicita,0.000000

$ uv run python -m distancia_ao_default avaliar --ticker AMC | grep -E 'distancia|pd_'
distancia_ao_default,1.0737
pd_implicita,0.141483
```

Três tickers reais, rodados de verdade: Apple (baixa alavancagem relativa ao
market cap) fica com distância-ao-default alta e PD ~0%; Ford (alavancagem
pesada, braço de financiamento próprio) fica no meio; AMC (historicamente
estressada) fica com distância abaixo de 1,1 desvio-padrão e PD de ~14% em
um ano. O modelo discrimina risco de crédito em nomes conhecidos sem ter
visto rating nenhum.

## Problema e escopo

- **Usuário:** eu, e quem revisa o portfólio avaliando para pesquisa
  quantitativa/risco.
- **Decisão:** dá pra estimar PD estrutural de qualquer firma pública com
  ação líquida, sem dado institucional.
- **Entrada:** `yfinance` — capitalização de mercado, histórico de preço
  (vol anualizada) e `Total Liabilities Net Minority Interest` do balanço.
  Taxa livre de risco: FRED `DGS3MO` via Postgres do
  [`dados-mercado-publico`](../dados-mercado-publico).
- **Fora de escopo:** SEC EDGAR, convenção KMV completa de dívida (curto
  prazo + 0,5×longo prazo — este corte usa passivo total), calibração
  contra taxa de default histórica real, carteira multi-emissor.

## Arquitetura

```
yfinance                          Postgres (dados-mercado-publico)
    │  equity, vol, passivo            │  DGS3MO via series_vintage
    ▼                                  ▼
fontes/equity.py                 taxa_livre_risco.py
    │                                  │
    └──────────────┬───────────────────┘
                    ▼
               merton.py          resolve o sistema de 2 equações,
                    │              2 incógnitas por ponto fixo
                    ▼
                 cli.py            distância-ao-default, PD
```

Duas decisões que valem explicação:

**Ponto fixo, não Newton multivariado.** O sistema de Merton é 2 equações e
2 incógnitas (valor e vol dos ativos), mas resolver por Newton bidimensional
exige montar e invertir um Jacobiano 2×2 numericamente — mais código, mais
jeito de errar sinal ou derivada parcial. A iteração de ponto fixo
(Vassalou-Xing/KMV) desacopla: fixa `sigma_V`, acha `V` por bisseção 1D
(reaproveitando a mesma disciplina do `vol-implicita-spx`), atualiza
`sigma_V` pela segunda equação, repete. Mais lenta, mais simples de
verificar linha por linha.

**Sem gabarito externo — a verificação é round-trip sintético.** Não existe
"IV da Yahoo" pra crédito: nenhuma fonte pública publica a PD estrutural de
uma firma pra comparar. `tests/test_merton.py` gera `E` e `sigma_E` a partir
de um `(V, sigma_V)` escolhido (o problema direto, que tem forma fechada),
roda o solver de volta, e confirma que ele recupera o par original — a
mesma disciplina de precisão numérica, aplicada ao problema inverso.

## Executar localmente

Requisitos: Python 3.12, `uv`, Docker (para o Postgres efêmero dos testes),
e o [`dados-mercado-publico`](../dados-mercado-publico) rodando com a
série `DGS3MO` ingerida:

```bash
# no dados-mercado-publico:
docker compose up -d
uv run python -m dados_mercado_publico ingerir --fonte fred --serie DGS3MO
```

```bash
uv sync
cp .env.example .env
uv run python -m distancia_ao_default avaliar --ticker AAPL
```

Sem a série `DGS3MO` ingerida, o comando orienta e sai com código 2. Se o
solver não convergir para uma firma com alavancagem/vol extrema, sai com
código 1 e mostra os inputs usados, em vez de devolver um número ruim.

## Qualidade

```bash
uv run python scripts/check.py
```

O check executa formatação, lint, tipos e testes com cobertura. É o mesmo
comando que o CI roda, em Windows, Linux e macOS.

## Estrutura

```text
src/distancia_ao_default/
    merton.py            sistema de Merton e o solver de ponto fixo
    fontes/equity.py      adaptador yfinance, testável com um ticker falso
    taxa_livre_risco.py   leitura da interface pública do dados-mercado-publico
    cli.py                  coordenação
```

## Limitações

- Passivo total do balanço mais recente, não a convenção KMV completa
  (curto prazo + metade do longo prazo) — superestima a dívida "efetiva"
  para firma com dívida de longo prazo relevante.
- Vol de equity histórica (log-retorno de 1 ano), não implícita — mistura
  regime de vol passado com a estrutura de capital atual.
- Sem calibração: a PD implícita não foi comparada contra taxa de default
  histórica real de nenhuma classe de rating. O valor é direcional
  (discrimina risco relativo entre firmas), não uma probabilidade calibrada.

## Licença

MIT. Dados de terceiros mantêm suas próprias licenças e termos de uso.
