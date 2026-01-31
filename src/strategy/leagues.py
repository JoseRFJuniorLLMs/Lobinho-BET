"""
League/Competition Manager
==========================
Gerencia campeonatos monitorados e suas configurações.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class LeaguePriority(Enum):
    """Prioridade do campeonato para análise."""
    HIGH = 1      # Campeonatos principais - mais dados, mais confiável
    MEDIUM = 2    # Campeonatos secundários - dados razoáveis
    LOW = 3       # Campeonatos menores - poucos dados, mais arriscado


@dataclass
class League:
    """Configuração de um campeonato."""

    id: str
    name: str
    country: str
    priority: LeaguePriority = LeaguePriority.MEDIUM

    # IDs nas diferentes APIs
    footystats_id: Optional[int] = None
    odds_api_key: Optional[str] = None
    fbref_path: Optional[str] = None

    # Configurações de aposta
    enabled: bool = True
    min_edge: float = 5.0  # Edge mínimo para apostar (%)
    max_stake: float = 3.0  # Stake máximo (% da banca)

    # Mercados permitidos
    allowed_markets: list[str] = field(default_factory=lambda: [
        "home", "draw", "away", "over_2.5", "under_2.5", "btts_yes"
    ])


# ============================================================================
# CAMPEONATOS CONFIGURADOS
# ============================================================================

LEAGUES = {
    # ===================
    # BRASIL
    # ===================
    "brasileirao_a": League(
        id="brasileirao_a",
        name="Brasileirão Série A",
        country="Brazil",
        priority=LeaguePriority.HIGH,
        footystats_id=1625,
        odds_api_key="soccer_brazil_serie_a",
        fbref_path="/en/comps/24/Serie-A-Stats",
        min_edge=4.0,
        max_stake=3.0,
    ),
    "brasileirao_b": League(
        id="brasileirao_b",
        name="Brasileirão Série B",
        country="Brazil",
        priority=LeaguePriority.MEDIUM,
        footystats_id=1626,
        odds_api_key="soccer_brazil_serie_b",
        min_edge=5.0,
        max_stake=2.5,
    ),
    "copa_do_brasil": League(
        id="copa_do_brasil",
        name="Copa do Brasil",
        country="Brazil",
        priority=LeaguePriority.MEDIUM,
        footystats_id=1627,
        min_edge=6.0,
        max_stake=2.0,
    ),

    # ===================
    # EUROPA TOP 5
    # ===================
    "premier_league": League(
        id="premier_league",
        name="Premier League",
        country="England",
        priority=LeaguePriority.HIGH,
        footystats_id=1204,
        odds_api_key="soccer_epl",
        fbref_path="/en/comps/9/Premier-League-Stats",
        min_edge=4.0,
        max_stake=3.0,
    ),
    "la_liga": League(
        id="la_liga",
        name="La Liga",
        country="Spain",
        priority=LeaguePriority.HIGH,
        footystats_id=1399,
        odds_api_key="soccer_spain_la_liga",
        fbref_path="/en/comps/12/La-Liga-Stats",
        min_edge=4.0,
        max_stake=3.0,
    ),
    "bundesliga": League(
        id="bundesliga",
        name="Bundesliga",
        country="Germany",
        priority=LeaguePriority.HIGH,
        footystats_id=1229,
        odds_api_key="soccer_germany_bundesliga",
        fbref_path="/en/comps/20/Bundesliga-Stats",
        min_edge=4.0,
        max_stake=3.0,
    ),
    "serie_a_italy": League(
        id="serie_a_italy",
        name="Serie A",
        country="Italy",
        priority=LeaguePriority.HIGH,
        footystats_id=1387,
        odds_api_key="soccer_italy_serie_a",
        fbref_path="/en/comps/11/Serie-A-Stats",
        min_edge=4.0,
        max_stake=3.0,
    ),
    "ligue_1": League(
        id="ligue_1",
        name="Ligue 1",
        country="France",
        priority=LeaguePriority.HIGH,
        footystats_id=1221,
        odds_api_key="soccer_france_ligue_one",
        fbref_path="/en/comps/13/Ligue-1-Stats",
        min_edge=4.5,
        max_stake=2.5,
    ),

    # ===================
    # COMPETIÇÕES EUROPEIAS
    # ===================
    "champions_league": League(
        id="champions_league",
        name="UEFA Champions League",
        country="Europe",
        priority=LeaguePriority.HIGH,
        footystats_id=1007,
        odds_api_key="soccer_uefa_champs_league",
        fbref_path="/en/comps/8/Champions-League-Stats",
        min_edge=5.0,
        max_stake=2.5,
    ),
    "europa_league": League(
        id="europa_league",
        name="UEFA Europa League",
        country="Europe",
        priority=LeaguePriority.MEDIUM,
        footystats_id=1017,
        odds_api_key="soccer_uefa_europa_league",
        min_edge=5.5,
        max_stake=2.0,
    ),

    # ===================
    # AMÉRICA DO SUL
    # ===================
    "libertadores": League(
        id="libertadores",
        name="Copa Libertadores",
        country="South America",
        priority=LeaguePriority.HIGH,
        footystats_id=1100,
        odds_api_key="soccer_conmebol_libertadores",
        fbref_path="/en/comps/14/Copa-Libertadores-Stats",
        min_edge=5.0,
        max_stake=2.5,
    ),
    "sulamericana": League(
        id="sulamericana",
        name="Copa Sulamericana",
        country="South America",
        priority=LeaguePriority.MEDIUM,
        footystats_id=1101,
        min_edge=6.0,
        max_stake=2.0,
    ),
    "argentina_primera": League(
        id="argentina_primera",
        name="Argentina Primera División",
        country="Argentina",
        priority=LeaguePriority.MEDIUM,
        footystats_id=1600,
        odds_api_key="soccer_argentina_primera_division",
        min_edge=5.0,
        max_stake=2.5,
    ),

    # ===================
    # OUTROS EUROPEUS
    # ===================
    "eredivisie": League(
        id="eredivisie",
        name="Eredivisie",
        country="Netherlands",
        priority=LeaguePriority.MEDIUM,
        footystats_id=1322,
        min_edge=5.0,
        max_stake=2.5,
    ),
    "primeira_liga": League(
        id="primeira_liga",
        name="Primeira Liga",
        country="Portugal",
        priority=LeaguePriority.MEDIUM,
        footystats_id=1352,
        min_edge=5.0,
        max_stake=2.5,
    ),
}


class LeagueManager:
    """Gerenciador de campeonatos."""

    def __init__(self, leagues: dict[str, League] = None):
        self.leagues = leagues or LEAGUES

    def get_league(self, league_id: str) -> Optional[League]:
        """Retorna um campeonato pelo ID."""
        return self.leagues.get(league_id)

    def get_enabled_leagues(self) -> list[League]:
        """Retorna campeonatos ativos."""
        return [lg for lg in self.leagues.values() if lg.enabled]

    def get_by_priority(self, priority: LeaguePriority) -> list[League]:
        """Retorna campeonatos por prioridade."""
        return [
            lg for lg in self.leagues.values()
            if lg.enabled and lg.priority == priority
        ]

    def get_high_priority(self) -> list[League]:
        """Retorna campeonatos de alta prioridade."""
        return self.get_by_priority(LeaguePriority.HIGH)

    def get_by_country(self, country: str) -> list[League]:
        """Retorna campeonatos de um país."""
        return [
            lg for lg in self.leagues.values()
            if lg.enabled and lg.country.lower() == country.lower()
        ]

    def get_brazil_leagues(self) -> list[League]:
        """Retorna campeonatos brasileiros."""
        return self.get_by_country("Brazil")

    def get_footystats_ids(self) -> list[int]:
        """Retorna IDs do FootyStats de todos campeonatos ativos."""
        return [
            lg.footystats_id for lg in self.get_enabled_leagues()
            if lg.footystats_id
        ]

    def get_odds_api_keys(self) -> list[str]:
        """Retorna keys do Odds API de todos campeonatos ativos."""
        return [
            lg.odds_api_key for lg in self.get_enabled_leagues()
            if lg.odds_api_key
        ]

    def enable_league(self, league_id: str) -> bool:
        """Ativa um campeonato."""
        if league_id in self.leagues:
            self.leagues[league_id].enabled = True
            return True
        return False

    def disable_league(self, league_id: str) -> bool:
        """Desativa um campeonato."""
        if league_id in self.leagues:
            self.leagues[league_id].enabled = False
            return True
        return False

    def set_min_edge(self, league_id: str, min_edge: float) -> bool:
        """Define edge mínimo para um campeonato."""
        if league_id in self.leagues:
            self.leagues[league_id].min_edge = min_edge
            return True
        return False

    def list_all(self) -> list[dict]:
        """Lista todos os campeonatos com status."""
        return [
            {
                "id": lg.id,
                "name": lg.name,
                "country": lg.country,
                "priority": lg.priority.name,
                "enabled": lg.enabled,
                "min_edge": lg.min_edge,
                "max_stake": lg.max_stake,
            }
            for lg in self.leagues.values()
        ]
