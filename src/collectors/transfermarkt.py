"""
Transfermarkt Scraper
=====================
Coleta dados reais de:
- Valor de mercado dos times
- Transferências
- Jogadores e lesões
- Histórico de técnicos

Fonte: transfermarkt.com
"""

import asyncio
import re
from typing import Optional
from datetime import datetime, date
from dataclasses import dataclass, field
from playwright.async_api import async_playwright, Page
from bs4 import BeautifulSoup
import httpx
from loguru import logger


@dataclass
class TransferData:
    """Dados de transferência."""
    player_name: str
    from_team: str
    to_team: str
    fee: float  # Em milhões EUR
    date: date
    player_age: int = 0
    player_position: str = ""
    market_value: float = 0


@dataclass
class PlayerData:
    """Dados de jogador."""
    name: str
    position: str
    age: int
    nationality: str
    market_value: float  # Em milhões EUR
    contract_until: Optional[date] = None
    is_injured: bool = False
    injury_type: str = ""
    return_date: Optional[date] = None
    goals: int = 0
    assists: int = 0


@dataclass
class TeamMarketData:
    """Dados de mercado de um time."""
    team_name: str
    squad_value: float  # Em milhões EUR
    avg_age: float
    avg_market_value: float
    squad_size: int
    foreigners_count: int
    national_players: int

    # Transferências da temporada
    arrivals: list[TransferData] = field(default_factory=list)
    departures: list[TransferData] = field(default_factory=list)
    total_spent: float = 0
    total_earned: float = 0
    net_spend: float = 0

    # Jogadores
    players: list[PlayerData] = field(default_factory=list)
    injured_players: list[PlayerData] = field(default_factory=list)

    # Técnico
    coach_name: str = ""
    coach_since: Optional[date] = None


