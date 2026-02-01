#!/usr/bin/env python3
"""
Dashboard Local Standalone - LOBINHO-BET
=========================================
Dashboard completo com estatisticas detalhadas, barras visuais e mapa de calor.
"""

import json
import random
from http.server import HTTPServer, SimpleHTTPRequestHandler
import webbrowser

# Dados completos dos jogos ao vivo
SAMPLE_EVENTS = [
    {
        "id": "1",
        "home_team": "Manchester City",
        "away_team": "Liverpool",
        "league": "Premier League",
        "kickoff": "15:00",
        "odds": {"home": 2.15, "draw": 3.50, "away": 3.40},
        "edge": 6.2,
        "signal": "buy",
        "markov_confidence": 85,
        "recommended_stake": 2.9,
        "is_live": True,
        "minute": 67,
        "period": "2T",
        "home_goals": 2,
        "away_goals": 1,
        "stats": {
            "possession": {"home": 58, "away": 42},
            "shots": {"home": 14, "away": 9},
            "shots_on_target": {"home": 7, "away": 4},
            "corners": {"home": 6, "away": 3},
            "fouls": {"home": 8, "away": 12},
            "yellow_cards": {"home": 1, "away": 2},
            "red_cards": {"home": 0, "away": 0},
            "dangerous_attacks": {"home": 48, "away": 31},
            "attacks": {"home": 78, "away": 52},
            "xg": {"home": 2.34, "away": 1.12},
            "passes": {"home": 412, "away": 298},
            "pass_accuracy": {"home": 87, "away": 81},
            "offsides": {"home": 2, "away": 3},
            "saves": {"home": 3, "away": 5},
            "tackles": {"home": 14, "away": 18},
            "interceptions": {"home": 8, "away": 11},
            "clearances": {"home": 12, "away": 19}
        },
        "heatmap": {
            "home_defense": 25,
            "home_midfield": 45,
            "home_attack": 72,
            "away_defense": 30,
            "away_midfield": 38,
            "away_attack": 28
        },
        "momentum": 65,
        "form_home": ["W", "W", "D", "W", "L"],
        "form_away": ["W", "L", "W", "W", "D"],
        "events": [
            {"minute": 12, "type": "goal", "team": "home", "player": "Haaland"},
            {"minute": 34, "type": "goal", "team": "away", "player": "Salah"},
            {"minute": 45, "type": "yellow", "team": "away", "player": "Robertson"},
            {"minute": 58, "type": "goal", "team": "home", "player": "De Bruyne"},
            {"minute": 63, "type": "yellow", "team": "away", "player": "Mac Allister"},
        ],
        "momentum_history": [
            {"min": 1, "home": 15, "away": 8},
            {"min": 5, "home": 35, "away": 12},
            {"min": 10, "home": 65, "away": 20},
            {"min": 12, "home": 85, "away": 15},
            {"min": 15, "home": 45, "away": 30},
            {"min": 20, "home": 30, "away": 55},
            {"min": 25, "home": 25, "away": 70},
            {"min": 30, "home": 40, "away": 60},
            {"min": 34, "home": 20, "away": 80},
            {"min": 35, "home": 35, "away": 50},
            {"min": 40, "home": 50, "away": 40},
            {"min": 45, "home": 55, "away": 35},
            {"min": 50, "home": 70, "away": 25},
            {"min": 55, "home": 80, "away": 20},
            {"min": 58, "home": 90, "away": 10},
            {"min": 60, "home": 75, "away": 30},
            {"min": 65, "home": 60, "away": 45},
            {"min": 67, "home": 55, "away": 40}
        ],
        "predictions": {
            "home_win": 52,
            "draw": 28,
            "away_win": 20,
            "over_25": 75,
            "btts": 85,
            "next_goal_home": 65,
            "next_goal_away": 35
        }
    },
    {
        "id": "2",
        "home_team": "Real Madrid",
        "away_team": "Barcelona",
        "league": "La Liga",
        "kickoff": "17:00",
        "odds": {"home": 2.10, "draw": 3.90, "away": 3.20},
        "edge": 5.2,
        "signal": "buy",
        "markov_confidence": 82,
        "recommended_stake": 2.5,
        "is_live": True,
        "minute": 34,
        "period": "1T",
        "home_goals": 1,
        "away_goals": 1,
        "stats": {
            "possession": {"home": 45, "away": 55},
            "shots": {"home": 8, "away": 10},
            "shots_on_target": {"home": 4, "away": 5},
            "corners": {"home": 3, "away": 5},
            "fouls": {"home": 6, "away": 8},
            "yellow_cards": {"home": 1, "away": 1},
            "red_cards": {"home": 0, "away": 0},
            "dangerous_attacks": {"home": 28, "away": 35},
            "attacks": {"home": 45, "away": 58},
            "xg": {"home": 1.15, "away": 1.42},
            "passes": {"home": 245, "away": 312},
            "pass_accuracy": {"home": 84, "away": 89},
            "offsides": {"home": 1, "away": 2},
            "saves": {"home": 4, "away": 3},
            "tackles": {"home": 12, "away": 10},
            "interceptions": {"home": 6, "away": 5},
            "clearances": {"home": 8, "away": 7}
        },
        "heatmap": {
            "home_defense": 35,
            "home_midfield": 42,
            "home_attack": 45,
            "away_defense": 32,
            "away_midfield": 48,
            "away_attack": 55
        },
        "momentum": 42,
        "form_home": ["W", "W", "W", "D", "W"],
        "form_away": ["W", "W", "L", "W", "W"],
        "events": [
            {"minute": 15, "type": "goal", "team": "home", "player": "Vinicius Jr"},
            {"minute": 28, "type": "goal", "team": "away", "player": "Lewandowski"},
            {"minute": 30, "type": "yellow", "team": "home", "player": "Tchouameni"},
        ],
        "momentum_history": [
            {"min": 1, "home": 20, "away": 25},
            {"min": 5, "home": 30, "away": 35},
            {"min": 10, "home": 45, "away": 40},
            {"min": 15, "home": 75, "away": 25},
            {"min": 20, "home": 50, "away": 45},
            {"min": 25, "home": 35, "away": 60},
            {"min": 28, "home": 20, "away": 85},
            {"min": 30, "home": 40, "away": 55},
            {"min": 34, "home": 45, "away": 50}
        ],
        "predictions": {
            "home_win": 38,
            "draw": 32,
            "away_win": 30,
            "over_25": 68,
            "btts": 90,
            "next_goal_home": 45,
            "next_goal_away": 55
        }
    },
    {
        "id": "3",
        "home_team": "Flamengo",
        "away_team": "Palmeiras",
        "league": "Brasileirao",
        "kickoff": "19:00",
        "odds": {"home": 2.05, "draw": 3.40, "away": 3.30},
        "edge": 2.1,
        "signal": "hold",
        "markov_confidence": 72,
        "recommended_stake": 1.5,
        "is_live": False,
    },
    {
        "id": "4",
        "home_team": "Bayern Munich",
        "away_team": "Dortmund",
        "league": "Bundesliga",
        "kickoff": "16:30",
        "odds": {"home": 1.75, "draw": 4.00, "away": 4.50},
        "edge": 4.0,
        "signal": "hold",
        "markov_confidence": 88,
        "recommended_stake": 2.3,
        "is_live": True,
        "minute": 78,
        "period": "2T",
        "home_goals": 3,
        "away_goals": 1,
        "stats": {
            "possession": {"home": 62, "away": 38},
            "shots": {"home": 18, "away": 8},
            "shots_on_target": {"home": 9, "away": 3},
            "corners": {"home": 8, "away": 2},
            "fouls": {"home": 10, "away": 14},
            "yellow_cards": {"home": 0, "away": 3},
            "red_cards": {"home": 0, "away": 0},
            "dangerous_attacks": {"home": 62, "away": 24},
            "attacks": {"home": 95, "away": 48},
            "xg": {"home": 3.21, "away": 0.89},
            "passes": {"home": 534, "away": 312},
            "pass_accuracy": {"home": 91, "away": 78},
            "offsides": {"home": 3, "away": 1},
            "saves": {"home": 2, "away": 6},
            "tackles": {"home": 16, "away": 22},
            "interceptions": {"home": 10, "away": 14},
            "clearances": {"home": 14, "away": 28}
        },
        "heatmap": {
            "home_defense": 18,
            "home_midfield": 55,
            "home_attack": 85,
            "away_defense": 65,
            "away_midfield": 32,
            "away_attack": 15
        },
        "momentum": 82,
        "form_home": ["W", "W", "W", "W", "W"],
        "form_away": ["W", "D", "L", "W", "D"],
        "events": [
            {"minute": 8, "type": "goal", "team": "home", "player": "Kane"},
            {"minute": 22, "type": "goal", "team": "away", "player": "Brandt"},
            {"minute": 45, "type": "yellow", "team": "away", "player": "Schlotterbeck"},
            {"minute": 56, "type": "goal", "team": "home", "player": "Musiala"},
            {"minute": 72, "type": "goal", "team": "home", "player": "Sane"},
            {"minute": 75, "type": "yellow", "team": "away", "player": "Can"},
        ],
        "momentum_history": [
            {"min": 1, "home": 30, "away": 20},
            {"min": 5, "home": 50, "away": 25},
            {"min": 8, "home": 90, "away": 10},
            {"min": 10, "home": 70, "away": 25},
            {"min": 15, "home": 55, "away": 40},
            {"min": 20, "home": 40, "away": 55},
            {"min": 22, "home": 25, "away": 75},
            {"min": 25, "home": 45, "away": 50},
            {"min": 30, "home": 55, "away": 40},
            {"min": 35, "home": 65, "away": 30},
            {"min": 40, "home": 70, "away": 25},
            {"min": 45, "home": 60, "away": 35},
            {"min": 50, "home": 75, "away": 20},
            {"min": 55, "home": 85, "away": 15},
            {"min": 56, "home": 95, "away": 5},
            {"min": 60, "home": 80, "away": 20},
            {"min": 65, "home": 70, "away": 30},
            {"min": 70, "home": 75, "away": 25},
            {"min": 72, "home": 90, "away": 10},
            {"min": 75, "home": 70, "away": 30},
            {"min": 78, "home": 65, "away": 35}
        ],
        "predictions": {
            "home_win": 92,
            "draw": 6,
            "away_win": 2,
            "over_25": 95,
            "btts": 100,
            "next_goal_home": 78,
            "next_goal_away": 22
        }
    },
    {
        "id": "5",
        "home_team": "Inter Milan",
        "away_team": "AC Milan",
        "league": "Serie A",
        "kickoff": "18:00",
        "odds": {"home": 2.00, "draw": 3.60, "away": 3.80},
        "edge": 4.2,
        "signal": "hold",
        "markov_confidence": 78,
        "recommended_stake": 2.1,
        "is_live": True,
        "minute": 52,
        "period": "2T",
        "home_goals": 0,
        "away_goals": 0,
        "stats": {
            "possession": {"home": 52, "away": 48},
            "shots": {"home": 11, "away": 9},
            "shots_on_target": {"home": 4, "away": 3},
            "corners": {"home": 5, "away": 4},
            "fouls": {"home": 12, "away": 11},
            "yellow_cards": {"home": 2, "away": 2},
            "red_cards": {"home": 0, "away": 0},
            "dangerous_attacks": {"home": 38, "away": 35},
            "attacks": {"home": 62, "away": 58},
            "xg": {"home": 1.45, "away": 1.12},
            "passes": {"home": 356, "away": 328},
            "pass_accuracy": {"home": 85, "away": 83},
            "offsides": {"home": 2, "away": 2},
            "saves": {"home": 3, "away": 4},
            "tackles": {"home": 18, "away": 16},
            "interceptions": {"home": 9, "away": 8},
            "clearances": {"home": 15, "away": 14}
        },
        "heatmap": {
            "home_defense": 38,
            "home_midfield": 50,
            "home_attack": 52,
            "away_defense": 40,
            "away_midfield": 48,
            "away_attack": 45
        },
        "momentum": 55,
        "form_home": ["W", "D", "W", "L", "W"],
        "form_away": ["D", "W", "W", "D", "L"],
        "events": [
            {"minute": 18, "type": "yellow", "team": "home", "player": "Barella"},
            {"minute": 35, "type": "yellow", "team": "away", "player": "Theo Hernandez"},
            {"minute": 42, "type": "yellow", "team": "home", "player": "Bastoni"},
            {"minute": 48, "type": "yellow", "team": "away", "player": "Bennacer"},
        ],
        "momentum_history": [
            {"min": 1, "home": 25, "away": 30},
            {"min": 5, "home": 35, "away": 40},
            {"min": 10, "home": 45, "away": 50},
            {"min": 15, "home": 55, "away": 45},
            {"min": 20, "home": 50, "away": 50},
            {"min": 25, "home": 40, "away": 55},
            {"min": 30, "home": 45, "away": 50},
            {"min": 35, "home": 50, "away": 45},
            {"min": 40, "home": 55, "away": 40},
            {"min": 45, "home": 50, "away": 50},
            {"min": 50, "home": 55, "away": 45},
            {"min": 52, "home": 52, "away": 48}
        ],
        "predictions": {
            "home_win": 42,
            "draw": 35,
            "away_win": 23,
            "over_25": 45,
            "btts": 55,
            "next_goal_home": 55,
            "next_goal_away": 45
        }
    },
    {
        "id": "6",
        "home_team": "Corinthians",
        "away_team": "Sao Paulo",
        "league": "Brasileirao",
        "kickoff": "21:00",
        "odds": {"home": 2.40, "draw": 3.20, "away": 2.90},
        "edge": -1.5,
        "signal": "avoid",
        "markov_confidence": 65,
        "recommended_stake": 0,
        "is_live": False,
    },
]

