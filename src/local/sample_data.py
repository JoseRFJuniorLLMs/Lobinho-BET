"""
Sample Data - Dados Locais para Teste
======================================
Dados de exemplo para rodar 100% offline.
"""

from datetime import datetime, timedelta
from typing import Optional
import random

# ============================================================================
# TIMES E LIGAS
# ============================================================================

TEAMS = {
    # Brasil
    "flamengo": {
        "name": "Flamengo",
        "country": "Brazil",
        "league": "Brasileirao",
        "elo": 1680,
        "squad_value": 185.0,
        "attack": 1.28,
        "defense": 1.12,
        "home_advantage": 0.15,
        "avg_goals_home": 1.8,
        "avg_goals_away": 1.4,
        "avg_conceded_home": 0.9,
        "avg_conceded_away": 1.3,
    },
    "palmeiras": {
        "name": "Palmeiras",
        "country": "Brazil",
        "league": "Brasileirao",
        "elo": 1665,
        "squad_value": 175.0,
        "attack": 1.22,
        "defense": 1.18,
        "home_advantage": 0.12,
        "avg_goals_home": 1.7,
        "avg_goals_away": 1.3,
        "avg_conceded_home": 0.8,
        "avg_conceded_away": 1.2,
    },
    "corinthians": {
        "name": "Corinthians",
        "country": "Brazil",
        "league": "Brasileirao",
        "elo": 1620,
        "squad_value": 120.0,
        "attack": 1.10,
        "defense": 1.05,
        "home_advantage": 0.18,
        "avg_goals_home": 1.5,
        "avg_goals_away": 1.1,
        "avg_conceded_home": 1.1,
        "avg_conceded_away": 1.4,
    },
    "sao_paulo": {
        "name": "Sao Paulo",
        "country": "Brazil",
        "league": "Brasileirao",
        "elo": 1610,
        "squad_value": 110.0,
        "attack": 1.08,
        "defense": 1.10,
        "home_advantage": 0.14,
        "avg_goals_home": 1.4,
        "avg_goals_away": 1.0,
        "avg_conceded_home": 1.0,
        "avg_conceded_away": 1.3,
    },
    "atletico_mg": {
        "name": "Atletico MG",
        "country": "Brazil",
        "league": "Brasileirao",
        "elo": 1635,
        "squad_value": 130.0,
        "attack": 1.15,
        "defense": 1.08,
        "home_advantage": 0.16,
        "avg_goals_home": 1.6,
        "avg_goals_away": 1.2,
        "avg_conceded_home": 1.0,
        "avg_conceded_away": 1.4,
    },
    "botafogo": {
        "name": "Botafogo",
        "country": "Brazil",
        "league": "Brasileirao",
        "elo": 1640,
        "squad_value": 95.0,
        "attack": 1.18,
        "defense": 1.05,
        "home_advantage": 0.13,
        "avg_goals_home": 1.6,
        "avg_goals_away": 1.3,
        "avg_conceded_home": 1.1,
        "avg_conceded_away": 1.3,
    },
    "fluminense": {
        "name": "Fluminense",
        "country": "Brazil",
        "league": "Brasileirao",
        "elo": 1625,
        "squad_value": 85.0,
        "attack": 1.12,
        "defense": 1.10,
        "home_advantage": 0.12,
        "avg_goals_home": 1.4,
        "avg_goals_away": 1.1,
        "avg_conceded_home": 1.0,
        "avg_conceded_away": 1.2,
    },
    "gremio": {
        "name": "Gremio",
        "country": "Brazil",
        "league": "Brasileirao",
        "elo": 1615,
        "squad_value": 90.0,
        "attack": 1.10,
        "defense": 1.08,
        "home_advantage": 0.17,
        "avg_goals_home": 1.5,
        "avg_goals_away": 1.0,
        "avg_conceded_home": 0.9,
        "avg_conceded_away": 1.4,
    },
    "internacional": {
        "name": "Internacional",
        "country": "Brazil",
        "league": "Brasileirao",
        "elo": 1610,
        "squad_value": 88.0,
        "attack": 1.08,
        "defense": 1.12,
        "home_advantage": 0.16,
        "avg_goals_home": 1.4,
        "avg_goals_away": 1.0,
        "avg_conceded_home": 0.9,
        "avg_conceded_away": 1.3,
    },
    "cruzeiro": {
        "name": "Cruzeiro",
        "country": "Brazil",
        "league": "Brasileirao",
        "elo": 1590,
        "squad_value": 75.0,
        "attack": 1.05,
        "defense": 1.02,
        "home_advantage": 0.15,
        "avg_goals_home": 1.3,
        "avg_goals_away": 1.0,
        "avg_conceded_home": 1.1,
        "avg_conceded_away": 1.4,
    },
    # Inglaterra
    "manchester_city": {
        "name": "Manchester City",
        "country": "England",
        "league": "Premier League",
        "elo": 1920,
        "squad_value": 1100.0,
        "attack": 1.45,
        "defense": 1.30,
        "home_advantage": 0.12,
        "avg_goals_home": 2.5,
        "avg_goals_away": 2.1,
        "avg_conceded_home": 0.6,
        "avg_conceded_away": 0.9,
    },
    "liverpool": {
        "name": "Liverpool",
        "country": "England",
        "league": "Premier League",
        "elo": 1880,
        "squad_value": 950.0,
        "attack": 1.40,
        "defense": 1.25,
        "home_advantage": 0.18,
        "avg_goals_home": 2.3,
        "avg_goals_away": 1.9,
        "avg_conceded_home": 0.7,
        "avg_conceded_away": 1.0,
    },
    "arsenal": {
        "name": "Arsenal",
        "country": "England",
        "league": "Premier League",
        "elo": 1860,
        "squad_value": 900.0,
        "attack": 1.35,
        "defense": 1.28,
        "home_advantage": 0.14,
        "avg_goals_home": 2.2,
        "avg_goals_away": 1.8,
        "avg_conceded_home": 0.7,
        "avg_conceded_away": 0.9,
    },
    "chelsea": {
        "name": "Chelsea",
        "country": "England",
        "league": "Premier League",
        "elo": 1780,
        "squad_value": 850.0,
        "attack": 1.25,
        "defense": 1.15,
        "home_advantage": 0.12,
        "avg_goals_home": 1.9,
        "avg_goals_away": 1.5,
        "avg_conceded_home": 0.9,
        "avg_conceded_away": 1.2,
    },
    "manchester_united": {
        "name": "Manchester United",
        "country": "England",
        "league": "Premier League",
        "elo": 1760,
        "squad_value": 800.0,
        "attack": 1.20,
        "defense": 1.10,
        "home_advantage": 0.15,
        "avg_goals_home": 1.8,
        "avg_goals_away": 1.4,
        "avg_conceded_home": 1.0,
        "avg_conceded_away": 1.3,
    },
    # Espanha
    "real_madrid": {
        "name": "Real Madrid",
        "country": "Spain",
        "league": "La Liga",
        "elo": 1900,
        "squad_value": 1050.0,
        "attack": 1.42,
        "defense": 1.28,
        "home_advantage": 0.15,
        "avg_goals_home": 2.4,
        "avg_goals_away": 2.0,
        "avg_conceded_home": 0.7,
        "avg_conceded_away": 1.0,
    },
    "barcelona": {
        "name": "Barcelona",
        "country": "Spain",
        "league": "La Liga",
        "elo": 1870,
        "squad_value": 950.0,
        "attack": 1.38,
        "defense": 1.20,
        "home_advantage": 0.16,
        "avg_goals_home": 2.3,
        "avg_goals_away": 1.9,
        "avg_conceded_home": 0.8,
        "avg_conceded_away": 1.1,
    },
    "atletico_madrid": {
        "name": "Atletico Madrid",
        "country": "Spain",
        "league": "La Liga",
        "elo": 1820,
        "squad_value": 600.0,
        "attack": 1.18,
        "defense": 1.35,
        "home_advantage": 0.14,
        "avg_goals_home": 1.8,
        "avg_goals_away": 1.4,
        "avg_conceded_home": 0.6,
        "avg_conceded_away": 0.9,
    },
    # Alemanha
    "bayern_munich": {
        "name": "Bayern Munich",
        "country": "Germany",
        "league": "Bundesliga",
        "elo": 1910,
        "squad_value": 1000.0,
        "attack": 1.48,
        "defense": 1.22,
        "home_advantage": 0.14,
        "avg_goals_home": 2.6,
        "avg_goals_away": 2.2,
        "avg_conceded_home": 0.8,
        "avg_conceded_away": 1.1,
    },
    "dortmund": {
        "name": "Borussia Dortmund",
        "country": "Germany",
        "league": "Bundesliga",
        "elo": 1820,
        "squad_value": 550.0,
        "attack": 1.32,
        "defense": 1.10,
        "home_advantage": 0.20,
        "avg_goals_home": 2.2,
        "avg_goals_away": 1.7,
        "avg_conceded_home": 1.0,
        "avg_conceded_away": 1.4,
    },
    # Italia
    "inter_milan": {
        "name": "Inter Milan",
        "country": "Italy",
        "league": "Serie A",
        "elo": 1850,
        "squad_value": 700.0,
        "attack": 1.30,
        "defense": 1.32,
        "home_advantage": 0.13,
        "avg_goals_home": 2.1,
        "avg_goals_away": 1.7,
        "avg_conceded_home": 0.6,
        "avg_conceded_away": 0.9,
    },
    "ac_milan": {
        "name": "AC Milan",
        "country": "Italy",
        "league": "Serie A",
        "elo": 1800,
        "squad_value": 550.0,
        "attack": 1.22,
        "defense": 1.18,
        "home_advantage": 0.14,
        "avg_goals_home": 1.9,
        "avg_goals_away": 1.5,
        "avg_conceded_home": 0.8,
        "avg_conceded_away": 1.1,
    },
    "juventus": {
        "name": "Juventus",
        "country": "Italy",
        "league": "Serie A",
        "elo": 1810,
        "squad_value": 580.0,
        "attack": 1.20,
        "defense": 1.25,
        "home_advantage": 0.15,
        "avg_goals_home": 1.8,
        "avg_goals_away": 1.4,
        "avg_conceded_home": 0.7,
        "avg_conceded_away": 1.0,
    },
    # Franca
    "psg": {
        "name": "Paris Saint-Germain",
        "country": "France",
        "league": "Ligue 1",
        "elo": 1870,
        "squad_value": 900.0,
        "attack": 1.42,
        "defense": 1.20,
        "home_advantage": 0.12,
        "avg_goals_home": 2.4,
        "avg_goals_away": 2.0,
        "avg_conceded_home": 0.7,
        "avg_conceded_away": 1.0,
    },
}