class TransfermarktScraper:
    """
    Scraper para Transfermarkt.

    Coleta dados reais de times, jogadores e transferências.
    """

    BASE_URL = "https://www.transfermarkt.com"

    # Mapeamento de times para URLs do Transfermarkt
    TEAM_URLS = {
        # Brasil
        "Flamengo": "/flamengo-rio-de-janeiro/startseite/verein/614",
        "Palmeiras": "/se-palmeiras/startseite/verein/1023",
        "Corinthians": "/corinthians-sao-paulo/startseite/verein/199",
        "São Paulo": "/fc-sao-paulo/startseite/verein/585",
        "Santos": "/santos-fc/startseite/verein/1097",
        "Fluminense": "/fluminense-fc/startseite/verein/2462",
        "Botafogo": "/botafogo-fr/startseite/verein/537",
        "Athletico-PR": "/club-athletico-paranaense/startseite/verein/679",
        "Internacional": "/sport-club-internacional/startseite/verein/6600",
        "Grêmio": "/gremio-fb-porto-alegrense/startseite/verein/210",
        "Atlético-MG": "/clube-atletico-mineiro/startseite/verein/330",
        "Cruzeiro": "/cruzeiro-ec/startseite/verein/609",

        # Inglaterra
        "Manchester City": "/manchester-city/startseite/verein/281",
        "Liverpool": "/fc-liverpool/startseite/verein/31",
        "Arsenal": "/fc-arsenal/startseite/verein/11",
        "Chelsea": "/fc-chelsea/startseite/verein/631",
        "Manchester United": "/manchester-united/startseite/verein/985",
        "Tottenham": "/tottenham-hotspur/startseite/verein/148",

        # Espanha
        "Real Madrid": "/real-madrid/startseite/verein/418",
        "Barcelona": "/fc-barcelona/startseite/verein/131",
        "Atletico Madrid": "/atletico-madrid/startseite/verein/13",

        # Itália
        "Juventus": "/juventus-turin/startseite/verein/506",
        "Inter Milan": "/inter-mailand/startseite/verein/46",
        "AC Milan": "/ac-mailand/startseite/verein/5",
        "Napoli": "/ssc-neapel/startseite/verein/6195",

        # Alemanha
        "Bayern Munich": "/fc-bayern-munchen/startseite/verein/27",
        "Borussia Dortmund": "/borussia-dortmund/startseite/verein/16",

        # França
        "PSG": "/fc-paris-saint-germain/startseite/verein/583",
    }

    def __init__(self, use_playwright: bool = False):
        """
        Args:
            use_playwright: Se True, usa Playwright para sites dinâmicos.
                           Se False, usa httpx + BeautifulSoup (mais rápido).
        """
        self.use_playwright = use_playwright
        self.client: Optional[httpx.AsyncClient] = None
        self.browser = None
        self.page: Optional[Page] = None

    async def __aenter__(self):
        if self.use_playwright:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=True)
            self.page = await self.browser.new_page()
        else:
            self.client = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept-Language": "en-US,en;q=0.9",
                },
                follow_redirects=True,
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        if self.client:
            await self.client.aclose()

    async def _fetch_page(self, url: str) -> BeautifulSoup:
        """Busca e parseia página."""
        full_url = f"{self.BASE_URL}{url}" if url.startswith("/") else url

        if self.use_playwright:
            await self.page.goto(full_url)
            await self.page.wait_for_load_state("networkidle")
            content = await self.page.content()
        else:
            response = await self.client.get(full_url)
            response.raise_for_status()
            content = response.text

        return BeautifulSoup(content, "lxml")

    async def get_team_data(self, team_name: str) -> Optional[TeamMarketData]:
        """
        Coleta dados completos de um time.
        """
        url = self.TEAM_URLS.get(team_name)
        if not url:
            logger.warning(f"Team URL not found: {team_name}")
            return None

        logger.info(f"Fetching data for {team_name}")

        try:
            soup = await self._fetch_page(url)

            data = TeamMarketData(team_name=team_name)

            # Valor do elenco
            data.squad_value = self._extract_squad_value(soup)

            # Idade média
            data.avg_age = self._extract_avg_age(soup)

            # Tamanho do elenco
            data.squad_size = self._extract_squad_size(soup)

            # Técnico
            data.coach_name = self._extract_coach(soup)

            # Busca transferências
            transfers_url = url.replace("/startseite/", "/transfers/")
            transfers_soup = await self._fetch_page(transfers_url)
            data.arrivals, data.departures = self._extract_transfers(transfers_soup)

            data.total_spent = sum(t.fee for t in data.arrivals)
            data.total_earned = sum(t.fee for t in data.departures)
            data.net_spend = data.total_spent - data.total_earned

            # Busca jogadores
            kader_url = url.replace("/startseite/", "/kader/")
            kader_soup = await self._fetch_page(kader_url)
            data.players = self._extract_players(kader_soup)

            # Busca lesões
            injuries_url = url.replace("/startseite/", "/sperrenundverletzungen/")
            try:
                injuries_soup = await self._fetch_page(injuries_url)
                data.injured_players = self._extract_injuries(injuries_soup)
            except:
                pass

            logger.info(f"Collected data for {team_name}: Value={data.squad_value}M, Players={data.squad_size}")
            return data

        except Exception as e:
            logger.error(f"Error fetching {team_name}: {e}")
            return None

    def _extract_squad_value(self, soup: BeautifulSoup) -> float:
        """Extrai valor total do elenco."""
        try:
            # Procura pelo valor de mercado total
            value_elem = soup.find("a", {"class": "data-header__market-value-wrapper"})
            if value_elem:
                text = value_elem.get_text(strip=True)
                return self._parse_value(text)

            # Alternativa
            value_elem = soup.find("div", {"class": "data-header__box--small"})
            if value_elem:
                text = value_elem.get_text(strip=True)
                return self._parse_value(text)
        except:
            pass
        return 0.0

    def _extract_avg_age(self, soup: BeautifulSoup) -> float:
        """Extrai idade média do elenco."""
        try:
            for item in soup.find_all("span", {"class": "data-header__label"}):
                if "age" in item.get_text().lower():
                    value = item.find_next("span", {"class": "data-header__content"})
                    if value:
                        return float(value.get_text(strip=True).replace(",", "."))
        except:
            pass
        return 0.0

    def _extract_squad_size(self, soup: BeautifulSoup) -> int:
        """Extrai tamanho do elenco."""
        try:
            for item in soup.find_all("span", {"class": "data-header__label"}):
                if "squad" in item.get_text().lower() or "elenco" in item.get_text().lower():
                    value = item.find_next("span", {"class": "data-header__content"})
                    if value:
                        text = value.get_text(strip=True)
                        match = re.search(r"\d+", text)
                        if match:
                            return int(match.group())
        except:
            pass
        return 0

    def _extract_coach(self, soup: BeautifulSoup) -> str:
        """Extrai nome do técnico."""
        try:
            coach_div = soup.find("div", {"data-viewport": "Mitarbeiter"})
            if coach_div:
                coach_link = coach_div.find("a")
                if coach_link:
                    return coach_link.get_text(strip=True)
        except:
            pass
        return ""

    def _extract_transfers(self, soup: BeautifulSoup) -> tuple[list, list]:
        """Extrai transferências (entradas e saídas)."""
        arrivals = []
        departures = []

        try:
            # Procura tabelas de transferências
            tables = soup.find_all("table", {"class": "items"})

            for table in tables:
                # Verifica se é entrada ou saída pelo header
                header = table.find_previous("h2") or table.find_previous("h3")
                is_arrival = header and ("zugänge" in header.get_text().lower() or
                                        "arrivals" in header.get_text().lower() or
                                        "contratações" in header.get_text().lower())

                rows = table.find_all("tr", {"class": ["odd", "even"]})

                for row in rows:
                    try:
                        cells = row.find_all("td")
                        if len(cells) < 5:
                            continue

                        player_link = cells[0].find("a")
                        player_name = player_link.get_text(strip=True) if player_link else ""

                        # Valor
                        fee_text = cells[-1].get_text(strip=True) if cells else ""
                        fee = self._parse_value(fee_text)

                        transfer = TransferData(
                            player_name=player_name,
                            from_team="" if is_arrival else "",
                            to_team="" if not is_arrival else "",
                            fee=fee,
                            date=date.today(),
                        )

                        if is_arrival:
                            arrivals.append(transfer)
                        else:
                            departures.append(transfer)

                    except Exception as e:
                        continue

        except Exception as e:
            logger.debug(f"Error extracting transfers: {e}")

        return arrivals, departures

    def _extract_players(self, soup: BeautifulSoup) -> list[PlayerData]:
        """Extrai lista de jogadores."""
        players = []

        try:
            table = soup.find("table", {"class": "items"})
            if not table:
                return players

            rows = table.find_all("tr", {"class": ["odd", "even"]})

            for row in rows:
                try:
                    cells = row.find_all("td")
                    if len(cells) < 5:
                        continue

                    # Nome
                    player_link = row.find("a", {"class": "spielprofil_tooltip"})
                    name = player_link.get_text(strip=True) if player_link else ""

                    # Posição
                    pos_elem = row.find("td", {"class": "pos"})
                    position = pos_elem.get_text(strip=True) if pos_elem else ""

                    # Idade
                    age = 0
                    for cell in cells:
                        text = cell.get_text(strip=True)
                        if text.isdigit() and 15 < int(text) < 45:
                            age = int(text)
                            break

                    # Valor de mercado
                    mv_elem = row.find("td", {"class": "rechts hauptlink"})
                    market_value = self._parse_value(mv_elem.get_text(strip=True)) if mv_elem else 0

                    player = PlayerData(
                        name=name,
                        position=position,
                        age=age,
                        nationality="",
                        market_value=market_value,
                    )

                    if name:
                        players.append(player)

                except Exception:
                    continue

        except Exception as e:
            logger.debug(f"Error extracting players: {e}")

        return players

    def _extract_injuries(self, soup: BeautifulSoup) -> list[PlayerData]:
        """Extrai jogadores lesionados."""
        injured = []

        try:
            table = soup.find("table", {"class": "items"})
            if not table:
                return injured

            rows = table.find_all("tr", {"class": ["odd", "even"]})

            for row in rows:
                try:
                    player_link = row.find("a", {"class": "spielprofil_tooltip"})
                    name = player_link.get_text(strip=True) if player_link else ""

                    # Tipo de lesão
                    injury_elem = row.find("td", {"class": "hauptlink"})
                    injury_type = injury_elem.get_text(strip=True) if injury_elem else "Unknown"

                    player = PlayerData(
                        name=name,
                        position="",
                        age=0,
                        nationality="",
                        market_value=0,
                        is_injured=True,
                        injury_type=injury_type,
                    )

                    if name:
                        injured.append(player)

                except Exception:
                    continue

        except Exception as e:
            logger.debug(f"Error extracting injuries: {e}")

        return injured

    def _parse_value(self, text: str) -> float:
        """Converte texto de valor para float (em milhões)."""
        if not text:
            return 0.0

        text = text.lower().replace("€", "").strip()

        try:
            # Ex: "250.00m" ou "250m"
            if "bn" in text or "bi" in text:
                value = float(re.sub(r"[^\d.]", "", text)) * 1000
            elif "m" in text:
                value = float(re.sub(r"[^\d.]", "", text))
            elif "k" in text or "th" in text:
                value = float(re.sub(r"[^\d.]", "", text)) / 1000
            else:
                value = float(re.sub(r"[^\d.]", "", text)) / 1000000
            return round(value, 2)
        except:
            return 0.0

    async def compare_teams(self, team1: str, team2: str) -> dict:
        """Compara dois times."""
        data1 = await self.get_team_data(team1)
        data2 = await self.get_team_data(team2)

        if not data1 or not data2:
            return {}

        comparison = {
            "team1": {
                "name": team1,
                "squad_value": data1.squad_value,
                "avg_age": data1.avg_age,
                "total_spent": data1.total_spent,
                "injured_count": len(data1.injured_players),
            },
            "team2": {
                "name": team2,
                "squad_value": data2.squad_value,
                "avg_age": data2.avg_age,
                "total_spent": data2.total_spent,
                "injured_count": len(data2.injured_players),
            },
            "advantage": {
                "squad_value": team1 if data1.squad_value > data2.squad_value else team2,
                "investment": team1 if data1.total_spent > data2.total_spent else team2,
                "fewer_injuries": team1 if len(data1.injured_players) < len(data2.injured_players) else team2,
            },
            "value_diff": data1.squad_value - data2.squad_value,
            "investment_diff": data1.total_spent - data2.total_spent,
        }

        return comparison


# ============================================================================
# FUNÇÕES DE CONVENIÊNCIA
# ============================================================================

async def fetch_team_market_data(team_name: str) -> Optional[TeamMarketData]:
    """Busca dados de mercado de um time."""
    async with TransfermarktScraper() as scraper:
        return await scraper.get_team_data(team_name)


async def compare_team_values(team1: str, team2: str) -> dict:
    """Compara valores de dois times."""
    async with TransfermarktScraper() as scraper:
        return await scraper.compare_teams(team1, team2)


async def get_injured_players(team_name: str) -> list[PlayerData]:
    """Retorna jogadores lesionados de um time."""
    async with TransfermarktScraper() as scraper:
        data = await scraper.get_team_data(team_name)
        return data.injured_players if data else []
