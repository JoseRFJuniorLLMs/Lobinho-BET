"""
Team Analysis - Pré-análise de Elencos
======================================
Analisa dados históricos de:
- Compras/Vendas de jogadores
- Investimentos do clube
- Valor do elenco
- Idade média
- Lesões/Suspensões
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional
from enum import Enum
import httpx
from bs4 import BeautifulSoup
from loguru import logger

from src.collectors.transfermarkt import TransfermarktScraper, TEAM_URLS


class TransferType(Enum):
    """Tipo de transferência."""
    PURCHASE = "purchase"
    SALE = "sale"
    LOAN_IN = "loan_in"
    LOAN_OUT = "loan_out"
    FREE = "free"


@dataclass
class Transfer:
    """Representa uma transferência."""
    player_name: str
    player_position: str
    from_team: str
    to_team: str
    fee: float  # em milhões EUR
    transfer_type: TransferType
    date: date
    age: int = 0
    market_value: float = 0  # valor de mercado em milhões EUR


@dataclass
class Player:
    """Jogador do elenco."""
    name: str
    position: str
    age: int
    market_value: float  # milhões EUR
    contract_until: Optional[date] = None
    is_injured: bool = False
    is_suspended: bool = False
    injury_return_date: Optional[date] = None
    goals: int = 0
    assists: int = 0
    minutes_played: int = 0


@dataclass
class TeamProfile:
    """Perfil completo de um time."""
    team_id: str
    name: str
    country: str
    league: str

    # Valor do elenco
    squad_value: float = 0  # milhões EUR
    avg_player_value: float = 0
    avg_age: float = 0

    # Transferências da temporada
    transfers_in: list[Transfer] = field(default_factory=list)
    transfers_out: list[Transfer] = field(default_factory=list)
    total_spent: float = 0  # milhões EUR
    total_earned: float = 0
    net_spend: float = 0

    # Elenco atual
    squad: list[Player] = field(default_factory=list)
    injured_players: list[Player] = field(default_factory=list)
    suspended_players: list[Player] = field(default_factory=list)

    # Estatísticas
    goals_scored: int = 0
    goals_conceded: int = 0
    clean_sheets: int = 0

    # Análise
    investment_score: float = 0  # 0-100
    squad_depth_score: float = 0  # 0-100
    injury_impact: float = 0  # % do valor do elenco lesionado

    def calculate_scores(self):
        """Calcula scores de análise."""
        # Investment Score - quanto investiu vs média
        if self.total_spent > 0:
            self.investment_score = min(100, (self.total_spent / 50) * 100)  # 50M = score 100

        # Squad Depth - baseado em tamanho e valor
        if self.squad:
            self.squad_depth_score = min(100, len(self.squad) * 3)

        # Injury Impact - % do valor lesionado
        if self.squad_value > 0:
            injured_value = sum(p.market_value for p in self.injured_players)
            self.injury_impact = (injured_value / self.squad_value) * 100

    def get_analysis_summary(self) -> dict:
        """Retorna resumo da análise."""
        self.calculate_scores()

        return {
            "team": self.name,
            "squad_value_millions": round(self.squad_value, 2),
            "avg_age": round(self.avg_age, 1),
            "avg_player_value": round(self.avg_player_value, 2),
            "transfers": {
                "spent": round(self.total_spent, 2),
                "earned": round(self.total_earned, 2),
                "net": round(self.net_spend, 2),
                "players_in": len(self.transfers_in),
                "players_out": len(self.transfers_out),
            },
            "squad_size": len(self.squad),
            "injuries": {
                "count": len(self.injured_players),
                "players": [p.name for p in self.injured_players],
                "impact_percent": round(self.injury_impact, 1),
            },
            "suspensions": {
                "count": len(self.suspended_players),
                "players": [p.name for p in self.suspended_players],
            },
            "scores": {
                "investment": round(self.investment_score, 1),
                "squad_depth": round(self.squad_depth_score, 1),
            },
        }


class TeamAnalyzer:
    """
    Analisador de times.

    Coleta dados de:
    - Transfermarkt (valor de mercado, transferências)
    - FBref (estatísticas)
    - Sites de notícias (lesões)
    """

    # URLs base
    TRANSFERMARKT_BASE = "https://www.transfermarkt.com"

    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None
        self.cache: dict[str, TeamProfile] = {}

    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            },
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def analyze_team(self, team_name: str, league: str = "") -> TeamProfile:
        """
        Analisa um time completo.

        Args:
            team_name: Nome do time
            league: Liga (para disambiguação)

        Returns:
            TeamProfile com análise completa
        """
        # Verifica cache
        cache_key = f"{team_name}_{league}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        logger.info(f"Analyzing team: {team_name}")

        profile = TeamProfile(
            team_id=cache_key,
            name=team_name,
            country="",
            league=league,
        )

        # Coleta dados de várias fontes
        try:
            # Transferências e valor de mercado
            await self._fetch_transfer_data(profile)

            # Lesões atuais
            await self._fetch_injury_data(profile)

            # Calcula scores
            profile.calculate_scores()

        except Exception as e:
            logger.error(f"Error analyzing {team_name}: {e}")

        # Cache resultado
        self.cache[cache_key] = profile
        return profile

    async def _fetch_transfer_data(self, profile: TeamProfile):
        """
        Busca dados de transferências do Transfermarkt.
        """
        logger.debug(f"Fetching transfer data for {profile.name}")

        try:
            # Verifica se time tem URL no Transfermarkt
            team_key = profile.name.lower().replace(" ", "_")
            tm_url = TEAM_URLS.get(team_key)

            if not tm_url:
                # Tenta buscar nome alternativo
                for key, url in TEAM_URLS.items():
                    if profile.name.lower() in key or key in profile.name.lower():
                        tm_url = url
                        break

            if not tm_url:
                logger.warning(f"No Transfermarkt URL for {profile.name}")
                return

            # Usa scraper do Transfermarkt
            async with TransfermarktScraper() as scraper:
                team_data = await scraper.get_team_data(tm_url)

                if team_data:
                    # Atualiza profile com dados reais
                    profile.squad_value = team_data.get("squad_value", 0)
                    profile.avg_age = team_data.get("avg_age", 0)
                    profile.total_spent = team_data.get("total_spent", 0)
                    profile.total_earned = team_data.get("total_earned", 0)
                    profile.net_spend = profile.total_spent - profile.total_earned

                    # Converte transferências
                    for t in team_data.get("transfers_in", []):
                        profile.transfers_in.append(Transfer(
                            player_name=t.get("player", "Unknown"),
                            player_position=t.get("position", ""),
                            from_team=t.get("from_team", ""),
                            to_team=profile.name,
                            fee=t.get("fee", 0),
                            transfer_type=TransferType.PURCHASE,
                            date=date.today(),
                            market_value=t.get("market_value", 0),
                        ))

                    for t in team_data.get("transfers_out", []):
                        profile.transfers_out.append(Transfer(
                            player_name=t.get("player", "Unknown"),
                            player_position=t.get("position", ""),
                            from_team=profile.name,
                            to_team=t.get("to_team", ""),
                            fee=t.get("fee", 0),
                            transfer_type=TransferType.SALE,
                            date=date.today(),
                            market_value=t.get("market_value", 0),
                        ))

                    # Converte jogadores
                    for p in team_data.get("players", []):
                        player = Player(
                            name=p.get("name", "Unknown"),
                            position=p.get("position", ""),
                            age=p.get("age", 0),
                            market_value=p.get("market_value", 0),
                            is_injured=p.get("injured", False),
                            is_suspended=p.get("suspended", False),
                        )
                        profile.squad.append(player)

                        if player.is_injured:
                            profile.injured_players.append(player)
                        if player.is_suspended:
                            profile.suspended_players.append(player)

                    logger.info(f"Loaded Transfermarkt data for {profile.name}: "
                               f"Value={profile.squad_value}M, Spent={profile.total_spent}M")

        except Exception as e:
            logger.error(f"Error fetching Transfermarkt data for {profile.name}: {e}")

    async def _fetch_injury_data(self, profile: TeamProfile):
        """
        Busca dados de lesões atuais do Transfermarkt.
        """
        logger.debug(f"Fetching injury data for {profile.name}")

        try:
            # Verifica se time tem URL no Transfermarkt
            team_key = profile.name.lower().replace(" ", "_")
            tm_url = TEAM_URLS.get(team_key)

            if not tm_url:
                for key, url in TEAM_URLS.items():
                    if profile.name.lower() in key or key in profile.name.lower():
                        tm_url = url
                        break

            if not tm_url:
                return

            # Usa scraper para buscar lesões
            async with TransfermarktScraper() as scraper:
                injuries = await scraper.get_injuries(tm_url)

                for injury in injuries:
                    # Atualiza jogador existente ou adiciona novo
                    player_name = injury.get("player", "")
                    existing = next((p for p in profile.squad if p.name == player_name), None)

                    if existing:
                        existing.is_injured = True
                        if existing not in profile.injured_players:
                            profile.injured_players.append(existing)
                    else:
                        # Cria jogador apenas com info de lesão
                        player = Player(
                            name=player_name,
                            position=injury.get("position", ""),
                            age=0,
                            market_value=0,
                            is_injured=True,
                        )
                        profile.injured_players.append(player)

                logger.info(f"Found {len(profile.injured_players)} injured players for {profile.name}")

        except Exception as e:
            logger.error(f"Error fetching injury data for {profile.name}: {e}")

    async def compare_teams(
        self,
        home_team: str,
        away_team: str,
        league: str = "",
    ) -> dict:
        """
        Compara dois times para pré-análise.

        Returns:
            Dict com comparação e vantagens
        """
        home_profile = await self.analyze_team(home_team, league)
        away_profile = await self.analyze_team(away_team, league)

        home_summary = home_profile.get_analysis_summary()
        away_summary = away_profile.get_analysis_summary()

        comparison = {
            "home": home_summary,
            "away": away_summary,
            "advantages": {
                "home": [],
                "away": [],
            },
            "concerns": {
                "home": [],
                "away": [],
            },
        }

        # Analisa vantagens de valor de elenco
        if home_profile.squad_value > away_profile.squad_value * 1.2:
            comparison["advantages"]["home"].append(
                f"Elenco mais valioso ({home_profile.squad_value:.1f}M vs {away_profile.squad_value:.1f}M)"
            )
        elif away_profile.squad_value > home_profile.squad_value * 1.2:
            comparison["advantages"]["away"].append(
                f"Elenco mais valioso ({away_profile.squad_value:.1f}M vs {home_profile.squad_value:.1f}M)"
            )

        # Analisa investimentos recentes
        if home_profile.total_spent > away_profile.total_spent * 1.5:
            comparison["advantages"]["home"].append(
                f"Investiu mais na temporada ({home_profile.total_spent:.1f}M)"
            )
        elif away_profile.total_spent > home_profile.total_spent * 1.5:
            comparison["advantages"]["away"].append(
                f"Investiu mais na temporada ({away_profile.total_spent:.1f}M)"
            )

        # Analisa lesões
        if home_profile.injury_impact > 15:
            comparison["concerns"]["home"].append(
                f"Muitos lesionados ({home_profile.injury_impact:.1f}% do elenco)"
            )
        if away_profile.injury_impact > 15:
            comparison["concerns"]["away"].append(
                f"Muitos lesionados ({away_profile.injury_impact:.1f}% do elenco)"
            )

        # Score geral de vantagem
        home_advantage_score = (
            (home_profile.squad_value - away_profile.squad_value) / 100 * 0.4
            + (home_profile.total_spent - away_profile.total_spent) / 50 * 0.3
            - home_profile.injury_impact * 0.02
            + away_profile.injury_impact * 0.02
        )

        comparison["advantage_score"] = {
            "value": round(home_advantage_score, 2),
            "favors": "home" if home_advantage_score > 0 else "away" if home_advantage_score < 0 else "neutral",
            "strength": "strong" if abs(home_advantage_score) > 2 else "moderate" if abs(home_advantage_score) > 1 else "slight",
        }

        return comparison


# ============================================================================
# DADOS DE EXEMPLO (em produção, viriam de APIs/scraping)
# ============================================================================

SAMPLE_TEAM_DATA = {
    "Flamengo": TeamProfile(
        team_id="flamengo",
        name="Flamengo",
        country="Brazil",
        league="Brasileirao",
        squad_value=180.5,
        avg_age=27.2,
        total_spent=45.0,
        total_earned=20.0,
        net_spend=25.0,
    ),
    "Palmeiras": TeamProfile(
        team_id="palmeiras",
        name="Palmeiras",
        country="Brazil",
        league="Brasileirao",
        squad_value=165.0,
        avg_age=26.8,
        total_spent=35.0,
        total_earned=15.0,
        net_spend=20.0,
    ),
    "Manchester City": TeamProfile(
        team_id="man_city",
        name="Manchester City",
        country="England",
        league="Premier League",
        squad_value=1100.0,
        avg_age=27.5,
        total_spent=150.0,
        total_earned=50.0,
        net_spend=100.0,
    ),
    "Real Madrid": TeamProfile(
        team_id="real_madrid",
        name="Real Madrid",
        country="Spain",
        league="La Liga",
        squad_value=1050.0,
        avg_age=28.0,
        total_spent=100.0,
        total_earned=80.0,
        net_spend=20.0,
    ),
}


async def get_pre_match_analysis(home_team: str, away_team: str) -> dict:
    """
    Gera pré-análise completa para uma partida.

    Combina:
    - Valor de elenco
    - Investimentos
    - Lesões
    - Histórico recente
    """
    async with TeamAnalyzer() as analyzer:
        comparison = await analyzer.compare_teams(home_team, away_team)

    return {
        "pre_analysis": comparison,
        "recommendation": _generate_recommendation(comparison),
    }


def _generate_recommendation(comparison: dict) -> str:
    """Gera recomendação baseada na pré-análise."""
    adv_score = comparison.get("advantage_score", {})
    favors = adv_score.get("favors", "neutral")
    strength = adv_score.get("strength", "slight")

    if favors == "neutral":
        return "⚖️ Times equilibrados na pré-análise. Foco nos dados em tempo real."

    team = "mandante" if favors == "home" else "visitante"

    if strength == "strong":
        return f"🔥 Vantagem forte para o {team}. Considerar apostar a favor."
    elif strength == "moderate":
        return f"✅ Vantagem moderada para o {team}. Verificar odds."
    else:
        return f"📊 Leve vantagem para o {team}. Aguardar mais dados."
