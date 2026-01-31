"""
Dashboard Web - LOBINHO-BET
===========================
Interface web ao vivo para acompanhamento de apostas.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from datetime import datetime
from typing import Optional
from loguru import logger

from src.models.markov_predictor import MarkovPredictor, get_markov_rankings
from src.models.value_detector import ValueDetector
from src.strategy.bookmakers import BookmakerManager, BOOKMAKERS
from src.strategy.event_filter import EventFilter
from src.collectors.live_stats import LiveMatchStats

app = FastAPI(title="LOBINHO-BET Dashboard", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connections
active_connections: list[WebSocket] = []

# State
current_events: list[dict] = []
live_matches: list[dict] = []


# ============================================================================
# HTML TEMPLATE
# ============================================================================

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🐺 LOBINHO-BET - Dashboard</title>
    <style>
        :root {
            --bg-dark: #0f1419;
            --bg-card: #1a1f26;
            --bg-card-hover: #242c36;
            --text-primary: #ffffff;
            --text-secondary: #8899a6;
            --accent-green: #17bf63;
            --accent-red: #e0245e;
            --accent-yellow: #ffad1f;
            --accent-blue: #1da1f2;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-dark);
            color: var(--text-primary);
            min-height: 100vh;
        }

        .header {
            background: linear-gradient(135deg, #1a1f26 0%, #0f1419 100%);
            padding: 20px;
            border-bottom: 1px solid #2d3741;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .header h1 {
            font-size: 24px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .header-stats {
            display: flex;
            gap: 30px;
            margin-top: 15px;
        }

        .stat-box {
            background: var(--bg-card);
            padding: 10px 20px;
            border-radius: 8px;
            text-align: center;
        }

        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: var(--accent-green);
        }

        .stat-label {
            font-size: 12px;
            color: var(--text-secondary);
        }

        .main-content {
            display: grid;
            grid-template-columns: 1fr 350px;
            gap: 20px;
            padding: 20px;
            max-width: 1600px;
            margin: 0 auto;
        }

        .events-section {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 20px;
        }

        .section-title {
            font-size: 18px;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .event-card {
            background: var(--bg-dark);
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
            border-left: 4px solid var(--accent-blue);
            transition: all 0.2s;
        }

        .event-card:hover {
            background: var(--bg-card-hover);
            transform: translateX(5px);
        }

        .event-card.strong-buy {
            border-left-color: var(--accent-green);
        }

        .event-card.live {
            border-left-color: var(--accent-red);
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.8; }
        }

        .event-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        .event-teams {
            font-size: 16px;
            font-weight: 600;
        }

        .event-league {
            font-size: 12px;
            color: var(--text-secondary);
        }

        .event-time {
            font-size: 12px;
            color: var(--accent-yellow);
        }

        .event-odds {
            display: flex;
            gap: 10px;
            margin: 10px 0;
        }

        .odd-box {
            background: var(--bg-card);
            padding: 8px 12px;
            border-radius: 6px;
            text-align: center;
            flex: 1;
            cursor: pointer;
            transition: all 0.2s;
        }

        .odd-box:hover {
            background: var(--accent-blue);
        }

        .odd-box.best {
            border: 1px solid var(--accent-green);
        }

        .odd-value {
            font-size: 18px;
            font-weight: bold;
        }

        .odd-label {
            font-size: 10px;
            color: var(--text-secondary);
        }

        .event-analysis {
            display: flex;
            gap: 15px;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #2d3741;
        }

        .analysis-item {
            font-size: 12px;
        }

        .analysis-item span {
            color: var(--text-secondary);
        }

        .signal-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
        }

        .signal-badge.strong-buy {
            background: var(--accent-green);
            color: #000;
        }

        .signal-badge.buy {
            background: var(--accent-blue);
        }

        .signal-badge.hold {
            background: var(--accent-yellow);
            color: #000;
        }

        .bookmakers-list {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-top: 10px;
        }

        .bookmaker-btn {
            background: var(--bg-card);
            border: 1px solid #2d3741;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 12px;
            color: var(--text-primary);
            text-decoration: none;
            transition: all 0.2s;
        }

        .bookmaker-btn:hover {
            background: var(--accent-green);
            color: #000;
            border-color: var(--accent-green);
        }

        .sidebar {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .sidebar-card {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 15px;
        }

        .live-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
            color: var(--accent-red);
            font-weight: bold;
        }

        .live-dot {
            width: 10px;
            height: 10px;
            background: var(--accent-red);
            border-radius: 50%;
            animation: blink 1s infinite;
        }

        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }

        .live-match {
            padding: 10px;
            background: var(--bg-dark);
            border-radius: 8px;
            margin-top: 10px;
        }

        .live-score {
            font-size: 24px;
            font-weight: bold;
            text-align: center;
            margin: 10px 0;
        }

        .live-stats {
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            gap: 5px;
            font-size: 12px;
        }

        .live-stats .label {
            text-align: center;
            color: var(--text-secondary);
        }

        .momentum-bar {
            height: 8px;
            background: #2d3741;
            border-radius: 4px;
            margin-top: 10px;
            overflow: hidden;
        }

        .momentum-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--accent-red), var(--accent-green));
            transition: width 0.5s;
        }

        .filters {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }

        .filter-btn {
            background: var(--bg-dark);
            border: 1px solid #2d3741;
            padding: 8px 16px;
            border-radius: 20px;
            color: var(--text-primary);
            cursor: pointer;
            transition: all 0.2s;
        }

        .filter-btn:hover, .filter-btn.active {
            background: var(--accent-blue);
            border-color: var(--accent-blue);
        }

        .markov-indicator {
            display: flex;
            align-items: center;
            gap: 5px;
            font-size: 11px;
            color: var(--accent-green);
        }

        .confidence-bar {
            width: 60px;
            height: 4px;
            background: #2d3741;
            border-radius: 2px;
            overflow: hidden;
        }

        .confidence-fill {
            height: 100%;
            background: var(--accent-green);
        }

        @media (max-width: 1024px) {
            .main-content {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <header class="header">
        <h1>🐺 LOBINHO-BET <span style="font-size: 14px; color: var(--text-secondary);">Dashboard Ao Vivo</span></h1>
        <div class="header-stats">
            <div class="stat-box">
                <div class="stat-value" id="total-events">0</div>
                <div class="stat-label">Eventos Analisados</div>
            </div>
            <div class="stat-box">
                <div class="stat-value" id="value-bets" style="color: var(--accent-green);">0</div>
                <div class="stat-label">Value Bets</div>
            </div>
            <div class="stat-box">
                <div class="stat-value" id="live-count" style="color: var(--accent-red);">0</div>
                <div class="stat-label">Jogos Ao Vivo</div>
            </div>
            <div class="stat-box">
                <div class="stat-value" id="last-update">--:--</div>
                <div class="stat-label">Última Atualização</div>
            </div>
        </div>
    </header>

    <main class="main-content">
        <section class="events-section">
            <h2 class="section-title">
                🎯 Melhores Eventos (Ranking Markov)
                <span class="markov-indicator">
                    <span>📊 Precisão:</span>
                    <div class="confidence-bar"><div class="confidence-fill" style="width: 85%;"></div></div>
                    85%
                </span>
            </h2>

            <div class="filters">
                <button class="filter-btn active" data-filter="all">Todos</button>
                <button class="filter-btn" data-filter="strong">🔥 Strong Buy</button>
                <button class="filter-btn" data-filter="live">🔴 Ao Vivo</button>
                <button class="filter-btn" data-filter="brazil">🇧🇷 Brasil</button>
                <button class="filter-btn" data-filter="europe">🇪🇺 Europa</button>
            </div>

            <div id="events-list">
                <!-- Events will be inserted here -->
                <div class="loading">Carregando eventos...</div>
            </div>
        </section>

        <aside class="sidebar">
            <div class="sidebar-card">
                <h3 class="section-title">
                    <span class="live-indicator">
                        <span class="live-dot"></span>
                        Jogos Ao Vivo
                    </span>
                </h3>
                <div id="live-matches">
                    <p style="color: var(--text-secondary); font-size: 14px;">
                        Nenhum jogo ao vivo no momento
                    </p>
                </div>
            </div>

            <div class="sidebar-card">
                <h3 class="section-title">🏦 Casas de Apostas</h3>
                <div class="bookmakers-list" id="bookmakers-list">
                    <!-- Bookmakers will be inserted here -->
                </div>
            </div>

            <div class="sidebar-card">
                <h3 class="section-title">📊 Estatísticas do Dia</h3>
                <div style="font-size: 14px; color: var(--text-secondary);">
                    <p>✅ Acertos: <span style="color: var(--accent-green);">--</span></p>
                    <p>❌ Erros: <span style="color: var(--accent-red);">--</span></p>
                    <p>📈 ROI: <span style="color: var(--accent-green);">--</span></p>
                </div>
            </div>
        </aside>
    </main>

    <script>
        // WebSocket connection
        let ws;
        let reconnectInterval = 5000;

        function connect() {
            ws = new WebSocket(`ws://${window.location.host}/ws`);

            ws.onopen = () => {
                console.log('Connected to WebSocket');
                document.getElementById('last-update').textContent = 'Conectado';
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                updateDashboard(data);
            };

            ws.onclose = () => {
                console.log('WebSocket closed, reconnecting...');
                document.getElementById('last-update').textContent = 'Reconectando...';
                setTimeout(connect, reconnectInterval);
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        }

        function updateDashboard(data) {
            // Update stats
            document.getElementById('total-events').textContent = data.total_events || 0;
            document.getElementById('value-bets').textContent = data.value_bets_count || 0;
            document.getElementById('live-count').textContent = data.live_count || 0;
            document.getElementById('last-update').textContent = new Date().toLocaleTimeString('pt-BR');

            // Update events list
            if (data.events) {
                renderEvents(data.events);
            }

            // Update live matches
            if (data.live_matches) {
                renderLiveMatches(data.live_matches);
            }

            // Update bookmakers
            if (data.bookmakers) {
                renderBookmakers(data.bookmakers);
            }
        }

        function renderEvents(events) {
            const container = document.getElementById('events-list');

            if (!events.length) {
                container.innerHTML = '<p style="color: var(--text-secondary);">Nenhum evento encontrado</p>';
                return;
            }

            container.innerHTML = events.map((event, index) => `
                <div class="event-card ${event.signal === 'strong_buy' ? 'strong-buy' : ''} ${event.is_live ? 'live' : ''}">
                    <div class="event-header">
                        <div>
                            <div class="event-teams">${event.home_team} vs ${event.away_team}</div>
                            <div class="event-league">${event.league}</div>
                        </div>
                        <div style="text-align: right;">
                            <div class="event-time">${event.is_live ? '🔴 AO VIVO' : event.kickoff}</div>
                            <span class="signal-badge ${event.signal}">${getSignalLabel(event.signal)}</span>
                        </div>
                    </div>

                    <div class="event-odds">
                        <div class="odd-box ${event.best_market === 'home' ? 'best' : ''}" onclick="openBet('${event.match_id}', 'home')">
                            <div class="odd-value">${event.odds?.home?.toFixed(2) || '-'}</div>
                            <div class="odd-label">Casa</div>
                        </div>
                        <div class="odd-box ${event.best_market === 'draw' ? 'best' : ''}" onclick="openBet('${event.match_id}', 'draw')">
                            <div class="odd-value">${event.odds?.draw?.toFixed(2) || '-'}</div>
                            <div class="odd-label">Empate</div>
                        </div>
                        <div class="odd-box ${event.best_market === 'away' ? 'best' : ''}" onclick="openBet('${event.match_id}', 'away')">
                            <div class="odd-value">${event.odds?.away?.toFixed(2) || '-'}</div>
                            <div class="odd-label">Fora</div>
                        </div>
                    </div>

                    <div class="event-analysis">
                        <div class="analysis-item">
                            <span>📊 Markov:</span> ${(event.markov_confidence || 0).toFixed(0)}%
                        </div>
                        <div class="analysis-item">
                            <span>📈 Edge:</span> ${(event.edge || 0).toFixed(1)}%
                        </div>
                        <div class="analysis-item">
                            <span>💰 Stake:</span> ${(event.recommended_stake || 0).toFixed(1)}%
                        </div>
                        <div class="analysis-item">
                            <span>🎯 Rank:</span> #${index + 1}
                        </div>
                    </div>

                    <div class="bookmakers-list">
                        ${(event.bookmaker_links || []).slice(0, 4).map(b => `
                            <a href="${b.url}" target="_blank" class="bookmaker-btn">${b.name}</a>
                        `).join('')}
                    </div>
                </div>
            `).join('');
        }

        function renderLiveMatches(matches) {
            const container = document.getElementById('live-matches');

            if (!matches.length) {
                container.innerHTML = '<p style="color: var(--text-secondary); font-size: 14px;">Nenhum jogo ao vivo</p>';
                return;
            }

            container.innerHTML = matches.map(match => `
                <div class="live-match">
                    <div style="font-size: 12px; color: var(--text-secondary);">${match.league} - ${match.minute}'</div>
                    <div class="live-score">${match.home_team} ${match.home_goals} - ${match.away_goals} ${match.away_team}</div>
                    <div class="live-stats">
                        <div>${match.stats?.possession?.home || 50}%</div>
                        <div class="label">Posse</div>
                        <div>${match.stats?.possession?.away || 50}%</div>
                        <div>${match.stats?.shots?.home || 0}</div>
                        <div class="label">Chutes</div>
                        <div>${match.stats?.shots?.away || 0}</div>
                    </div>
                    <div class="momentum-bar">
                        <div class="momentum-fill" style="width: ${50 + (match.momentum || 0) / 2}%;"></div>
                    </div>
                </div>
            `).join('');
        }

        function renderBookmakers(bookmakers) {
            const container = document.getElementById('bookmakers-list');
            container.innerHTML = bookmakers.map(b => `
                <a href="${b.url}" target="_blank" class="bookmaker-btn">
                    ${b.accepts_pix ? '💚' : ''} ${b.name}
                </a>
            `).join('');
        }

        function getSignalLabel(signal) {
            const labels = {
                'strong_buy': '🔥 APOSTAR',
                'buy': '✅ COMPRAR',
                'hold': '⏳ AGUARDAR',
                'avoid': '❌ EVITAR'
            };
            return labels[signal] || signal;
        }

        function openBet(matchId, market) {
            // Abre link da casa de apostas para o mercado selecionado
            console.log(`Opening bet: ${matchId} - ${market}`);
        }

        // Filter buttons
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                // Implement filter logic here
            });
        });

        // Initial connection
        connect();

        // Fetch initial data
        fetch('/api/events')
            .then(res => res.json())
            .then(data => updateDashboard(data))
            .catch(err => console.error('Error fetching initial data:', err));
    </script>
</body>
</html>
"""


