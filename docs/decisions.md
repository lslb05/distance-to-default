# Decisões

Registre somente decisões que alterem custo de mudança futuro.

## Modelo

### AAAA-MM-DD — Título

- **Contexto:** qual restrição ou problema exigiu decisão.
- **Decisão:** o caminho escolhido.
- **Alternativas:** opções relevantes descartadas.
- **Consequências:** ganhos, custos e gatilho para revisar.

### 2026-08-18 — Manter `CLAUDE.md` e `AGENTS.md` no repositório público

- **Contexto:** os dois arquivos declaram que o repositório é construído com
  apoio de agentes. A alternativa era ignorá-los no git para que o repositório
  público não revelasse o fluxo de trabalho.
- **Decisão:** manter os dois versionados e públicos.
- **Alternativas:** ignorar `AGENTS.md` no `.gitignore`; mantê-lo apenas local.
  Ambas quebram a delegação ao Codex, que lê esse arquivo do repositório — o
  custo é funcional e imediato, o ganho é cosmético.
- **Consequências:** o repositório declara o método em vez de escondê-lo, o que
  também é verificável por quem lê. Rever se algum destino exigir o contrário.

### 2026-08-19 — Ponto fixo (Vassalou-Xing) em vez de Newton multivariado

- **Contexto:** o sistema de Merton tem 2 equações e 2 incógnitas
  (`V`, `sigma_V`), sem solução fechada. Newton multivariado converge mais
  rápido, mas exige montar e resolver um Jacobiano 2×2 a cada iteração.
- **Decisão:** iteração de ponto fixo — fixa `sigma_V`, resolve `V` por
  bisseção 1D (equação de precificação), atualiza `sigma_V` pela segunda
  equação, repete até os dois convergirem.
- **Alternativas:** Newton multivariado — mais rápido (poucas iterações),
  mas o Jacobiano dessas duas equações não é trivial de derivar sem erro de
  sinal, e o ganho de velocidade não importa para um CLI que roda uma vez
  por ticker.
- **Consequências:** mais iterações externas (dezenas, não poucas), mas
  cada peça é verificável isoladamente — o `_resolver_v` interno é o mesmo
  tipo de root-finding 1D já usado em outro projeto do portfólio. Rever se
  este projeto algum dia precisar avaliar uma carteira inteira e a
  velocidade virar gargalo real.

### 2026-08-19 — Passivo total do balanço, não a convenção KMV de dívida

- **Contexto:** o KMV clássico usa "ponto de default" = dívida de curto
  prazo + metade da dívida de longo prazo, não o passivo total do balanço.
  Replicar isso exige separar as linhas de dívida de curto e longo prazo do
  `yfinance`, que nem sempre vêm decompostas de forma limpa para toda firma.
- **Decisão:** usar `Total Liabilities Net Minority Interest` como o `D` do
  modelo — mais simples de extrair de forma confiável para qualquer ticker.
- **Alternativas:** convenção KMV completa — mais fiel à literatura, mas
  adiciona uma segunda extração de balanço com mais chance de dado ausente
  por firma, num corte que já tem risco técnico suficiente no solver.
- **Consequências:** o passivo total superestima o "ponto de default" para
  firma com muita dívida de longo prazo — a PD implícita fica
  conservadora (mais alta) nesses casos, documentado no README, não
  escondido. Rever se um corte futuro precisar de PD calibrada, não só
  comparável entre firmas.
