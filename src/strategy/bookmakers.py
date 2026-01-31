"""
Bookmakers - Casas de Apostas
=============================
Links diretos para casas de apostas e gestão de redirecionamento.
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class BookmakerRegion(Enum):
    """Região da casa de apostas."""
    BRAZIL = "brazil"
    GLOBAL = "global"
    EUROPE = "europe"


@dataclass
class Bookmaker:
    """Casa de apostas."""

    id: str
    name: str
    region: BookmakerRegion
    base_url: str
    logo_url: str
    affiliate_code: Optional[str] = None

    # Qualidade
    odds_quality: int = 3  # 1-5 (5 = melhores odds)
    payout_speed: int = 3  # 1-5 (5 = mais rápido)
    reliability: int = 3   # 1-5 (5 = mais confiável)

    # Status
    is_active: bool = True
    accepts_pix: bool = False
    min_deposit: float = 10.0
    min_bet: float = 1.0

    def get_event_url(self, event_id: str = "", sport: str = "futebol") -> str:
        """Gera URL para evento específico."""
        url = self.base_url

        # Adiciona código de afiliado se existir
        if self.affiliate_code:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}ref={self.affiliate_code}"

        return url

    def get_registration_url(self) -> str:
        """URL de cadastro com código de afiliado."""
        url = f"{self.base_url}/registro"
        if self.affiliate_code:
            url = f"{url}?ref={self.affiliate_code}"
        return url


# ============================================================================
# CASAS DE APOSTAS CONFIGURADAS
# ============================================================================

BOOKMAKERS = {
    # ===================
    # BRASIL
    # ===================
    "bet365": Bookmaker(
        id="bet365",
        name="Bet365",
        region=BookmakerRegion.BRAZIL,
        base_url="https://www.bet365.com",
        logo_url="/static/logos/bet365.png",
        odds_quality=5,
        payout_speed=4,
        reliability=5,
        accepts_pix=True,
        min_deposit=20.0,
    ),
    "betano": Bookmaker(
        id="betano",
        name="Betano",
        region=BookmakerRegion.BRAZIL,
        base_url="https://www.betano.com.br",
        logo_url="/static/logos/betano.png",
        odds_quality=4,
        payout_speed=5,
        reliability=5,
        accepts_pix=True,
        min_deposit=10.0,
    ),
    "sportingbet": Bookmaker(
        id="sportingbet",
        name="Sportingbet",
        region=BookmakerRegion.BRAZIL,
        base_url="https://www.sportingbet.com",
        logo_url="/static/logos/sportingbet.png",
        odds_quality=4,
        payout_speed=4,
        reliability=4,
        accepts_pix=True,
        min_deposit=10.0,
    ),
    "pixbet": Bookmaker(
        id="pixbet",
        name="PixBet",
        region=BookmakerRegion.BRAZIL,
        base_url="https://www.pixbet.com",
        logo_url="/static/logos/pixbet.png",
        odds_quality=3,
        payout_speed=5,
        reliability=4,
        accepts_pix=True,
        min_deposit=1.0,
        min_bet=0.50,
    ),
    "estrelabet": Bookmaker(
        id="estrelabet",
        name="EstrelaBet",
        region=BookmakerRegion.BRAZIL,
        base_url="https://www.estrelabet.com",
        logo_url="/static/logos/estrelabet.png",
        odds_quality=3,
        payout_speed=4,
        reliability=4,
        accepts_pix=True,
        min_deposit=5.0,
    ),
    "novibet": Bookmaker(
        id="novibet",
        name="Novibet",
        region=BookmakerRegion.BRAZIL,
        base_url="https://www.novibet.com.br",
        logo_url="/static/logos/novibet.png",
        odds_quality=4,
        payout_speed=4,
        reliability=4,
        accepts_pix=True,
        min_deposit=20.0,
    ),
    "betfair": Bookmaker(
        id="betfair",
        name="Betfair",
        region=BookmakerRegion.BRAZIL,
        base_url="https://www.betfair.com",
        logo_url="/static/logos/betfair.png",
        odds_quality=5,  # Exchange = melhores odds
        payout_speed=4,
        reliability=5,
        accepts_pix=True,
        min_deposit=20.0,
    ),
    "1xbet": Bookmaker(
        id="1xbet",
        name="1xBet",
        region=BookmakerRegion.BRAZIL,
        base_url="https://www.1xbet.com",
        logo_url="/static/logos/1xbet.png",
        odds_quality=5,
        payout_speed=3,
        reliability=3,
        accepts_pix=True,
        min_deposit=5.0,
    ),
    "pinnacle": Bookmaker(
        id="pinnacle",
        name="Pinnacle",
        region=BookmakerRegion.GLOBAL,
        base_url="https://www.pinnacle.com",
        logo_url="/static/logos/pinnacle.png",
        odds_quality=5,  # Referência do mercado
        payout_speed=4,
        reliability=5,
        accepts_pix=False,
        min_deposit=50.0,
    ),
    "betway": Bookmaker(
        id="betway",
        name="Betway",
        region=BookmakerRegion.BRAZIL,
        base_url="https://www.betway.com",
        logo_url="/static/logos/betway.png",
        odds_quality=4,
        payout_speed=4,
        reliability=4,
        accepts_pix=True,
        min_deposit=15.0,
    ),
    "betnacional": Bookmaker(
        id="betnacional",
        name="Bet Nacional",
        region=BookmakerRegion.BRAZIL,
        base_url="https://www.betnacional.com",
        logo_url="/static/logos/betnacional.png",
        odds_quality=3,
        payout_speed=4,
        reliability=3,
        accepts_pix=True,
        min_deposit=5.0,
    ),
    "f12bet": Bookmaker(
        id="f12bet",
        name="F12.Bet",
        region=BookmakerRegion.BRAZIL,
        base_url="https://www.f12.bet",
        logo_url="/static/logos/f12bet.png",
        odds_quality=3,
        payout_speed=5,
        reliability=3,
        accepts_pix=True,
        min_deposit=5.0,
    ),
}


class BookmakerManager:
    """Gerenciador de casas de apostas."""

    def __init__(self):
        self.bookmakers = BOOKMAKERS

    def get_all(self) -> list[Bookmaker]:
        """Retorna todas as casas ativas."""
        return [b for b in self.bookmakers.values() if b.is_active]

    def get_by_id(self, bookmaker_id: str) -> Optional[Bookmaker]:
        """Retorna casa por ID."""
        return self.bookmakers.get(bookmaker_id)

    def get_brazil_bookmakers(self) -> list[Bookmaker]:
        """Retorna casas que operam no Brasil."""
        return [
            b for b in self.bookmakers.values()
            if b.is_active and b.region == BookmakerRegion.BRAZIL
        ]

    def get_with_pix(self) -> list[Bookmaker]:
        """Retorna casas que aceitam PIX."""
        return [b for b in self.bookmakers.values() if b.is_active and b.accepts_pix]

    def get_best_odds(self) -> list[Bookmaker]:
        """Retorna casas com melhores odds (quality >= 4)."""
        return sorted(
            [b for b in self.bookmakers.values() if b.is_active and b.odds_quality >= 4],
            key=lambda x: x.odds_quality,
            reverse=True,
        )

    def get_by_reliability(self, min_reliability: int = 4) -> list[Bookmaker]:
        """Retorna casas confiáveis."""
        return [
            b for b in self.bookmakers.values()
            if b.is_active and b.reliability >= min_reliability
        ]

    def compare_bookmakers(self, bookmaker_ids: list[str]) -> dict:
        """Compara casas de apostas."""
        bookmakers = [self.get_by_id(bid) for bid in bookmaker_ids if self.get_by_id(bid)]

        return {
            "bookmakers": [
                {
                    "id": b.id,
                    "name": b.name,
                    "odds_quality": b.odds_quality,
                    "payout_speed": b.payout_speed,
                    "reliability": b.reliability,
                    "accepts_pix": b.accepts_pix,
                    "min_deposit": b.min_deposit,
                    "url": b.base_url,
                }
                for b in bookmakers
            ],
            "best_odds": max(bookmakers, key=lambda x: x.odds_quality).name if bookmakers else None,
            "fastest_payout": max(bookmakers, key=lambda x: x.payout_speed).name if bookmakers else None,
            "most_reliable": max(bookmakers, key=lambda x: x.reliability).name if bookmakers else None,
        }


def get_best_bookmaker_for_odds(odds_data: dict) -> dict:
    """
    Encontra a melhor casa para cada seleção.

    Args:
        odds_data: Dict com odds de várias casas

    Returns:
        Dict com melhor casa para cada mercado
    """
    result = {
        "home": {"bookmaker": None, "odds": 0},
        "draw": {"bookmaker": None, "odds": 0},
        "away": {"bookmaker": None, "odds": 0},
    }

    for bookmaker_id, odds in odds_data.items():
        if odds.get("home", 0) > result["home"]["odds"]:
            result["home"] = {"bookmaker": bookmaker_id, "odds": odds["home"]}
        if odds.get("draw", 0) > result["draw"]["odds"]:
            result["draw"] = {"bookmaker": bookmaker_id, "odds": odds["draw"]}
        if odds.get("away", 0) > result["away"]["odds"]:
            result["away"] = {"bookmaker": bookmaker_id, "odds": odds["away"]}

    return result