# ============================================================================
# HISTORICO DE FORMA (Ultimos 10 jogos)
# ============================================================================

TEAM_FORM = {
    "flamengo": "WWDWLWWDWW",
    "palmeiras": "WDWWWLWDWW",
    "corinthians": "LDWDLWDLWD",
    "sao_paulo": "DWLDWWDLDW",
    "atletico_mg": "WWDLWWDWLD",
    "botafogo": "WWWDWWLDWW",
    "fluminense": "DWWDLDWWDL",
    "gremio": "WDLDWWDWLD",
    "internacional": "DWWLDWDWWL",
    "cruzeiro": "LDWDWLDWDL",
    "manchester_city": "WWWWWDWWWW",
    "liverpool": "WWWDWWWWDW",
    "arsenal": "WWDWWWDWWW",
    "chelsea": "WDWLDWWDLW",
    "manchester_united": "DWLDWDWLDW",
    "real_madrid": "WWWWDWWWWW",
    "barcelona": "WWDWWWDWWL",
    "atletico_madrid": "DDWWDWDWWD",
    "bayern_munich": "WWWWWWDWWW",
    "dortmund": "WDWWLWWDWL",
    "inter_milan": "WWWDWWWDWW",
    "ac_milan": "DWWDWLDWWD",
    "juventus": "WDWWDWDWWD",
    "psg": "WWWWDWWWDW",
}