# ============================================================================
# ROUTES
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve o dashboard HTML."""
    return DASHBOARD_HTML


@app.get("/api/events")
async def get_events():
    """Retorna eventos rankeados."""
    from src.strategy.bookmakers import BookmakerManager

    # Busca eventos (em produção, viria do orchestrator)
    events = await _fetch_sample_events()

    # Rankeia por Markov
    markov = MarkovPredictor()
    ranked_events = markov.rank_events(events, max_events=15)

    # Filtra melhores
    event_filter = EventFilter()
    filtered = event_filter.filter_events(ranked_events, [])

    # Bookmakers
    bm_manager = BookmakerManager()
    bookmakers = [
        {
            "id": b.id,
            "name": b.name,
            "url": b.base_url,
            "accepts_pix": b.accepts_pix,
        }
        for b in bm_manager.get_brazil_bookmakers()
    ]

    return {
        "total_events": len(ranked_events),
        "value_bets_count": len([e for e in filtered if e.signal.value in ['strong_buy', 'buy']]),
        "live_count": len([e for e in ranked_events if e.get("is_live")]),
        "events": [e.to_dict() for e in filtered[:15]],
        "live_matches": [],
        "bookmakers": bookmakers,
    }


@app.get("/api/bookmakers")
async def get_bookmakers():
    """Retorna casas de apostas."""
    manager = BookmakerManager()
    return {
        "bookmakers": [
            {
                "id": b.id,
                "name": b.name,
                "url": b.base_url,
                "odds_quality": b.odds_quality,
                "accepts_pix": b.accepts_pix,
                "min_deposit": b.min_deposit,
            }
            for b in manager.get_all()
        ]
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket para atualizações em tempo real."""
    await websocket.accept()
    active_connections.append(websocket)

    try:
        while True:
            # Envia updates a cada 30 segundos
            data = await get_events()
            await websocket.send_json(data)
            await asyncio.sleep(30)

    except WebSocketDisconnect:
        active_connections.remove(websocket)