BOOKMAKERS = [
    {"id": "bet365", "name": "Bet365", "url": "https://www.bet365.com", "accepts_pix": True},
    {"id": "betano", "name": "Betano", "url": "https://www.betano.com.br", "accepts_pix": True},
    {"id": "sportingbet", "name": "Sportingbet", "url": "https://www.sportingbet.com", "accepts_pix": True},
    {"id": "pinnacle", "name": "Pinnacle", "url": "https://www.pinnacle.com", "accepts_pix": False},
    {"id": "betfair", "name": "Betfair", "url": "https://www.betfair.com", "accepts_pix": False},
]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LOBINHO-BET - Dashboard Completo</title>
    <style>
        :root {
            --bg-dark: #0a0e14;
            --bg-card: #141a22;
            --bg-card-alt: #1a222d;
            --bg-hover: #1e2833;
            --text-primary: #ffffff;
            --text-secondary: #8899a6;
            --text-muted: #5c6b7a;
            --accent-green: #00d26a;
            --accent-red: #ff4757;
            --accent-yellow: #ffc107;
            --accent-blue: #00a8ff;
            --accent-purple: #9c27b0;
            --accent-orange: #ff9f43;
            --border-color: #2d3741;
            --home-color: #3498db;
            --away-color: #e74c3c;
            --field-green: #2d5a27;
            --field-lines: rgba(255,255,255,0.6);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
            background: var(--bg-dark);
            color: var(--text-primary);
            min-height: 100vh;
            line-height: 1.4;
        }

        /* Header */
        .header {
            background: linear-gradient(135deg, #141a22 0%, #0a0e14 100%);
            padding: 15px 20px;
            border-bottom: 1px solid var(--border-color);
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .header-content {
            max-width: 1800px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }

        .header h1 {
            font-size: 22px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .header-stats {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            align-items: center;
        }

        /* Sound Toggle Button */
        .sound-toggle {
            display: flex;
            align-items: center;
            gap: 8px;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 25px;
            padding: 8px 16px;
            cursor: pointer;
            transition: all 0.3s ease;
            color: var(--text-primary);
            font-size: 13px;
        }

        .sound-toggle:hover {
            background: var(--bg-card-alt);
            border-color: var(--accent-green);
        }

        .sound-toggle.muted {
            background: rgba(239, 68, 68, 0.1);
            border-color: var(--accent-red);
        }

        .sound-toggle.muted:hover {
            background: rgba(239, 68, 68, 0.2);
        }

        .sound-toggle .sound-icon {
            font-size: 16px;
        }

        .sound-toggle .sound-label {
            font-weight: 600;
        }

        .stat-box {
            background: var(--bg-card);
            padding: 8px 16px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid var(--border-color);
        }

        .stat-value {
            font-size: 20px;
            font-weight: bold;
            color: var(--accent-green);
        }

        .stat-value.red { color: var(--accent-red); }
        .stat-value.blue { color: var(--accent-blue); }
        .stat-value.yellow { color: var(--accent-yellow); }

        .stat-label {
            font-size: 11px;
            color: var(--text-secondary);
            text-transform: uppercase;
        }

        /* Main Layout with Sidebar */
        .main-wrapper {
            display: grid;
            grid-template-columns: 1fr 320px;
            max-width: 1800px;
            margin: 0 auto;
            gap: 20px;
            padding: 20px;
        }

        @media (max-width: 1200px) {
            .main-wrapper {
                grid-template-columns: 1fr;
            }
            .sidebar {
                order: -1;
            }
        }

        .main-content {
            min-width: 0;
        }

        /* Sidebar */
        .sidebar {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }

        .sidebar-card {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 15px;
            border: 1px solid var(--border-color);
        }

        .sidebar-title {
            font-size: 14px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* Football Field Heatmap - FootyStats Style */
        .field-container {
            position: relative;
            width: 100%;
            aspect-ratio: 1.5;
            background: linear-gradient(to right, #1a472a 0%, #2d5a27 50%, #1a472a 100%);
            border-radius: 8px;
            overflow: hidden;
            border: 2px solid #fff;
        }

        /* Field lines */
        .field-lines {
            position: absolute;
            inset: 0;
            pointer-events: none;
        }

        .field-lines::before {
            content: '';
            position: absolute;
            left: 50%;
            top: 0;
            bottom: 0;
            width: 2px;
            background: rgba(255,255,255,0.5);
            transform: translateX(-50%);
        }

        .field-lines::after {
            content: '';
            position: absolute;
            left: 50%;
            top: 50%;
            width: 50px;
            height: 50px;
            border: 2px solid rgba(255,255,255,0.5);
            border-radius: 50%;
            transform: translate(-50%, -50%);
        }

        /* Penalty areas */
        .penalty-box-left,
        .penalty-box-right {
            position: absolute;
            width: 18%;
            height: 60%;
            top: 20%;
            border: 2px solid rgba(255,255,255,0.5);
            z-index: 5;
        }

        .penalty-box-left { left: 0; border-left: none; }
        .penalty-box-right { right: 0; border-right: none; }

        .goal-box-left,
        .goal-box-right {
            position: absolute;
            width: 8%;
            height: 30%;
            top: 35%;
            border: 2px solid rgba(255,255,255,0.5);
            z-index: 5;
        }

        .goal-box-left { left: 0; border-left: none; }
        .goal-box-right { right: 0; border-right: none; }

        /* Heatmap Canvas Layer */
        .heatmap-canvas {
            position: absolute;
            inset: 0;
            z-index: 2;
        }

        /* Legend - FootyStats Style */
        .heatmap-legend-fs {
            display: flex;
            flex-direction: column;
            gap: 6px;
            margin-top: 12px;
            padding: 12px;
            background: var(--bg-card-alt);
            border-radius: 8px;
        }

        .legend-title-fs {
            font-size: 13px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 4px;
        }

        .legend-item-fs {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 11px;
        }

        .legend-color-fs {
            width: 40px;
            height: 14px;
            border-radius: 3px;
        }

        .legend-color-fs.hot { background: linear-gradient(90deg, #ff4500, #ff0000); }
        .legend-color-fs.warm { background: linear-gradient(90deg, #ff8c00, #ff6600); }
        .legend-color-fs.moderate { background: linear-gradient(90deg, #00bfff, #1e90ff); }
        .legend-color-fs.cold { background: linear-gradient(90deg, #0000cd, #000080); }

        /* Team indicators on field */
        .field-team-labels {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-size: 12px;
            font-weight: 600;
        }

        .field-team-labels .home { color: var(--home-color); }
        .field-team-labels .away { color: var(--away-color); }

        /* Attack Momentum Chart - Full Width */
        .momentum-chart-container {
            background: var(--bg-card-alt);
            border-radius: 0;
            padding: 15px 20px;
            margin: 20px -20px 0 -20px;
            width: calc(100% + 40px);
        }

        .momentum-chart-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }

        .momentum-chart-title {
            font-size: 14px;
            font-weight: 600;
            color: var(--text-primary);
        }

        .momentum-chart {
            position: relative;
            height: 150px;
            background: var(--bg-dark);
            border-radius: 0;
            overflow: hidden;
        }

        .momentum-chart-center {
            position: absolute;
            left: 0;
            right: 0;
            top: 50%;
            height: 1px;
            background: rgba(255,255,255,0.3);
            z-index: 1;
        }

        .momentum-bars {
            display: flex;
            align-items: center;
            height: 100%;
            gap: 1px;
            padding: 0;
        }

        .momentum-bar-wrapper {
            flex: 1;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            position: relative;
        }

        .momentum-bar {
            width: 100%;
            transition: height 0.3s ease;
            border-radius: 2px;
        }

        .momentum-bar.home {
            background: linear-gradient(180deg, #00d26a 0%, #00a854 100%);
            align-self: flex-end;
            margin-bottom: 50%;
            transform: translateY(50%);
        }

        .momentum-bar.away {
            background: linear-gradient(0deg, #00a8ff 0%, #0077cc 100%);
            align-self: flex-start;
            margin-top: 50%;
            transform: translateY(-50%);
        }

        .momentum-time-labels {
            display: flex;
            justify-content: space-between;
            margin-top: 8px;
            font-size: 10px;
            color: var(--text-muted);
        }

        /* 6 Segment Dividers */
        .momentum-segments {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            display: flex;
            pointer-events: none;
            z-index: 2;
        }

        .momentum-segment {
            flex: 1;
            border-right: 1px dashed rgba(255,255,255,0.15);
            position: relative;
        }

        .momentum-segment:last-child {
            border-right: none;
        }

        .momentum-segment-label {
            position: absolute;
            top: 5px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 9px;
            color: rgba(255,255,255,0.3);
            font-weight: 600;
        }

        /* Momentum Analysis Panel */
        .momentum-analysis {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid var(--border-color);
        }

        .momentum-analysis-box {
            background: var(--bg-dark);
            border-radius: 8px;
            padding: 12px;
        }

        .momentum-analysis-title {
            font-size: 11px;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .momentum-analysis-title .icon {
            font-size: 14px;
        }

        .last-15-stats {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .last-15-team {
            text-align: center;
        }

        .last-15-team .team-name {
            font-size: 10px;
            color: var(--text-muted);
            margin-bottom: 4px;
        }

        .last-15-team .pressure-value {
            font-size: 24px;
            font-weight: 700;
        }

        .last-15-team.home .pressure-value { color: var(--accent-green); }
        .last-15-team.away .pressure-value { color: var(--accent-blue); }

        .last-15-vs {
            font-size: 12px;
            color: var(--text-muted);
        }

        .prediction-indicator {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 8px;
        }

        .prediction-indicator:last-child {
            margin-bottom: 0;
        }

        .prediction-icon {
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
        }

        .prediction-icon.high { background: rgba(0, 210, 106, 0.2); }
        .prediction-icon.medium { background: rgba(255, 193, 7, 0.2); }
        .prediction-icon.low { background: rgba(239, 68, 68, 0.2); }

        .prediction-text {
            flex: 1;
        }

        .prediction-text .label {
            font-size: 11px;
            color: var(--text-secondary);
        }

        .prediction-text .value {
            font-size: 13px;
            font-weight: 600;
            color: var(--text-primary);
        }

        .prediction-text .value.high { color: var(--accent-green); }
        .prediction-text .value.medium { color: #ffc107; }
        .prediction-text .value.low { color: var(--accent-red); }

        .prediction-prob {
            font-size: 16px;
            font-weight: 700;
        }

        .prediction-prob.high { color: var(--accent-green); }
        .prediction-prob.medium { color: #ffc107; }
        .prediction-prob.low { color: var(--accent-red); }

        .momentum-team-labels {
            display: flex;
            flex-direction: column;
            position: absolute;
            right: 8px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 10px;
            gap: 60px;
        }

        .momentum-team-labels span:first-child {
            color: var(--accent-green);
        }

        .momentum-team-labels span:last-child {
            color: var(--accent-blue);
        }

        /* Predictions Panel */
        .predictions-panel {
            background: var(--bg-card-alt);
            border-radius: 10px;
            padding: 15px;
            margin-top: 15px;
        }

        .predictions-title {
            font-size: 14px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .predictions-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
        }

        .prediction-item {
            background: var(--bg-dark);
            border-radius: 8px;
            padding: 12px 8px;
            text-align: center;
        }

        .prediction-label {
            font-size: 10px;
            color: var(--text-secondary);
            text-transform: uppercase;
            margin-bottom: 6px;
        }

        .prediction-value {
            font-size: 22px;
            font-weight: 700;
        }

        .prediction-value.high { color: var(--accent-green); }
        .prediction-value.medium { color: var(--accent-yellow); }
        .prediction-value.low { color: var(--accent-red); }

        .prediction-bar {
            height: 4px;
            background: var(--bg-card);
            border-radius: 2px;
            margin-top: 6px;
            overflow: hidden;
        }

        .prediction-bar-fill {
            height: 100%;
            border-radius: 2px;
            transition: width 0.5s ease;
        }

        .prediction-bar-fill.high { background: var(--accent-green); }
        .prediction-bar-fill.medium { background: var(--accent-yellow); }
        .prediction-bar-fill.low { background: var(--accent-red); }

        /* Termometer */
        .termometer-container {
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid var(--border-color);
        }

        .termometer-title {
            font-size: 12px;
            color: var(--text-secondary);
            margin-bottom: 8px;
            text-transform: uppercase;
        }

        .termometer-bar {
            height: 24px;
            background: var(--bg-dark);
            border-radius: 12px;
            overflow: hidden;
            display: flex;
            position: relative;
        }

        .termometer-home {
            height: 100%;
            background: linear-gradient(90deg, var(--home-color), #5dade2);
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding-right: 8px;
            font-size: 11px;
            font-weight: bold;
            transition: width 0.5s ease;
        }

        .termometer-away {
            height: 100%;
            background: linear-gradient(90deg, #ec7063, var(--away-color));
            display: flex;
            align-items: center;
            justify-content: flex-start;
            padding-left: 8px;
            font-size: 11px;
            font-weight: bold;
            transition: width 0.5s ease;
        }

        /* Action indicators */
        .action-indicators {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin-top: 15px;
        }

        .action-item {
            background: var(--bg-card-alt);
            padding: 10px;
            border-radius: 6px;
            text-align: center;
        }

        .action-value {
            font-size: 18px;
            font-weight: bold;
        }

        .action-value.home { color: var(--home-color); }
        .action-value.away { color: var(--away-color); }

        .action-label {
            font-size: 10px;
            color: var(--text-secondary);
            text-transform: uppercase;
        }

        /* Match selector in sidebar */
        .match-selector {
            margin-bottom: 15px;
        }

        .match-selector select {
            width: 100%;
            padding: 10px;
            background: var(--bg-card-alt);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            color: var(--text-primary);
            font-size: 13px;
            cursor: pointer;
        }

        .match-selector select:focus {
            outline: none;
            border-color: var(--accent-blue);
        }

        /* Live Games Section */
        .live-section {
            margin-bottom: 30px;
        }

        .section-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--accent-red);
        }

        .section-title {
            font-size: 18px;
            font-weight: 600;
        }

        .live-pulse {
            width: 12px;
            height: 12px;
            background: var(--accent-red);
            border-radius: 50%;
            animation: pulse 1.5s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(0.9); }
        }

        /* Live Match Card */
        .live-match-card {
            background: var(--bg-card);
            border-radius: 12px;
            margin-bottom: 20px;
            border: 1px solid var(--border-color);
            overflow: hidden;
        }

        .match-header {
            background: linear-gradient(90deg, var(--bg-card-alt) 0%, var(--bg-card) 50%, var(--bg-card-alt) 100%);
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border-color);
        }

        .match-info {
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .league-badge {
            background: var(--accent-blue);
            color: white;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }

        .match-time {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .minute-badge {
            background: var(--accent-red);
            color: white;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 14px;
            font-weight: bold;
            animation: blink 1s infinite;
        }

        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }

        .period-badge {
            color: var(--text-secondary);
            font-size: 12px;
        }

        /* Scoreboard */
        .scoreboard {
            padding: 25px 20px;
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            gap: 30px;
            align-items: center;
        }

        .team-side {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .team-side.home { text-align: right; }
        .team-side.away { text-align: left; }

        .team-name {
            font-size: 22px;
            font-weight: 700;
        }

        .team-form {
            display: flex;
            gap: 4px;
            justify-content: flex-end;
        }

        .team-side.away .team-form {
            justify-content: flex-start;
        }

        .form-badge {
            width: 22px;
            height: 22px;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 11px;
            font-weight: bold;
        }

        .form-badge.W { background: var(--accent-green); color: #000; }
        .form-badge.D { background: var(--accent-yellow); color: #000; }
        .form-badge.L { background: var(--accent-red); color: #fff; }

        .score-center {
            text-align: center;
        }

        .score-display {
            font-size: 52px;
            font-weight: 800;
            letter-spacing: 8px;
            background: linear-gradient(180deg, #fff 0%, #ccc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .match-status {
            font-size: 12px;
            color: var(--accent-green);
            margin-top: 5px;
        }

        /* Stats Container */
        .stats-container {
            padding: 0 20px 20px 20px;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 15px;
        }

        /* Stat Row with Bar */
        .stat-row {
            background: var(--bg-card-alt);
            border-radius: 8px;
            padding: 12px 15px;
        }

        .stat-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }

        .stat-name {
            font-size: 12px;
            color: var(--text-secondary);
            text-transform: uppercase;
            font-weight: 600;
        }

        .stat-values {
            display: flex;
            gap: 15px;
            font-size: 14px;
            font-weight: 700;
        }

        .stat-home { color: var(--home-color); }
        .stat-away { color: var(--away-color); }

        /* Progress Bar */
        .stat-bar-container {
            height: 8px;
            background: var(--bg-dark);
            border-radius: 4px;
            overflow: hidden;
            display: flex;
        }

        .stat-bar-home {
            height: 100%;
            background: linear-gradient(90deg, var(--home-color), #5dade2);
            transition: width 0.5s ease;
            border-radius: 4px 0 0 4px;
        }

        .stat-bar-away {
            height: 100%;
            background: linear-gradient(90deg, #ec7063, var(--away-color));
            transition: width 0.5s ease;
            border-radius: 0 4px 4px 0;
        }

        /* XG Special */
        .xg-display {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            background: linear-gradient(90deg, rgba(52, 152, 219, 0.1), transparent, rgba(231, 76, 60, 0.1));
            border-radius: 8px;
            margin-bottom: 15px;
        }

        .xg-value {
            font-size: 28px;
            font-weight: 800;
        }

        .xg-label {
            font-size: 12px;
            color: var(--text-secondary);
        }

        .xg-vs {
            font-size: 12px;
            color: var(--text-muted);
        }

        /* Momentum Bar */
        .momentum-container {
            background: var(--bg-card-alt);
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
        }

        .momentum-label {
            display: flex;
            justify-content: space-between;
            font-size: 11px;
            color: var(--text-secondary);
            margin-bottom: 8px;
        }

        .momentum-bar {
            height: 12px;
            background: linear-gradient(90deg, var(--home-color), var(--bg-dark) 45%, var(--bg-dark) 55%, var(--away-color));
            border-radius: 6px;
            position: relative;
        }

        .momentum-indicator {
            position: absolute;
            top: -3px;
            width: 18px;
            height: 18px;
            background: var(--accent-yellow);
            border-radius: 50%;
            border: 2px solid var(--bg-dark);
            transition: left 0.5s ease;
        }

        /* Match Events Timeline */
        .events-timeline {
            background: var(--bg-card-alt);
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
        }

        .events-title {
            font-size: 13px;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 10px;
            text-transform: uppercase;
        }

        .event-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 0;
            border-bottom: 1px solid var(--border-color);
            font-size: 13px;
        }

        .event-item:last-child { border-bottom: none; }

        .event-minute {
            width: 35px;
            font-weight: 600;
            color: var(--text-secondary);
        }

        .event-icon {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
        }

        .event-icon.goal { background: var(--accent-green); }
        .event-icon.yellow { background: var(--accent-yellow); color: #000; }
        .event-icon.red { background: var(--accent-red); }
        .event-icon.sub { background: var(--accent-blue); }

        .event-player { flex: 1; }
        .event-team {
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 3px;
        }

        .event-team.home { background: rgba(52, 152, 219, 0.2); color: var(--home-color); }
        .event-team.away { background: rgba(231, 76, 60, 0.2); color: var(--away-color); }

        /* Odds Section */
        .odds-section {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-top: 15px;
            padding: 15px;
            background: var(--bg-card-alt);
            border-radius: 8px;
        }

        .odd-box {
            text-align: center;
            padding: 12px;
            background: var(--bg-dark);
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
            border: 2px solid transparent;
        }

        .odd-box:hover {
            background: var(--bg-hover);
            border-color: var(--accent-blue);
        }

        .odd-box.recommended {
            border-color: var(--accent-green);
            background: rgba(0, 210, 106, 0.1);
        }

        .odd-value {
            font-size: 22px;
            font-weight: 700;
        }

        .odd-label {
            font-size: 11px;
            color: var(--text-secondary);
            margin-top: 4px;
        }

        .odd-trend {
            font-size: 10px;
            margin-top: 4px;
        }

        .odd-trend.up { color: var(--accent-green); }
        .odd-trend.down { color: var(--accent-red); }

        /* Analysis Badge */
        .analysis-section {
            display: flex;
            gap: 15px;
            padding: 15px;
            background: var(--bg-card-alt);
            border-radius: 8px;
            margin-top: 15px;
            flex-wrap: wrap;
        }

        .analysis-item {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .analysis-label {
            font-size: 10px;
            color: var(--text-secondary);
            text-transform: uppercase;
        }

        .analysis-value {
            font-size: 16px;
            font-weight: 700;
        }

        .signal-badge {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
        }

        .signal-badge.buy { background: var(--accent-green); color: #000; }
        .signal-badge.hold { background: var(--accent-yellow); color: #000; }
        .signal-badge.avoid { background: #666; color: #fff; }

        /* Upcoming Events */
        .upcoming-section {
            margin-top: 30px;
        }

        .upcoming-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--accent-blue);
        }

        .upcoming-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 15px;
        }

        .upcoming-card {
            background: var(--bg-card);
            border-radius: 10px;
            padding: 15px;
            border: 1px solid var(--border-color);
            transition: all 0.2s;
        }

        .upcoming-card:hover {
            transform: translateY(-2px);
            border-color: var(--accent-blue);
        }

        .upcoming-league {
            font-size: 11px;
            color: var(--accent-blue);
            margin-bottom: 8px;
        }

        .upcoming-teams {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 10px;
        }

        .upcoming-time {
            font-size: 20px;
            font-weight: 700;
            color: var(--accent-yellow);
            margin-bottom: 10px;
        }

        .upcoming-odds {
            display: flex;
            gap: 8px;
            margin-bottom: 10px;
        }

        .upcoming-odd {
            flex: 1;
            text-align: center;
            padding: 8px;
            background: var(--bg-card-alt);
            border-radius: 6px;
        }

        .upcoming-odd-value {
            font-weight: 700;
        }

        .upcoming-odd-label {
            font-size: 10px;
            color: var(--text-secondary);
        }

        /* Footer Update */
        .update-indicator {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: var(--accent-green);
            color: #000;
            padding: 10px 20px;
            border-radius: 25px;
            font-size: 13px;
            font-weight: 600;
            opacity: 0;
            transition: opacity 0.3s;
            display: flex;
            align-items: center;
            gap: 8px;
            z-index: 1000;
        }

        .update-indicator.show { opacity: 1; }

        /* Goal Notification */
        .goal-notification {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) scale(0.5);
            background: linear-gradient(135deg, #ff6b00 0%, #ff9500 50%, #ffcc00 100%);
            color: #000;
            padding: 30px 60px;
            border-radius: 20px;
            font-size: 32px;
            font-weight: 900;
            text-transform: uppercase;
            opacity: 0;
            transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
            z-index: 9999;
            box-shadow: 0 0 60px rgba(255, 150, 0, 0.8), 0 0 100px rgba(255, 150, 0, 0.4);
            text-align: center;
            pointer-events: none;
        }

        .goal-notification.show {
            opacity: 1;
            transform: translate(-50%, -50%) scale(1);
        }

        .goal-notification .goal-icon {
            font-size: 50px;
            display: block;
            margin-bottom: 10px;
            animation: bounce 0.5s ease infinite;
        }

        .goal-notification .goal-teams {
            font-size: 16px;
            font-weight: 600;
            margin-top: 10px;
            opacity: 0.9;
        }

        .goal-notification .goal-score {
            font-size: 48px;
            font-weight: 900;
            margin: 5px 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .goal-notification .goal-scorer {
            font-size: 18px;
            font-weight: 700;
            margin-top: 8px;
            color: #222;
        }

        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }

        @keyframes goalPulse {
            0%, 100% { box-shadow: 0 0 60px rgba(255, 150, 0, 0.8), 0 0 100px rgba(255, 150, 0, 0.4); }
            50% { box-shadow: 0 0 80px rgba(255, 150, 0, 1), 0 0 150px rgba(255, 150, 0, 0.6); }
        }

        .goal-notification.show {
            animation: goalPulse 0.5s ease infinite;
        }

        /* Goal Prediction Alert */
        .goal-prediction-alert {
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%) translateY(-100px);
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border: 2px solid #ffc107;
            border-radius: 15px;
            padding: 15px 25px;
            display: flex;
            align-items: center;
            gap: 15px;
            z-index: 9998;
            opacity: 0;
            transition: all 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
            box-shadow: 0 10px 40px rgba(255, 193, 7, 0.3);
        }

        .goal-prediction-alert.show {
            opacity: 1;
            transform: translateX(-50%) translateY(0);
        }

        .goal-prediction-alert .alert-icon {
            font-size: 36px;
            animation: pulse 1s ease infinite;
        }

        .goal-prediction-alert .alert-content {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .goal-prediction-alert .alert-title {
            font-size: 18px;
            font-weight: 800;
            color: #ffc107;
            text-transform: uppercase;
        }

        .goal-prediction-alert .alert-match {
            font-size: 14px;
            font-weight: 600;
            color: var(--text-primary);
        }

        .goal-prediction-alert .alert-details {
            display: flex;
            gap: 15px;
            font-size: 12px;
            color: var(--text-secondary);
        }

        .goal-prediction-alert .alert-details span {
            display: flex;
            align-items: center;
            gap: 4px;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .scoreboard {
                grid-template-columns: 1fr;
                gap: 15px;
            }
            .team-side, .team-side.home { text-align: center; }
            .team-form { justify-content: center; }
            .stats-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <header class="header">
        <div class="header-content">
            <h1>LOBINHO-BET <span style="font-size: 13px; color: var(--text-secondary); font-weight: 400;">Dashboard Ao Vivo</span></h1>
            <div class="header-stats">
                <div class="stat-box">
                    <div class="stat-value" id="total-events">0</div>
                    <div class="stat-label">Eventos</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" id="value-bets">0</div>
                    <div class="stat-label">Value Bets</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value red" id="live-count">0</div>
                    <div class="stat-label">Ao Vivo</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value yellow" id="total-goals">0</div>
                    <div class="stat-label">Gols Hoje</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value blue" id="last-update">--:--:--</div>
                    <div class="stat-label">Atualizado</div>
                </div>
                <button class="sound-toggle" id="sound-toggle" onclick="toggleSound()" title="Ativar/Silenciar Sons">
                    <span class="sound-icon" id="sound-icon">🔔</span>
                    <span class="sound-label" id="sound-label">Som</span>
                </button>
            </div>
        </div>
    </header>

    <div class="main-wrapper">
        <main class="main-content">
            <!-- Live Games Section -->
            <section class="live-section">
                <div class="section-header">
                    <div class="live-pulse"></div>
                    <h2 class="section-title">Jogos Ao Vivo - Estatisticas Detalhadas</h2>
                </div>
                <div id="live-matches-container"></div>
            </section>

            <!-- Upcoming Games -->
            <section class="upcoming-section">
                <div class="upcoming-header">
                    <h2 class="section-title">Proximos Jogos</h2>
                </div>
                <div class="upcoming-grid" id="upcoming-container"></div>
            </section>
        </main>

        <!-- Sidebar with Heatmap -->
        <aside class="sidebar">
            <div class="sidebar-card">
                <div class="sidebar-title">
                    <span style="font-size: 16px;">🔥</span>
                    Mapa de Calor - Termometro do Jogo
                </div>

                <div class="match-selector">
                    <select id="heatmap-match-selector" onchange="updateHeatmapDisplay()">
                    </select>
                </div>

                <div class="field-team-labels">
                    <span class="home" id="heatmap-home-team">Casa</span>
                    <span class="away" id="heatmap-away-team">Fora</span>
                </div>

                <div class="field-container" id="field-container">
                    <canvas id="heatmap-canvas" class="heatmap-canvas"></canvas>
                    <div class="field-lines"></div>
                    <div class="penalty-box-left"></div>
                    <div class="penalty-box-right"></div>
                    <div class="goal-box-left"></div>
                    <div class="goal-box-right"></div>
                </div>

                <!-- Legenda estilo FootyStats -->
                <div class="heatmap-legend-fs">
                    <div class="legend-title-fs">Acoes na Area</div>
                    <div class="legend-item-fs">
                        <div class="legend-color-fs hot"></div>
                        <span>Muitas Acoes</span>
                    </div>
                    <div class="legend-item-fs">
                        <div class="legend-color-fs warm"></div>
                        <span>Acoes Moderadas</span>
                    </div>
                    <div class="legend-item-fs">
                        <div class="legend-color-fs moderate"></div>
                        <span>Poucas Acoes</span>
                    </div>
                    <div class="legend-item-fs">
                        <div class="legend-color-fs cold"></div>
                        <span>Nenhuma Acao</span>
                    </div>
                </div>

                <div class="termometer-container">
                    <div class="termometer-title">Pressao Geral</div>
                    <div class="termometer-bar">
                        <div class="termometer-home" id="termo-home" style="width: 50%;">50%</div>
                        <div class="termometer-away" id="termo-away" style="width: 50%;">50%</div>
                    </div>
                </div>

                <div class="action-indicators">
                    <div class="action-item">
                        <div class="action-value home" id="actions-home">0</div>
                        <div class="action-label">Acoes Casa</div>
                    </div>
                    <div class="action-item">
                        <div class="action-value away" id="actions-away">0</div>
                        <div class="action-label">Acoes Fora</div>
                    </div>
                    <div class="action-item">
                        <div class="action-value home" id="danger-home">0</div>
                        <div class="action-label">Perigo Casa</div>
                    </div>
                    <div class="action-item">
                        <div class="action-value away" id="danger-away">0</div>
                        <div class="action-label">Perigo Fora</div>
                    </div>
                </div>
            </div>

            <div class="sidebar-card">
                <div class="sidebar-title">
                    <span style="font-size: 16px;">📊</span>
                    Como Interpretar
                </div>
                <div style="font-size: 12px; color: var(--text-secondary); line-height: 1.8;">
                    <p><strong style="color: #ff4500;">Vermelho/Laranja</strong> = Alta atividade ofensiva</p>
                    <p><strong style="color: #00bfff;">Azul Claro</strong> = Atividade moderada</p>
                    <p><strong style="color: #0000cd;">Azul Escuro</strong> = Baixa atividade</p>
                    <p style="margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--border-color);">
                        Zonas quentes indicam onde o time esta pressionando.
                        Use para prever gols e corners!
                    </p>
                </div>
            </div>
        </aside>
    </div>

    <div class="update-indicator" id="update-indicator">Dados Atualizados!</div>

    <div class="goal-notification" id="goal-notification">
        <span class="goal-icon">⚽</span>
        <div>GOOOOOL!</div>
        <div class="goal-teams" id="goal-teams"></div>
        <div class="goal-score" id="goal-score"></div>
        <div class="goal-scorer" id="goal-scorer"></div>
    </div>

    <!-- Goal Sound Effect (coin sound) -->
    <audio id="goal-sound" preload="auto">
        <source src="data:audio/mp3;base64,SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4Ljc2LjEwMAAAAAAAAAAAAAAA//tQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAWGluZwAAAA8AAAACAAABhgC7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7//////////////////////////////////////////////////////////////////8AAAAATGF2YzU4LjEzAAAAAAAAAAAAAAAAJAAAAAAAAAAAAYYNQPHmAAAAAAD/+9DEAAAIAAaH9AAAIAYC8f8poAhVgYMJ8ogHD5QEEhIhogmUBwMBw+D8Pg+CAIOBx/l8vKAgCAIeXB8HwfB8HwfB8HxAEAAACGhpaJp/QEAQA8Hw+GAYP8+XB4Pn/Lg+UBwMBw+sD6wfqHygOHwfygfggEHAQB8HwQCD4IQBAQBAH//+sHw+D5QHwQgEIPg+D4AAALu7v7u7v//7u7u8HwfB8oD4Pg+D4AA=" type="audio/mp3"/>
    </audio>

    <script>
        let events = EVENTS_DATA;
        let bookmakers = BOOKMAKERS_DATA;
        let selectedMatchId = null;

        // Sound settings
        let soundEnabled = true;
        let goalAudioCtx = null;

        function toggleSound() {
            soundEnabled = !soundEnabled;
            const btn = document.getElementById('sound-toggle');
            const icon = document.getElementById('sound-icon');
            const label = document.getElementById('sound-label');

            if (soundEnabled) {
                btn.classList.remove('muted');
                icon.textContent = '🔔';
                label.textContent = 'Som';
            } else {
                btn.classList.add('muted');
                icon.textContent = '🔕';
                label.textContent = 'Mudo';
            }

            // Save preference
            localStorage.setItem('lobinho_sound', soundEnabled ? 'on' : 'off');
        }

        // Load sound preference on start
        document.addEventListener('DOMContentLoaded', () => {
            const savedPref = localStorage.getItem('lobinho_sound');
            if (savedPref === 'off') {
                soundEnabled = false;
                const btn = document.getElementById('sound-toggle');
                const icon = document.getElementById('sound-icon');
                const label = document.getElementById('sound-label');
                btn.classList.add('muted');
                icon.textContent = '🔕';
                label.textContent = 'Mudo';
            }
        });

        function playGoalSound() {
            // Check if sound is enabled
            if (!soundEnabled) return;

            // Create audio context if not exists
            if (!goalAudioCtx) {
                goalAudioCtx = new (window.AudioContext || window.webkitAudioContext)();
            }

            // Play a coin/ding sound using Web Audio API
            const oscillator = goalAudioCtx.createOscillator();
            const gainNode = goalAudioCtx.createGain();

            oscillator.connect(gainNode);
            gainNode.connect(goalAudioCtx.destination);

            // Coin sound frequencies
            oscillator.frequency.setValueAtTime(1200, goalAudioCtx.currentTime);
            oscillator.frequency.exponentialRampToValueAtTime(2400, goalAudioCtx.currentTime + 0.1);
            oscillator.frequency.exponentialRampToValueAtTime(1800, goalAudioCtx.currentTime + 0.2);

            gainNode.gain.setValueAtTime(0.3, goalAudioCtx.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, goalAudioCtx.currentTime + 0.5);

            oscillator.start(goalAudioCtx.currentTime);
            oscillator.stop(goalAudioCtx.currentTime + 0.5);

            // Play second ding after short delay (double coin sound)
            setTimeout(() => {
                const osc2 = goalAudioCtx.createOscillator();
                const gain2 = goalAudioCtx.createGain();
                osc2.connect(gain2);
                gain2.connect(goalAudioCtx.destination);

                osc2.frequency.setValueAtTime(1500, goalAudioCtx.currentTime);
                osc2.frequency.exponentialRampToValueAtTime(3000, goalAudioCtx.currentTime + 0.1);

                gain2.gain.setValueAtTime(0.4, goalAudioCtx.currentTime);
                gain2.gain.exponentialRampToValueAtTime(0.01, goalAudioCtx.currentTime + 0.4);

                osc2.start(goalAudioCtx.currentTime);
                osc2.stop(goalAudioCtx.currentTime + 0.4);
            }, 150);
        }

        function showGoalNotification(match, team, scorer) {
            const notification = document.getElementById('goal-notification');
            const teamsEl = document.getElementById('goal-teams');
            const scoreEl = document.getElementById('goal-score');
            const scorerEl = document.getElementById('goal-scorer');

            teamsEl.textContent = match.home_team + ' vs ' + match.away_team;
            scoreEl.textContent = match.home_goals + ' - ' + match.away_goals;
            scorerEl.textContent = '⚽ ' + (team === 'home' ? match.home_team.split(' ')[0] : match.away_team.split(' ')[0]) + ' - ' + scorer + ' ' + match.minute + "'";

            // Play sound
            playGoalSound();

            // Show notification
            notification.classList.add('show');

            // Hide after 3 seconds
            setTimeout(() => {
                notification.classList.remove('show');
            }, 3000);
        }

        document.addEventListener('DOMContentLoaded', () => {
            initHeatmapSelector();
            renderAll();
            startAutoUpdate();
        });

        function initHeatmapSelector() {
            const selector = document.getElementById('heatmap-match-selector');
            const liveEvents = events.filter(e => e.is_live);

            selector.innerHTML = liveEvents.map(e =>
                `<option value="${e.id}">${e.home_team} vs ${e.away_team} (${e.minute}')</option>`
            ).join('');

            if (liveEvents.length > 0) {
                selectedMatchId = liveEvents[0].id;
            }

            // Initialize canvas size
            setTimeout(() => {
                updateHeatmapDisplay();
            }, 100);

            // Redraw on window resize
            window.addEventListener('resize', () => {
                updateHeatmapDisplay();
            });
        }

        function updateHeatmapDisplay() {
            const selector = document.getElementById('heatmap-match-selector');
            selectedMatchId = selector.value;

            const match = events.find(e => e.id === selectedMatchId);
            if (!match || !match.is_live) return;

            // Update team names
            document.getElementById('heatmap-home-team').textContent = match.home_team.split(' ')[0];
            document.getElementById('heatmap-away-team').textContent = match.away_team.split(' ')[0];

            // Get heatmap data (or calculate from stats)
            const heatmap = match.heatmap || calculateHeatmap(match);

            // Draw heatmap on canvas
            drawHeatmap(heatmap);

            // Update termometer
            const homeTotal = heatmap.home_defense + heatmap.home_midfield + heatmap.home_attack;
            const awayTotal = heatmap.away_defense + heatmap.away_midfield + heatmap.away_attack;
            const total = homeTotal + awayTotal;
            const homePercent = Math.round((homeTotal / total) * 100);
            const awayPercent = 100 - homePercent;

            document.getElementById('termo-home').style.width = homePercent + '%';
            document.getElementById('termo-home').textContent = homePercent + '%';
            document.getElementById('termo-away').style.width = awayPercent + '%';
            document.getElementById('termo-away').textContent = awayPercent + '%';

            // Update action indicators
            document.getElementById('actions-home').textContent = match.stats?.attacks?.home || 0;
            document.getElementById('actions-away').textContent = match.stats?.attacks?.away || 0;
            document.getElementById('danger-home').textContent = match.stats?.dangerous_attacks?.home || 0;
            document.getElementById('danger-away').textContent = match.stats?.dangerous_attacks?.away || 0;
        }

        function calculateHeatmap(match) {
            const stats = match.stats || {};
            const possession = stats.possession || {home: 50, away: 50};
            const attacks = stats.attacks || {home: 50, away: 50};
            const dangerous = stats.dangerous_attacks || {home: 30, away: 30};
            const shots = stats.shots || {home: 5, away: 5};

            return {
                home_defense: Math.round(20 + (100 - possession.home) * 0.3),
                home_midfield: Math.round(30 + possession.home * 0.4),
                home_attack: Math.round(attacks.home * 0.5 + dangerous.home * 0.8 + shots.home * 2),
                away_defense: Math.round(20 + (100 - possession.away) * 0.3),
                away_midfield: Math.round(30 + possession.away * 0.4),
                away_attack: Math.round(attacks.away * 0.5 + dangerous.away * 0.8 + shots.away * 2)
            };
        }

        function drawHeatmap(heatmap) {
            const container = document.getElementById('field-container');
            const canvas = document.getElementById('heatmap-canvas');
            const ctx = canvas.getContext('2d');

            // Set canvas size
            canvas.width = container.offsetWidth;
            canvas.height = container.offsetHeight;

            const w = canvas.width;
            const h = canvas.height;

            // Clear canvas
            ctx.clearRect(0, 0, w, h);

            // Normalize values (0-100)
            const normalize = (val) => Math.min(100, Math.max(0, val));

            // Define heat zones with positions and intensities
            const zones = [
                // Home side (left)
                { x: w * 0.12, y: h * 0.5, intensity: normalize(heatmap.home_attack), radius: w * 0.18 },
                { x: w * 0.08, y: h * 0.3, intensity: normalize(heatmap.home_attack * 0.7), radius: w * 0.12 },
                { x: w * 0.08, y: h * 0.7, intensity: normalize(heatmap.home_attack * 0.7), radius: w * 0.12 },
                { x: w * 0.25, y: h * 0.5, intensity: normalize(heatmap.home_midfield), radius: w * 0.15 },
                { x: w * 0.35, y: h * 0.35, intensity: normalize(heatmap.home_midfield * 0.6), radius: w * 0.12 },
                { x: w * 0.35, y: h * 0.65, intensity: normalize(heatmap.home_midfield * 0.6), radius: w * 0.12 },
                // Away side (right)
                { x: w * 0.88, y: h * 0.5, intensity: normalize(heatmap.away_attack), radius: w * 0.18 },
                { x: w * 0.92, y: h * 0.3, intensity: normalize(heatmap.away_attack * 0.7), radius: w * 0.12 },
                { x: w * 0.92, y: h * 0.7, intensity: normalize(heatmap.away_attack * 0.7), radius: w * 0.12 },
                { x: w * 0.75, y: h * 0.5, intensity: normalize(heatmap.away_midfield), radius: w * 0.15 },
                { x: w * 0.65, y: h * 0.35, intensity: normalize(heatmap.away_midfield * 0.6), radius: w * 0.12 },
                { x: w * 0.65, y: h * 0.65, intensity: normalize(heatmap.away_midfield * 0.6), radius: w * 0.12 },
                // Center
                { x: w * 0.5, y: h * 0.5, intensity: normalize((heatmap.home_midfield + heatmap.away_midfield) / 2 * 0.4), radius: w * 0.12 },
            ];

            // Draw each heat zone
            zones.forEach(zone => {
                if (zone.intensity > 10) {
                    drawHeatZone(ctx, zone.x, zone.y, zone.radius, zone.intensity);
                }
            });
        }

        function drawHeatZone(ctx, x, y, radius, intensity) {
            // Create radial gradient - FootyStats style colors
            const gradient = ctx.createRadialGradient(x, y, 0, x, y, radius);

            // Color based on intensity
            let innerColor, outerColor;

            if (intensity >= 70) {
                // Hot - Red/Orange
                innerColor = `rgba(255, 0, 0, ${0.7 * intensity / 100})`;
                outerColor = `rgba(255, 69, 0, 0)`;
            } else if (intensity >= 50) {
                // Warm - Orange
                innerColor = `rgba(255, 140, 0, ${0.6 * intensity / 100})`;
                outerColor = `rgba(255, 165, 0, 0)`;
            } else if (intensity >= 30) {
                // Moderate - Blue/Cyan
                innerColor = `rgba(0, 191, 255, ${0.5 * intensity / 100})`;
                outerColor = `rgba(30, 144, 255, 0)`;
            } else {
                // Cold - Dark Blue
                innerColor = `rgba(0, 0, 205, ${0.4 * intensity / 100})`;
                outerColor = `rgba(0, 0, 128, 0)`;
            }

            gradient.addColorStop(0, innerColor);
            gradient.addColorStop(0.5, innerColor.replace(/[\d.]+\)$/, `${0.3 * intensity / 100})`));
            gradient.addColorStop(1, outerColor);

            ctx.fillStyle = gradient;
            ctx.beginPath();
            ctx.arc(x, y, radius, 0, Math.PI * 2);
            ctx.fill();
        }

        function renderAll() {
            renderLiveMatches();
            renderUpcomingMatches();
            updateStats();
            updateHeatmapDisplay();
        }

        function renderLiveMatches() {
            const container = document.getElementById('live-matches-container');
            const liveEvents = events.filter(e => e.is_live);

            if (liveEvents.length === 0) {
                container.innerHTML = '<p style="color: var(--text-secondary); padding: 30px; text-align: center;">Nenhum jogo ao vivo no momento</p>';
                return;
            }

            container.innerHTML = liveEvents.map(match => `
                <div class="live-match-card">
                    <!-- Header -->
                    <div class="match-header">
                        <div class="match-info">
                            <span class="league-badge">${match.league}</span>
                        </div>
                        <div class="match-time">
                            <span class="minute-badge">${match.minute}'</span>
                            <span class="period-badge">${match.period || '2T'}</span>
                        </div>
                    </div>

                    <!-- Scoreboard -->
                    <div class="scoreboard">
                        <div class="team-side home">
                            <div class="team-name">${match.home_team}</div>
                            <div class="team-form">
                                ${(match.form_home || ['W','D','L','W','W']).map(f => `<span class="form-badge ${f}">${f}</span>`).join('')}
                            </div>
                        </div>
                        <div class="score-center">
                            <div class="score-display">${match.home_goals} - ${match.away_goals}</div>
                            <div class="match-status">Em andamento</div>
                        </div>
                        <div class="team-side away">
                            <div class="team-name">${match.away_team}</div>
                            <div class="team-form">
                                ${(match.form_away || ['W','L','W','D','W']).map(f => `<span class="form-badge ${f}">${f}</span>`).join('')}
                            </div>
                        </div>
                    </div>

                    <!-- Stats -->
                    <div class="stats-container">
                        <!-- xG Display -->
                        <div class="xg-display">
                            <div>
                                <div class="xg-value stat-home">${match.stats?.xg?.home?.toFixed(2) || '0.00'}</div>
                                <div class="xg-label">xG Casa</div>
                            </div>
                            <div class="xg-vs">Expected Goals</div>
                            <div>
                                <div class="xg-value stat-away">${match.stats?.xg?.away?.toFixed(2) || '0.00'}</div>
                                <div class="xg-label">xG Fora</div>
                            </div>
                        </div>

                        <!-- Momentum -->
                        <div class="momentum-container">
                            <div class="momentum-label">
                                <span>Pressao ${match.home_team.split(' ')[0]}</span>
                                <span>Momentum do Jogo</span>
                                <span>Pressao ${match.away_team.split(' ')[0]}</span>
                            </div>
                            <div class="momentum-bar">
                                <div class="momentum-indicator" style="left: calc(${match.momentum || 50}% - 9px);"></div>
                            </div>
                        </div>

                        <!-- Stats Grid -->
                        <div class="stats-grid">
                            ${renderStatRow('Posse de Bola', match.stats?.possession?.home || 50, match.stats?.possession?.away || 50, '%')}
                            ${renderStatRow('Finalizacoes', match.stats?.shots?.home || 0, match.stats?.shots?.away || 0)}
                            ${renderStatRow('Chutes no Gol', match.stats?.shots_on_target?.home || 0, match.stats?.shots_on_target?.away || 0)}
                            ${renderStatRow('Escanteios', match.stats?.corners?.home || 0, match.stats?.corners?.away || 0)}
                            ${renderStatRow('Ataques Perigosos', match.stats?.dangerous_attacks?.home || 0, match.stats?.dangerous_attacks?.away || 0)}
                            ${renderStatRow('Ataques', match.stats?.attacks?.home || 0, match.stats?.attacks?.away || 0)}
                            ${renderStatRow('Faltas', match.stats?.fouls?.home || 0, match.stats?.fouls?.away || 0)}
                            ${renderStatRow('Cartoes Amarelos', match.stats?.yellow_cards?.home || 0, match.stats?.yellow_cards?.away || 0)}
                            ${renderStatRow('Cartoes Vermelhos', match.stats?.red_cards?.home || 0, match.stats?.red_cards?.away || 0)}
                            ${renderStatRow('Passes', match.stats?.passes?.home || 0, match.stats?.passes?.away || 0)}
                            ${renderStatRow('Precisao Passes', match.stats?.pass_accuracy?.home || 0, match.stats?.pass_accuracy?.away || 0, '%')}
                            ${renderStatRow('Impedimentos', match.stats?.offsides?.home || 0, match.stats?.offsides?.away || 0)}
                            ${renderStatRow('Defesas', match.stats?.saves?.home || 0, match.stats?.saves?.away || 0)}
                            ${renderStatRow('Desarmes', match.stats?.tackles?.home || 0, match.stats?.tackles?.away || 0)}
                            ${renderStatRow('Interceptacoes', match.stats?.interceptions?.home || 0, match.stats?.interceptions?.away || 0)}
                            ${renderStatRow('Cortes', match.stats?.clearances?.home || 0, match.stats?.clearances?.away || 0)}
                        </div>

                        <!-- Events Timeline -->
                        ${match.events && match.events.length > 0 ? `
                            <div class="events-timeline">
                                <div class="events-title">Linha do Tempo</div>
                                ${match.events.slice(-6).reverse().map(ev => `
                                    <div class="event-item">
                                        <span class="event-minute">${ev.minute}'</span>
                                        <span class="event-icon ${ev.type}">${getEventIcon(ev.type)}</span>
                                        <span class="event-player">${ev.player}</span>
                                        <span class="event-team ${ev.team}">${ev.team === 'home' ? match.home_team.split(' ')[0] : match.away_team.split(' ')[0]}</span>
                                    </div>
                                `).join('')}
                            </div>
                        ` : ''}

                        <!-- Odds -->
                        <div class="odds-section">
                            <div class="odd-box ${match.signal === 'buy' ? 'recommended' : ''}">
                                <div class="odd-value">${match.odds.home.toFixed(2)}</div>
                                <div class="odd-label">Casa</div>
                                <div class="odd-trend ${Math.random() > 0.5 ? 'up' : 'down'}">${Math.random() > 0.5 ? '↑' : '↓'}</div>
                            </div>
                            <div class="odd-box">
                                <div class="odd-value">${match.odds.draw.toFixed(2)}</div>
                                <div class="odd-label">Empate</div>
                                <div class="odd-trend ${Math.random() > 0.5 ? 'up' : 'down'}">${Math.random() > 0.5 ? '↑' : '↓'}</div>
                            </div>
                            <div class="odd-box">
                                <div class="odd-value">${match.odds.away.toFixed(2)}</div>
                                <div class="odd-label">Fora</div>
                                <div class="odd-trend ${Math.random() > 0.5 ? 'up' : 'down'}">${Math.random() > 0.5 ? '↑' : '↓'}</div>
                            </div>
                        </div>

                        <!-- Analysis -->
                        <div class="analysis-section">
                            <div class="analysis-item">
                                <span class="analysis-label">Markov</span>
                                <span class="analysis-value">${match.markov_confidence}%</span>
                            </div>
                            <div class="analysis-item">
                                <span class="analysis-label">Edge</span>
                                <span class="analysis-value" style="color: ${match.edge > 0 ? 'var(--accent-green)' : 'var(--accent-red)'}">${match.edge > 0 ? '+' : ''}${match.edge.toFixed(1)}%</span>
                            </div>
                            <div class="analysis-item">
                                <span class="analysis-label">Stake Kelly</span>
                                <span class="analysis-value">${match.recommended_stake.toFixed(1)}%</span>
                            </div>
                            <div class="analysis-item">
                                <span class="analysis-label">Sinal</span>
                                <span class="signal-badge ${match.signal}">${getSignalLabel(match.signal)}</span>
                            </div>
                        </div>

                        <!-- Attack Momentum Chart -->
                        ${match.momentum_history ? `
                        <div class="momentum-chart-container">
                            <div class="momentum-chart-header">
                                <span class="momentum-chart-title">📊 Attack Momentum</span>
                                <span style="font-size: 11px; color: var(--text-secondary);">${match.minute}'</span>
                            </div>
                            <div class="momentum-chart">
                                <div class="momentum-chart-center"></div>
                                <!-- 6 Segment Dividers -->
                                <div class="momentum-segments">
                                    <div class="momentum-segment"><span class="momentum-segment-label">0-15</span></div>
                                    <div class="momentum-segment"><span class="momentum-segment-label">15-30</span></div>
                                    <div class="momentum-segment"><span class="momentum-segment-label">30-45</span></div>
                                    <div class="momentum-segment"><span class="momentum-segment-label">45-60</span></div>
                                    <div class="momentum-segment"><span class="momentum-segment-label">60-75</span></div>
                                    <div class="momentum-segment"><span class="momentum-segment-label">75-90</span></div>
                                </div>
                                <div class="momentum-bars">
                                    ${match.momentum_history.map(m => `
                                        <div class="momentum-bar-wrapper" title="${m.min}'">
                                            <div class="momentum-bar home" style="height: ${m.home * 0.45}%;"></div>
                                            <div class="momentum-bar away" style="height: ${m.away * 0.45}%;"></div>
                                        </div>
                                    `).join('')}
                                </div>
                                <div class="momentum-team-labels">
                                    <span>${match.home_team.split(' ')[0]}</span>
                                    <span>${match.away_team.split(' ')[0]}</span>
                                </div>
                            </div>
                            <div class="momentum-time-labels">
                                <span>0'</span>
                                <span>15'</span>
                                <span>30'</span>
                                <span>45'</span>
                                <span>60'</span>
                                <span>75'</span>
                                <span>90'</span>
                            </div>

                            <!-- Momentum Analysis -->
                            <div class="momentum-analysis" id="momentum-analysis-${match.id}">
                                ${renderMomentumAnalysis(match)}
                            </div>
                        </div>
                        ` : ''}

                        <!-- Predictions Panel -->
                        ${match.predictions ? `
                        <div class="predictions-panel">
                            <div class="predictions-title">
                                <span>📊</span> Previsao de Resultado
                            </div>
                            <div class="predictions-grid">
                                <div class="prediction-item">
                                    <div class="prediction-label">Casa</div>
                                    <div class="prediction-value ${match.predictions.home_win >= 50 ? 'high' : match.predictions.home_win >= 30 ? 'medium' : 'low'}">${match.predictions.home_win}%</div>
                                    <div class="prediction-bar">
                                        <div class="prediction-bar-fill ${match.predictions.home_win >= 50 ? 'high' : match.predictions.home_win >= 30 ? 'medium' : 'low'}" style="width: ${match.predictions.home_win}%"></div>
                                    </div>
                                </div>
                                <div class="prediction-item">
                                    <div class="prediction-label">Empate</div>
                                    <div class="prediction-value ${match.predictions.draw >= 40 ? 'high' : match.predictions.draw >= 25 ? 'medium' : 'low'}">${match.predictions.draw}%</div>
                                    <div class="prediction-bar">
                                        <div class="prediction-bar-fill ${match.predictions.draw >= 40 ? 'high' : match.predictions.draw >= 25 ? 'medium' : 'low'}" style="width: ${match.predictions.draw}%"></div>
                                    </div>
                                </div>
                                <div class="prediction-item">
                                    <div class="prediction-label">Fora</div>
                                    <div class="prediction-value ${match.predictions.away_win >= 50 ? 'high' : match.predictions.away_win >= 30 ? 'medium' : 'low'}">${match.predictions.away_win}%</div>
                                    <div class="prediction-bar">
                                        <div class="prediction-bar-fill ${match.predictions.away_win >= 50 ? 'high' : match.predictions.away_win >= 30 ? 'medium' : 'low'}" style="width: ${match.predictions.away_win}%"></div>
                                    </div>
                                </div>
                                <div class="prediction-item">
                                    <div class="prediction-label">Over 2.5</div>
                                    <div class="prediction-value ${match.predictions.over_25 >= 60 ? 'high' : match.predictions.over_25 >= 40 ? 'medium' : 'low'}">${match.predictions.over_25}%</div>
                                    <div class="prediction-bar">
                                        <div class="prediction-bar-fill ${match.predictions.over_25 >= 60 ? 'high' : match.predictions.over_25 >= 40 ? 'medium' : 'low'}" style="width: ${match.predictions.over_25}%"></div>
                                    </div>
                                </div>
                                <div class="prediction-item">
                                    <div class="prediction-label">BTTS</div>
                                    <div class="prediction-value ${match.predictions.btts >= 60 ? 'high' : match.predictions.btts >= 40 ? 'medium' : 'low'}">${match.predictions.btts}%</div>
                                    <div class="prediction-bar">
                                        <div class="prediction-bar-fill ${match.predictions.btts >= 60 ? 'high' : match.predictions.btts >= 40 ? 'medium' : 'low'}" style="width: ${match.predictions.btts}%"></div>
                                    </div>
                                </div>
                                <div class="prediction-item">
                                    <div class="prediction-label">Prox. Gol</div>
                                    <div class="prediction-value" style="font-size: 14px; color: ${match.predictions.next_goal_home > match.predictions.next_goal_away ? 'var(--accent-green)' : 'var(--accent-blue)'}">
                                        ${match.predictions.next_goal_home > match.predictions.next_goal_away ? match.home_team.split(' ')[0] : match.away_team.split(' ')[0]}
                                    </div>
                                    <div style="font-size: 10px; color: var(--text-secondary); margin-top: 4px;">
                                        ${match.predictions.next_goal_home}% / ${match.predictions.next_goal_away}%
                                    </div>
                                </div>
                            </div>
                        </div>
                        ` : ''}
                    </div>
                </div>
            `).join('');
        }

        function renderStatRow(name, homeVal, awayVal, suffix = '') {
            const total = Math.max(homeVal + awayVal, 1);
            const homePercent = (homeVal / total) * 100;
            const awayPercent = (awayVal / total) * 100;

            return `
                <div class="stat-row">
                    <div class="stat-header">
                        <span class="stat-name">${name}</span>
                        <div class="stat-values">
                            <span class="stat-home">${homeVal}${suffix}</span>
                            <span class="stat-away">${awayVal}${suffix}</span>
                        </div>
                    </div>
                    <div class="stat-bar-container">
                        <div class="stat-bar-home" style="width: ${homePercent}%;"></div>
                        <div class="stat-bar-away" style="width: ${awayPercent}%;"></div>
                    </div>
                </div>
            `;
        }

        function renderUpcomingMatches() {
            const container = document.getElementById('upcoming-container');
            const upcomingEvents = events.filter(e => !e.is_live);

            container.innerHTML = upcomingEvents.map(match => `
                <div class="upcoming-card">
                    <div class="upcoming-league">${match.league}</div>
                    <div class="upcoming-teams">${match.home_team} vs ${match.away_team}</div>
                    <div class="upcoming-time">${match.kickoff}</div>
                    <div class="upcoming-odds">
                        <div class="upcoming-odd">
                            <div class="upcoming-odd-value">${match.odds.home.toFixed(2)}</div>
                            <div class="upcoming-odd-label">Casa</div>
                        </div>
                        <div class="upcoming-odd">
                            <div class="upcoming-odd-value">${match.odds.draw.toFixed(2)}</div>
                            <div class="upcoming-odd-label">Empate</div>
                        </div>
                        <div class="upcoming-odd">
                            <div class="upcoming-odd-value">${match.odds.away.toFixed(2)}</div>
                            <div class="upcoming-odd-label">Fora</div>
                        </div>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="signal-badge ${match.signal}">${getSignalLabel(match.signal)}</span>
                        <span style="font-size: 12px; color: var(--text-secondary);">Markov: ${match.markov_confidence}%</span>
                    </div>
                </div>
            `).join('');
        }

        function updateStats() {
            const liveEvents = events.filter(e => e.is_live);
            const totalGoals = liveEvents.reduce((sum, e) => sum + (e.home_goals || 0) + (e.away_goals || 0), 0);

            document.getElementById('total-events').textContent = events.length;
            document.getElementById('value-bets').textContent = events.filter(e => e.signal === 'buy').length;
            document.getElementById('live-count').textContent = liveEvents.length;
            document.getElementById('total-goals').textContent = totalGoals;
            document.getElementById('last-update').textContent = new Date().toLocaleTimeString('pt-BR');
        }

        function getSignalLabel(signal) {
            const labels = {
                'buy': 'BUY',
                'hold': 'HOLD',
                'avoid': 'AVOID'
            };
            return labels[signal] || signal.toUpperCase();
        }

        function getEventIcon(type) {
            const icons = {
                'goal': '⚽',
                'yellow': '🟨',
                'red': '🟥',
                'sub': '🔄'
            };
            return icons[type] || '•';
        }

        // Momentum Analysis Functions
        function analyzeMomentum(match) {
            if (!match.momentum_history || match.momentum_history.length < 3) {
                return { last15Home: 0, last15Away: 0, goalProb: 0, dominance: 'neutral', trend: 'stable' };
            }

            const history = match.momentum_history;
            const last5 = history.slice(-5);  // Last ~15 minutes

            // Calculate average pressure in last 15 min
            const last15Home = Math.round(last5.reduce((sum, m) => sum + m.home, 0) / last5.length);
            const last15Away = Math.round(last5.reduce((sum, m) => sum + m.away, 0) / last5.length);

            // Calculate trend (increasing, decreasing, stable)
            const firstHalf = history.slice(0, Math.floor(history.length / 2));
            const secondHalf = history.slice(Math.floor(history.length / 2));

            const firstAvgHome = firstHalf.reduce((sum, m) => sum + m.home, 0) / firstHalf.length;
            const secondAvgHome = secondHalf.reduce((sum, m) => sum + m.home, 0) / secondHalf.length;

            let trend = 'stable';
            if (secondAvgHome > firstAvgHome + 10) trend = 'home_rising';
            else if (secondAvgHome < firstAvgHome - 10) trend = 'away_rising';

            // Dominance
            let dominance = 'neutral';
            if (last15Home > last15Away + 15) dominance = 'home';
            else if (last15Away > last15Home + 15) dominance = 'away';

            // Goal probability based on pressure and xG
            const xgTotal = (match.stats?.xg?.home || 0) + (match.stats?.xg?.away || 0);
            const shotsTotal = (match.stats?.shots_on_target?.home || 0) + (match.stats?.shots_on_target?.away || 0);
            const pressure = Math.max(last15Home, last15Away);

            // Base probability
            let goalProb = 30;
            if (pressure > 70) goalProb += 25;
            else if (pressure > 50) goalProb += 15;

            if (xgTotal > 2) goalProb += 15;
            if (shotsTotal > 8) goalProb += 10;

            // Time factor (more goals in 2nd half and end of game)
            if (match.minute > 75) goalProb += 10;
            else if (match.minute > 60) goalProb += 5;

            goalProb = Math.min(95, Math.max(15, goalProb));

            return { last15Home, last15Away, goalProb, dominance, trend };
        }

        function renderMomentumAnalysis(match) {
            const analysis = analyzeMomentum(match);

            const trendText = {
                'home_rising': '📈 Casa crescendo',
                'away_rising': '📈 Fora crescendo',
                'stable': '➡️ Estavel'
            };

            const goalLevel = analysis.goalProb >= 60 ? 'high' : analysis.goalProb >= 40 ? 'medium' : 'low';
            const goalIcon = analysis.goalProb >= 60 ? '🔥' : analysis.goalProb >= 40 ? '⚡' : '💤';

            return `
                <div class="momentum-analysis-box">
                    <div class="momentum-analysis-title">
                        <span class="icon">⏱️</span> Ultimos 15 min
                    </div>
                    <div class="last-15-stats">
                        <div class="last-15-team home">
                            <div class="team-name">${match.home_team.split(' ')[0]}</div>
                            <div class="pressure-value">${analysis.last15Home}%</div>
                        </div>
                        <div class="last-15-vs">vs</div>
                        <div class="last-15-team away">
                            <div class="team-name">${match.away_team.split(' ')[0]}</div>
                            <div class="pressure-value">${analysis.last15Away}%</div>
                        </div>
                    </div>
                </div>
                <div class="momentum-analysis-box">
                    <div class="momentum-analysis-title">
                        <span class="icon">🎯</span> Previsibilidade
                    </div>
                    <div class="prediction-indicator">
                        <div class="prediction-icon ${goalLevel}">${goalIcon}</div>
                        <div class="prediction-text">
                            <div class="label">Prob. Gol em 15min</div>
                            <div class="value ${goalLevel}">${analysis.goalProb >= 60 ? 'ALTA' : analysis.goalProb >= 40 ? 'MEDIA' : 'BAIXA'}</div>
                        </div>
                        <div class="prediction-prob ${goalLevel}">${analysis.goalProb}%</div>
                    </div>
                    <div class="prediction-indicator">
                        <div class="prediction-icon medium">📊</div>
                        <div class="prediction-text">
                            <div class="label">Tendencia</div>
                            <div class="value">${trendText[analysis.trend]}</div>
                        </div>
                    </div>
                </div>
            `;
        }

        // Track goal alerts
        let goalAlertShown = {};

        function checkGoalAlert(match) {
            const analysis = analyzeMomentum(match);

            // If high goal probability and not already shown alert for this match
            if (analysis.goalProb >= 65 && !goalAlertShown[match.id + '_' + Math.floor(match.minute / 5)]) {
                goalAlertShown[match.id + '_' + Math.floor(match.minute / 5)] = true;
                showGoalPredictionAlert(match, analysis);
            }
        }

        function showGoalPredictionAlert(match, analysis) {
            // Create alert element if not exists
            let alertEl = document.getElementById('goal-prediction-alert');
            if (!alertEl) {
                alertEl = document.createElement('div');
                alertEl.id = 'goal-prediction-alert';
                alertEl.className = 'goal-prediction-alert';
                document.body.appendChild(alertEl);
            }

            const dominantTeam = analysis.dominance === 'home' ? match.home_team.split(' ')[0] :
                                 analysis.dominance === 'away' ? match.away_team.split(' ')[0] : 'Ambos';

            alertEl.innerHTML = `
                <div class="alert-icon">🎯</div>
                <div class="alert-content">
                    <div class="alert-title">GOL PROVAVEL!</div>
                    <div class="alert-match">${match.home_team} vs ${match.away_team}</div>
                    <div class="alert-details">
                        <span>📊 ${analysis.goalProb}% chance</span>
                        <span>⏱️ Proximos 15min</span>
                        <span>🔥 ${dominantTeam} pressionando</span>
                    </div>
                </div>
            `;

            // Play alert sound
            playAlertSound();

            alertEl.classList.add('show');
            setTimeout(() => alertEl.classList.remove('show'), 5000);
        }

        function playAlertSound() {
            // Check if sound is enabled
            if (!soundEnabled) return;

            if (!goalAudioCtx) {
                goalAudioCtx = new (window.AudioContext || window.webkitAudioContext)();
            }

            // Alert sound (3 quick beeps)
            [0, 150, 300].forEach(delay => {
                setTimeout(() => {
                    const osc = goalAudioCtx.createOscillator();
                    const gain = goalAudioCtx.createGain();
                    osc.connect(gain);
                    gain.connect(goalAudioCtx.destination);

                    osc.frequency.setValueAtTime(880, goalAudioCtx.currentTime);
                    gain.gain.setValueAtTime(0.2, goalAudioCtx.currentTime);
                    gain.gain.exponentialRampToValueAtTime(0.01, goalAudioCtx.currentTime + 0.15);

                    osc.start(goalAudioCtx.currentTime);
                    osc.stop(goalAudioCtx.currentTime + 0.15);
                }, delay);
            });
        }

        function startAutoUpdate() {
            setInterval(() => {
                events.forEach(event => {
                    if (event.is_live && event.stats) {
                        // Update minute
                        event.minute = Math.min(90, event.minute + 1);
                        if (event.minute > 45 && event.minute < 46) event.period = 'INT';
                        else if (event.minute >= 46) event.period = '2T';

                        // Random goal chance (3%)
                        if (Math.random() < 0.03) {
                            const isHome = Math.random() < event.stats.possession.home / 100;
                            const scorerNames = ['Silva', 'Santos', 'Oliveira', 'Souza', 'Lima', 'Pereira', 'Costa', 'Ferreira', 'Rodrigues', 'Almeida', 'Nascimento', 'Araujo'];
                            const scorer = scorerNames[Math.floor(Math.random() * scorerNames.length)];

                            if (isHome) {
                                event.home_goals++;
                                event.stats.xg.home += 0.8 + Math.random() * 0.4;
                                event.events.push({minute: event.minute, type: 'goal', team: 'home', player: scorer});
                                // Show goal notification
                                showGoalNotification(event, 'home', scorer);
                            } else {
                                event.away_goals++;
                                event.stats.xg.away += 0.8 + Math.random() * 0.4;
                                event.events.push({minute: event.minute, type: 'goal', team: 'away', player: scorer});
                                // Show goal notification
                                showGoalNotification(event, 'away', scorer);
                            }
                        }

                        // Update stats dynamically
                        event.stats.possession.home = Math.max(30, Math.min(70, event.stats.possession.home + (Math.random() - 0.5) * 3));
                        event.stats.possession.away = 100 - event.stats.possession.home;

                        if (Math.random() < 0.4) {
                            if (Math.random() < event.stats.possession.home / 100) {
                                event.stats.shots.home++;
                                if (Math.random() < 0.4) event.stats.shots_on_target.home++;
                                event.stats.xg.home += Math.random() * 0.15;
                            } else {
                                event.stats.shots.away++;
                                if (Math.random() < 0.4) event.stats.shots_on_target.away++;
                                event.stats.xg.away += Math.random() * 0.15;
                            }
                        }

                        if (Math.random() < 0.15) {
                            if (Math.random() < 0.5) event.stats.corners.home++;
                            else event.stats.corners.away++;
                        }

                        if (Math.random() < 0.2) {
                            if (Math.random() < 0.5) event.stats.fouls.home++;
                            else event.stats.fouls.away++;
                        }

                        event.stats.dangerous_attacks.home += Math.floor(Math.random() * 3);
                        event.stats.dangerous_attacks.away += Math.floor(Math.random() * 2);
                        event.stats.attacks.home += Math.floor(Math.random() * 4);
                        event.stats.attacks.away += Math.floor(Math.random() * 3);
                        event.stats.passes.home += Math.floor(Math.random() * 8);
                        event.stats.passes.away += Math.floor(Math.random() * 6);

                        // Update heatmap zones
                        if (event.heatmap) {
                            event.heatmap.home_defense = Math.max(10, Math.min(90, event.heatmap.home_defense + (Math.random() - 0.5) * 8));
                            event.heatmap.home_midfield = Math.max(20, Math.min(80, event.heatmap.home_midfield + (Math.random() - 0.5) * 6));
                            event.heatmap.home_attack = Math.max(15, Math.min(95, event.heatmap.home_attack + (Math.random() - 0.5) * 10));
                            event.heatmap.away_defense = Math.max(10, Math.min(90, event.heatmap.away_defense + (Math.random() - 0.5) * 8));
                            event.heatmap.away_midfield = Math.max(20, Math.min(80, event.heatmap.away_midfield + (Math.random() - 0.5) * 6));
                            event.heatmap.away_attack = Math.max(15, Math.min(95, event.heatmap.away_attack + (Math.random() - 0.5) * 10));
                        }

                        // Update momentum
                        event.momentum = Math.max(20, Math.min(80, event.momentum + (Math.random() - 0.5) * 8));

                        // Update momentum history
                        if (event.momentum_history) {
                            const newHome = Math.round(30 + Math.random() * 60);
                            const newAway = Math.round(30 + Math.random() * 60);
                            event.momentum_history.push({
                                min: event.minute,
                                home: newHome,
                                away: newAway
                            });
                            // Keep only last 25 entries
                            if (event.momentum_history.length > 25) {
                                event.momentum_history.shift();
                            }
                        }

                        // Update predictions based on current stats
                        if (event.predictions) {
                            const homeDominance = event.stats.possession.home / 100 * 0.3 +
                                                  event.stats.shots.home / (event.stats.shots.home + event.stats.shots.away + 1) * 0.4 +
                                                  event.stats.xg.home / (event.stats.xg.home + event.stats.xg.away + 0.1) * 0.3;

                            event.predictions.home_win = Math.round(Math.max(5, Math.min(95, event.predictions.home_win + (Math.random() - 0.5) * 4)));
                            event.predictions.draw = Math.round(Math.max(5, Math.min(50, event.predictions.draw + (Math.random() - 0.5) * 3)));
                            event.predictions.away_win = 100 - event.predictions.home_win - event.predictions.draw;
                            event.predictions.next_goal_home = Math.round(homeDominance * 100);
                            event.predictions.next_goal_away = 100 - event.predictions.next_goal_home;
                        }

                        // Update odds
                        event.odds.home = Math.max(1.05, event.odds.home + (Math.random() - 0.5) * 0.08);
                        event.odds.draw = Math.max(1.05, event.odds.draw + (Math.random() - 0.5) * 0.08);
                        event.odds.away = Math.max(1.05, event.odds.away + (Math.random() - 0.5) * 0.08);
                    }
                });

                // Update match selector
                const selector = document.getElementById('heatmap-match-selector');
                const currentValue = selector.value;
                const liveEvents = events.filter(e => e.is_live);
                selector.innerHTML = liveEvents.map(e =>
                    `<option value="${e.id}" ${e.id === currentValue ? 'selected' : ''}>${e.home_team} vs ${e.away_team} (${e.minute}')</option>`
                ).join('');

                renderAll();
                showUpdateIndicator();

                // Check for goal prediction alerts
                liveEvents.forEach(event => {
                    if (event.momentum_history) {
                        checkGoalAlert(event);
                    }
                });
            }, 5000);
        }

        function showUpdateIndicator() {
            const indicator = document.getElementById('update-indicator');
            indicator.classList.add('show');
            setTimeout(() => indicator.classList.remove('show'), 1500);
        }
    </script>
</body>
</html>
""".replace('EVENTS_DATA', json.dumps(SAMPLE_EVENTS)).replace('BOOKMAKERS_DATA', json.dumps(BOOKMAKERS))


def create_server():
    """Cria servidor HTTP simples."""
    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode('utf-8'))

        def log_message(self, format, *args):
            pass

    return HTTPServer(('127.0.0.1', 8000), Handler)


def main():
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   LOBINHO-BET - Dashboard Completo com Mapa de Calor              ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
    """)

    server = create_server()

    print("Servidor iniciado!")
    print("Abrindo navegador...")
    print("")
    print("   URL: http://127.0.0.1:8000")
    print("")
    print("   Pressione Ctrl+C para parar")
    print("")

    webbrowser.open('http://127.0.0.1:8000')

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServidor parado")
        server.shutdown()


if __name__ == "__main__":
    main()