# ============================================================================
# CONFRONTOS DIRETOS (H2H)
# ============================================================================

H2H_RESULTS = {
    ("flamengo", "palmeiras"): "WDLWD",      # Perspectiva do primeiro time
    ("flamengo", "corinthians"): "WWDWL",
    ("flamengo", "sao_paulo"): "WDWWD",
    ("palmeiras", "corinthians"): "WDWWW",
    ("palmeiras", "sao_paulo"): "DWWDW",
    ("corinthians", "sao_paulo"): "DLDWD",
    ("manchester_city", "liverpool"): "WDWDW",
    ("manchester_city", "arsenal"): "WDWWW",
    ("manchester_city", "chelsea"): "WWWDW",
    ("liverpool", "arsenal"): "DWDWL",
    ("liverpool", "chelsea"): "WDWWW",
    ("real_madrid", "barcelona"): "WDWDL",
    ("real_madrid", "atletico_madrid"): "WDWWW",
    ("barcelona", "atletico_madrid"): "WDWDW",
    ("bayern_munich", "dortmund"): "WWWDW",
    ("inter_milan", "ac_milan"): "WWDWD",
    ("inter_milan", "juventus"): "DWWDW",
    ("ac_milan", "juventus"): "DLDWD",
}


# ============================================================================
# ODDS DE MERCADO (Simuladas)
# ============================================================================

