# CHECKPOINT - Lobinho-BET
**Data:** 2026-02-19
**Status:** ~60-70% completo - modelos estatisticos funcionam, ML nao treinado, Neo4j placeholder, bugs de integracao

---

## O QUE E O PROJETO
Sistema automatizado de analise de apostas esportivas focado em futebol. Coleta dados em tempo real de multiplas fontes, aplica modelos estatisticos e ML para prever resultados, detecta "value bets" (EV positivo), e envia alertas via Telegram.

**Tech Stack:** Python 3.10+, FastAPI, httpx, aiohttp, BeautifulSoup4, Playwright, SQLAlchemy 2.0 async + PostgreSQL (asyncpg) + SQLite fallback, Neo4j 5.x, Redis 5.x, scikit-learn, XGBoost, LightGBM, APScheduler, python-telegram-bot, Docker Compose

---

## O QUE FUNCIONA
### Coleta de Dados
- FootyStats API: matches, team stats, H2H, league table, Over/Under, BTTS
- The Odds API: odds real-time de 40+ bookmakers, best-odds, margin calculator
- FBref scraper: xG/xGA data
- Transfermarkt scraper: squad value, transfers, injuries (Playwright + httpx+BS4)
- Betista.com scraper: Playwright full flow
- LiveStatsMonitor: polls FootyStats cada 30s para dados live

### Modelos Estatisticos (todos implementados)
- Markov Chain predictor: matrizes transicao, steady-state, H2H weighting
- Poisson predictor: expected goals, score exato, Over/Under, BTTS
- ELO rating system: ratings, home advantage, margin factor
- Monte Carlo simulator: N=5000-10000 simulacoes por jogo
- Ensemble predictor: Markov(0.20) + Poisson(0.25) + ELO(0.25) + MC(0.15) + Graph placeholder(0.15)
- Dixon-Coles model: tau correction, time decay, MLE optimization
- Bradley-Terry model: pairwise comparison, MM algorithm
- Bayesian predictor: Beta distribution, credibility intervals
- ScientificEnsemble: weight optimization via grid search
- XGBoost/RF ML predictor: 21 features (mas NAO TREINADO)

### Value Bet Detection
- Edge calculation: `(prob * odds - 1) * 100`
- Kelly Criterion (fracionario, 1/4 Kelly)
- Expected Value calculation
- Confidence tiering: low/medium/high

### Live Market Analyzer
- 20+ tipos de mercado analisados
- Weighted scoring: time + pressure + recent events + odds movement + history
- Odds trend detection (STEAM/FALLING/STABLE/RISING)

### Database Layer
- SQLAlchemy async models completos: Leagues, Teams, Players, Matches, etc
- Repository pattern + Unit of Work
- Alembic migration (schema inicial completo)

### Notificacoes
- Telegram bot: /start, /status, /bets, /live, /leagues, /help
- Alertas formatados com emoji tiers

### Orquestracao
- APScheduler: coleta diaria 06:00, analise 08:00, odds updates 30min, live check 5min
- 15 ligas configuradas (Brasil + Europa)

### Estatisticas Avancadas
- Model calibration: Brier score, Log Loss, ECE
- Dynamic Kelly com protecao drawdown
- Backtesting framework com Sharpe ratio, max drawdown

---

## O QUE FALTA
1. **ML Model NAO TREINADO** - predictor.pkl nao existe. XGBoost raises RuntimeError("Model not trained"). Pipeline de predicao principal falha
2. **Neo4j placeholder** - EnsemblePredictor hardcoda graph prediction: `{"home_win": 0.40, "draw": 0.28, "away_win": 0.32}`. graph_db.py so tem skeleton
3. **Stats Analysis comentada** - home_stats = {} # await collector.get_team_stats(home_id) - analise vazia
4. **Live Odds nao implementado** - `_update_live_odds()` e um no-op (pass)
5. **Telegram Bot commands stubs** - /bets e /live retornam texto placeholder
6. **Sem Dockerfile** - Docker Compose existe mas container app comentado
7. **Sem .env** - so .env.example existe
8. **dashboard_local.py 129KB** - monolito massivo, provavelmente duplica funcionalidade

---

## BUGS
1. **CRITICO: sync function chama async context manager** - `_match_odds_to_game()` e `def` (sync) mas usa `async with OddsAPICollector()`. CRASHA com TypeError
2. **XGBoost deprecated parameter** - `use_label_encoder=False` removido em XGBoost 2.0.3. Erro ao treinar
3. **Testes referenciam API inexistente** - test_models.py chama `predictor._form_to_states()`, `_calculate_transition_matrix()` que nao existem. Todos testes FALHAM
4. **data_service.py import errado** - `from src.core.config import get_settings` mas modulo e `config.settings`. Tambem usa Session sync com repos async
5. **TransfermarktScraper recebe URL em vez de team_name** - team_analysis.py passa URL mas get_team_data espera nome. Retorna None
6. **FBref chamado com int ID** - orchestrator passa league_id int mas FBref espera string key. ValueError
7. **numpy.math deprecated** - test_models.py usa np.math.factorial (removido no NumPy 2.0)
8. **OddsAPICollector.get_team_stats() sempre raises** - NotImplementedError
9. **_match_odds_to_game() match por substring fragil** - "City" match "Manchester City" E "Leicester City"
10. **BankrollRepository.record() ROI incorreto** - `profit / (total_bets * 10)` formula errada

---

## DEPENDENCIAS PRINCIPAIS
fastapi 0.109, uvicorn 0.27, httpx 0.26, aiohttp 3.9.1, beautifulsoup4 4.12.2, playwright 1.41, sqlalchemy 2.0.25, asyncpg 0.29, redis 5.0.1, neo4j 5.15, pandas 2.1.4, numpy 1.26.3, scikit-learn 1.4, xgboost 2.0.3, lightgbm 4.2, python-telegram-bot 20.7, apscheduler 3.10.4, alembic 1.13.1

**Nunca usados:** lightgbm, celery, discord.py, anthropic, websockets, aiohttp (so httpx usado)

---

## DEAD CODE
- lightgbm em requirements.txt (nao importado)
- celery em requirements.txt (APScheduler usado)
- discord.py em requirements.txt (nenhuma integracao Discord)
- anthropic em requirements.txt (nenhuma chamada Claude)
- dashboard_local.py (129KB, provavelmente duplica src/api/dashboard.py)

---

## .md PARA DELETAR
- README.md (32 bytes, so titulo garbled UTF-16 BOM. Substituir por documentacao real)