async def broadcast_update(data: dict):
    """Envia update para todos os clientes conectados."""
    for connection in active_connections:
        try:
            await connection.send_json(data)
        except:
            pass


async def _fetch_sample_events() -> list[dict]:
    """Eventos de exemplo (em produção, viria das APIs)."""
    return [
        {
            "id": "1",
            "home_team": {"name": "Flamengo"},
            "away_team": {"name": "Palmeiras"},
            "league": "brasileirao_a",
            "kickoff": datetime.now().isoformat(),
            "home_form": "WDWWL",
            "away_form": "WWDLW",
            "h2h_results": "WDLWD",
            "odds": {"home": 2.10, "draw": 3.40, "away": 3.20},
        },
        {
            "id": "2",
            "home_team": {"name": "Manchester City"},
            "away_team": {"name": "Liverpool"},
            "league": "premier_league",
            "kickoff": datetime.now().isoformat(),
            "home_form": "WWWWW",
            "away_form": "WDWWW",
            "h2h_results": "DWWLD",
            "odds": {"home": 1.75, "draw": 3.80, "away": 4.50},
        },
        {
            "id": "3",
            "home_team": {"name": "Real Madrid"},
            "away_team": {"name": "Barcelona"},
            "league": "la_liga",
            "kickoff": datetime.now().isoformat(),
            "home_form": "WWWDW",
            "away_form": "WDWLW",
            "h2h_results": "WDWDL",
            "odds": {"home": 2.00, "draw": 3.50, "away": 3.60},
        },
        {
            "id": "4",
            "home_team": {"name": "Corinthians"},
            "away_team": {"name": "São Paulo"},
            "league": "brasileirao_a",
            "kickoff": datetime.now().isoformat(),
            "home_form": "LDLWD",
            "away_form": "WDWDL",
            "h2h_results": "DDDWL",
            "odds": {"home": 2.60, "draw": 3.10, "away": 2.80},
        },
        {
            "id": "5",
            "home_team": {"name": "Bayern Munich"},
            "away_team": {"name": "Dortmund"},
            "league": "bundesliga",
            "kickoff": datetime.now().isoformat(),
            "home_form": "WWWWW",
            "away_form": "WLWDW",
            "h2h_results": "WWWDW",
            "odds": {"home": 1.45, "draw": 4.80, "away": 6.50},
        },
    ]


# ============================================================================
# RUN
# ============================================================================

def run_dashboard(host: str = "0.0.0.0", port: int = 8000):
    """Inicia o dashboard."""
    import uvicorn
    logger.info(f"Starting dashboard at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_dashboard()