def generate_odds(home_prob: float, draw_prob: float, away_prob: float, margin: float = 0.05) -> dict:
    """
    Gera odds com margem da casa.
    Algumas odds terao value para demonstrar o sistema.
    """
    # Adiciona variacao aleatoria para criar oportunidades de value
    variance = random.uniform(-0.08, 0.05)  # -8% a +5% de variacao

    total = home_prob + draw_prob + away_prob
    home_prob_adj = home_prob / total * (1 + margin + variance)
    draw_prob_adj = draw_prob / total * (1 + margin + random.uniform(-0.05, 0.08))
    away_prob_adj = away_prob / total * (1 + margin + random.uniform(-0.06, 0.04))

    return {
        "home": round(max(1.05, 1 / home_prob_adj), 2),
        "draw": round(max(1.05, 1 / draw_prob_adj), 2),
        "away": round(max(1.05, 1 / away_prob_adj), 2),
        "over_25": round(random.uniform(1.70, 2.10), 2),
        "under_25": round(random.uniform(1.75, 2.15), 2),
        "btts_yes": round(random.uniform(1.65, 2.00), 2),
        "btts_no": round(random.uniform(1.75, 2.20), 2),
    }


# Odds fixas para jogos especificos (com value intencional)
FIXED_ODDS = {
    "BR001": {  # Flamengo vs Palmeiras - Value no empate
        "home": 2.05,
        "draw": 3.80,  # Odd alta para empate (value!)
        "away": 3.30,
        "over_25": 1.85,
        "under_25": 1.95,
        "btts_yes": 1.75,
        "btts_no": 2.05,
    },
    "PL001": {  # Man City vs Liverpool - Value no City
        "home": 2.15,  # Odd alta para favorito (value!)
        "draw": 3.50,
        "away": 3.40,
        "over_25": 1.65,
        "under_25": 2.25,
        "btts_yes": 1.70,
        "btts_no": 2.10,
    },
    "LL001": {  # Real Madrid vs Barcelona - Value no empate
        "home": 2.10,
        "draw": 3.90,  # Value!
        "away": 3.20,
        "over_25": 1.60,
        "under_25": 2.35,
        "btts_yes": 1.55,
        "btts_no": 2.40,
    },
    "BL001": {  # Bayern vs Dortmund - Value no Bayern
        "home": 1.75,  # Value para favorito
        "draw": 4.00,
        "away": 4.50,
        "over_25": 1.50,
        "under_25": 2.60,
        "btts_yes": 1.60,
        "btts_no": 2.30,
    },
    "SA001": {  # Inter vs AC Milan - Value no Inter
        "home": 2.00,  # Value!
        "draw": 3.60,
        "away": 3.80,
        "over_25": 1.90,
        "under_25": 1.90,
        "btts_yes": 1.80,
        "btts_no": 2.00,
    },
}


