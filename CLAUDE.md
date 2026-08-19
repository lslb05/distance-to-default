# Contrato do projeto — Distancia Ao Default

Leia o `CLAUDE.md` global e use este arquivo para o que é específico deste
repositório.

## Resultado do produto

- **Problema:** PD de firma pública normalmente é caixa-preta (rating de
  agência) ou classificador estatístico sobre dado tabular de terceiro. O
  modelo estrutural de Merton/KMV — equity como call sobre o valor dos
  ativos da firma — conecta credit risk a option pricing de verdade.
- **Usuário:** eu, e quem revisa o portfólio avaliando para pesquisa
  quantitativa/risco.
- **Saída verificável:** para uma empresa e uma data, distância-ao-default e
  PD implícita (1 ano), via inversão numérica do sistema de Merton (2
  equações não-lineares, 2 incógnitas: valor e vol dos ativos).
- **Fonte de dados permitida:** `yfinance` — preço/vol de equity e
  `Total Liabilities Net Minority Interest` do balanço. Taxa livre de risco:
  FRED `DGS3MO` via Postgres do `dados-mercado-publico`.
- **Menor corte ponta a ponta:** CLI que recebe um ticker e devolve
  distância-ao-default, PD implícita e os inputs usados (valor de equity,
  vol de equity, passivo total, taxa livre de risco).
- **Fora de escopo:** SEC EDGAR, convenção KMV completa para dívida
  (curto prazo + 0.5×longo prazo — este corte usa passivo total), calibração
  contra taxa de default histórica real, carteira multi-emissor.

Não implemente enquanto um `PREENCHER` que altere o design continuar em aberto.

## Comandos

```bash
uv sync
uv run python scripts/format.py
uv run python scripts/check.py
```

## Regras locais

- O pacote é `distancia_ao_default` e vive em `src/distancia_ao_default`.
- Notebook importa de `src/`; código de produção nunca importa notebook.
- Configuração vem de ambiente por `Settings`.
- Preserve dado bruto e metadados temporais quando houver ingestão.
- Atualize este arquivo quando uma decisão estrutural mudar.

## Estilo

Código público, lido por gente. A regra é contenção — a lista completa está em
`AGENTS.md`, seção "Style", e vale igual para mim e para o Codex.

- Comentário explica *por quê*, nunca *o quê*. Se parafraseia a linha abaixo,
  apague; se a linha precisa de paráfrase, renomeie a variável.
- Docstring só onde a assinatura não basta (unidade, fuso, efeito colateral,
  o que levanta). Helper privado de três linhas não leva.
- Teste afirma comportamento que pode quebrar, não constante. Cobertura é
  consequência de testar o que importa, nunca meta a inflar.
- Não capture exceção que não sabe tratar; não abstraia com um único chamador.

## Autoria dos commits

Autor e committer são um só: o dono do repositório. Nenhum `Co-Authored-By:`,
nenhum trailer de sessão, nenhuma menção a Claude, Codex ou ferramenta. Não
altere `user.name` nem `user.email`.

## Estado da sessão

- **Decidido:** primeiro corte entregue — CLI `avaliar --ticker` que resolve
  o sistema de Merton por ponto fixo e devolve distância-ao-default e PD
  implícita. Validado por round-trip sintético (sem gabarito externo
  possível para crédito) e por rodada real contra AAPL/F/AMC — discrimina
  risco de forma plausível (PD ~0% para AAPL, ~14% para AMC).
- **Pendente:** nada bloqueando; próximos cortes são extensões de escopo.
- **Próximo passo:** avaliar se vale trocar passivo total pela convenção
  KMV de dívida (curto prazo + 0,5×longo prazo) ou se calibração contra
  taxa de default histórica real (SEC EDGAR) é o corte mais valioso.