def get_match_odds(match_id: str, home_prob: float, draw_prob: float, away_prob: float) -> dict:
    """Retorna odds para um jogo (fixas ou geradas)."""
    if match_id in FIXED_ODDS:
        return FIXED_ODDS[match_id]
    return generate_odds(home_prob, draw_prob, away_prob)


# ============================================================================
# JOGOS DE EXEMPLO
# ============================================================================

def get_sample_matches() -> list[dict]:
    """Retorna lista de jogos para analise."""
    matches = [
        # Brasileirao
        {
            "id": "BR001",
            "home_team": "flamengo",
            "away_team": "palmeiras",
            "league": "Brasileirao",
            "kickoff": datetime.now() + timedelta(hours=3),
        },
        {
            "id": "BR002",
            "home_team": "corinthians",
            "away_team": "sao_paulo",
            "league": "Brasileirao",
            "kickoff": datetime.now() + timedelta(hours=5),
        },
        {
            "id": "BR003",
            "home_team": "atletico_mg",
            "away_team": "botafogo",
            "league": "Brasileirao",
            "kickoff": datetime.now() + timedelta(hours=7),
        },
        {
            "id": "BR004",
            "home_team": "fluminense",
            "away_team": "gremio",
            "league": "Brasileirao",
            "kickoff": datetime.now() + timedelta(days=1),
        },
        {
            "id": "BR005",
            "home_team": "internacional",
            "away_team": "cruzeiro",
            "league": "Brasileirao",
            "kickoff": datetime.now() + timedelta(days=1, hours=2),
        },
        # Premier League
        {
            "id": "PL001",
            "home_team": "manchester_city",
            "away_team": "liverpool",
            "league": "Premier League",
            "kickoff": datetime.now() + timedelta(hours=4),
        },
        {
            "id": "PL002",
            "home_team": "arsenal",
            "away_team": "chelsea",
            "league": "Premier League",
            "kickoff": datetime.now() + timedelta(hours=6),
        },
        {
            "id": "PL003",
            "home_team": "manchester_united",
            "away_team": "arsenal",
            "league": "Premier League",
            "kickoff": datetime.now() + timedelta(days=1, hours=4),
        },
        # La Liga
        {
            "id": "LL001",
            "home_team": "real_madrid",
            "away_team": "barcelona",
            "league": "La Liga",
            "kickoff": datetime.now() + timedelta(hours=8),
        },
        {
            "id": "LL002",
            "home_team": "atletico_madrid",
            "away_team": "real_madrid",
            "league": "La Liga",
            "kickoff": datetime.now() + timedelta(days=2),
        },
        # Bundesliga
        {
            "id": "BL001",
            "home_team": "bayern_munich",
            "away_team": "dortmund",
            "league": "Bundesliga",
            "kickoff": datetime.now() + timedelta(hours=5),
        },
        # Serie A
        {
            "id": "SA001",
            "home_team": "inter_milan",
            "away_team": "ac_milan",
            "league": "Serie A",
            "kickoff": datetime.now() + timedelta(hours=6),
        },
        {
            "id": "SA002",
            "home_team": "juventus",
            "away_team": "inter_milan",
            "league": "Serie A",
            "kickoff": datetime.now() + timedelta(days=1, hours=6),
        },
        # Ligue 1
        {
            "id": "L1001",
            "home_team": "psg",
            "away_team": "ac_milan",  # Exemplo UCL
            "league": "Champions League",
            "kickoff": datetime.now() + timedelta(days=3),
        },
    ]

    return matches


def get_team_data(team_key: str) -> Optional[dict]:
    """Retorna dados de um time."""
    return TEAMS.get(team_key)


def get_team_form(team_key: str) -> str:
    """Retorna forma recente do time."""
    return TEAM_FORM.get(team_key, "DDDDD")


def get_h2h(team1: str, team2: str) -> str:
    """Retorna confrontos diretos."""
    key = (team1, team2)
    reverse_key = (team2, team1)

    if key in H2H_RESULTS:
        return H2H_RESULTS[key]
    elif reverse_key in H2H_RESULTS:
        # Inverte resultado
        result = H2H_RESULTS[reverse_key]
        inverted = result.replace("W", "X").replace("L", "W").replace("X", "L")
        return inverted
    else:
        return "DDDDD"
