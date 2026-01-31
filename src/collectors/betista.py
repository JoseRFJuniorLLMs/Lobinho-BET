"""
Betista.com Collector
=====================
Coleta dados do Betista.com para análise.

Fluxo:
1. Acessa betista.com
2. Lista eventos disponíveis
3. Abre todos os mercados de cada evento
4. Coleta dados históricos e estatísticas
5. Rankeia eventos mais rentáveis
6. Direciona para monitoramento ao vivo
"""

import asyncio
from typing import Optional
from datetime import datetime, date
from dataclasses import dataclass, field
from playwright.async_api import async_playwright, Page, Browser
from loguru import logger


@dataclass
class BetMarket:
    """Mercado de aposta disponível."""
    name: str  # "Resultado Final", "Over/Under", etc
    selections: list[dict]  # [{name: "Casa", odds: 1.85}, ...]
    is_main: bool = False


@dataclass
class BetEvent:
    """Evento de aposta do Betista."""
    event_id: str
    home_team: str
    away_team: str
    league: str
    kickoff: datetime
    status: str = "scheduled"  # scheduled, live, finished

    # Mercados disponíveis
    markets: list[BetMarket] = field(default_factory=list)

    # Estatísticas históricas
    stats: dict = field(default_factory=dict)
    h2h: list[dict] = field(default_factory=list)
    home_form: str = ""
    away_form: str = ""

    # Análise
    predicted_value: float = 0  # Value esperado
    best_market: Optional[str] = None
    best_selection: Optional[str] = None
    best_odds: float = 0
    confidence: float = 0

    # Ranking
    rank_score: float = 0

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "match": f"{self.home_team} vs {self.away_team}",
            "league": self.league,
            "kickoff": self.kickoff.isoformat() if self.kickoff else None,
            "status": self.status,
            "markets_count": len(self.markets),
            "best_market": self.best_market,
            "best_selection": self.best_selection,
            "best_odds": self.best_odds,
            "confidence": self.confidence,
            "rank_score": self.rank_score,
            "home_form": self.home_form,
            "away_form": self.away_form,
        }


class BetistaCollector:
    """
    Coleta dados do Betista.com usando Playwright.

    Fluxo completo:
    1. Abre página inicial
    2. Lista todos os eventos de futebol
    3. Para cada evento, abre detalhes e mercados
    4. Coleta estatísticas e histórico
    5. Analisa e rankeia por rentabilidade
    """

    BASE_URL = "https://betista.com"

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    async def __aenter__(self):
        await self.start_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_browser()

    async def start_browser(self):
        """Inicia navegador."""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()
        logger.info("Browser started")

    async def close_browser(self):
        """Fecha navegador."""
        if self.browser:
            await self.browser.close()
            logger.info("Browser closed")

    # =========================================================================
    # PASSO 1: Listar eventos disponíveis
    # =========================================================================

    async def get_available_events(self, sport: str = "futebol") -> list[BetEvent]:
        """
        Lista todos os eventos disponíveis.

        Returns:
            Lista de BetEvent com dados básicos
        """
        logger.info(f"Fetching available events for {sport}")

        # Acessa página de futebol
        await self.page.goto(f"{self.BASE_URL}/{sport}")
        await self.page.wait_for_load_state("networkidle")

        # Aguarda lista de eventos carregar
        await self.page.wait_for_selector(".event-list, .matches-container, [data-event]", timeout=10000)

        events = []

        # Seleciona todos os eventos
        # (seletores podem variar - ajustar conforme estrutura real do site)
        event_elements = await self.page.query_selector_all(
            ".event-item, .match-row, [data-event-id]"
        )

        for element in event_elements:
            try:
                event = await self._parse_event_element(element)
                if event:
                    events.append(event)
            except Exception as e:
                logger.debug(f"Error parsing event: {e}")

        logger.info(f"Found {len(events)} events")
        return events

    async def _parse_event_element(self, element) -> Optional[BetEvent]:
        """Extrai dados de um elemento de evento."""
        try:
            # Extrai ID do evento
            event_id = await element.get_attribute("data-event-id") or ""
            if not event_id:
                event_id = await element.get_attribute("id") or str(hash(str(element)))

            # Extrai times
            teams = await element.query_selector_all(".team-name, .participant")
            home_team = await teams[0].inner_text() if len(teams) > 0 else ""
            away_team = await teams[1].inner_text() if len(teams) > 1 else ""

            # Extrai liga
            league_el = await element.query_selector(".league-name, .competition")
            league = await league_el.inner_text() if league_el else ""

            # Extrai horário
            time_el = await element.query_selector(".event-time, .match-time, .kickoff")
            time_str = await time_el.inner_text() if time_el else ""

            # Extrai odds principais
            odds_els = await element.query_selector_all(".odd-value, .odds-button, .price")
            odds = []
            for odd_el in odds_els[:3]:
                try:
                    odd_text = await odd_el.inner_text()
                    odds.append(float(odd_text.replace(",", ".")))
                except:
                    odds.append(0)

            # Cria evento
            event = BetEvent(
                event_id=event_id.strip(),
                home_team=home_team.strip(),
                away_team=away_team.strip(),
                league=league.strip(),
                kickoff=datetime.now(),  # Parsear do time_str
                status="scheduled",
            )

            # Adiciona mercado principal se tiver odds
            if len(odds) >= 3 and all(o > 0 for o in odds):
                event.markets.append(BetMarket(
                    name="Resultado Final",
                    selections=[
                        {"name": "Casa", "odds": odds[0]},
                        {"name": "Empate", "odds": odds[1]},
                        {"name": "Fora", "odds": odds[2]},
                    ],
                    is_main=True,
                ))

            return event

        except Exception as e:
            logger.debug(f"Error parsing event element: {e}")
            return None

    # =========================================================================
    # PASSO 2: Abrir todos os mercados de um evento
    # =========================================================================

    async def get_event_markets(self, event: BetEvent) -> list[BetMarket]:
        """
        Abre página do evento e coleta todos os mercados.
        """
        logger.info(f"Fetching markets for {event.home_team} vs {event.away_team}")

        # Navega para página do evento
        event_url = f"{self.BASE_URL}/evento/{event.event_id}"
        await self.page.goto(event_url)
        await self.page.wait_for_load_state("networkidle")

        markets = []

        # Expande todos os mercados (clica em "Mostrar mais" se existir)
        expand_buttons = await self.page.query_selector_all(
            ".expand-markets, .show-more, .toggle-markets"
        )
        for btn in expand_buttons:
            try:
                await btn.click()
                await asyncio.sleep(0.3)
            except:
                pass

        # Coleta todos os mercados
        market_sections = await self.page.query_selector_all(
            ".market-section, .bet-type, [data-market]"
        )

        for section in market_sections:
            try:
                market = await self._parse_market_section(section)
                if market:
                    markets.append(market)
            except Exception as e:
                logger.debug(f"Error parsing market: {e}")

        event.markets = markets
        logger.info(f"Found {len(markets)} markets")
        return markets

    async def _parse_market_section(self, section) -> Optional[BetMarket]:
        """Extrai dados de uma seção de mercado."""
        try:
            # Nome do mercado
            name_el = await section.query_selector(".market-name, .bet-type-name, h3, h4")
            name = await name_el.inner_text() if name_el else "Unknown"

            # Seleções e odds
            selection_els = await section.query_selector_all(
                ".selection, .odd-button, .bet-option"
            )

            selections = []
            for sel_el in selection_els:
                sel_name_el = await sel_el.query_selector(".selection-name, .option-name")
                sel_odds_el = await sel_el.query_selector(".odds, .price, .odd-value")

                sel_name = await sel_name_el.inner_text() if sel_name_el else ""
                sel_odds_text = await sel_odds_el.inner_text() if sel_odds_el else "0"

                try:
                    sel_odds = float(sel_odds_text.replace(",", "."))
                except:
                    sel_odds = 0

                if sel_name and sel_odds > 0:
                    selections.append({
                        "name": sel_name.strip(),
                        "odds": sel_odds,
                    })

            if selections:
                return BetMarket(
                    name=name.strip(),
                    selections=selections,
                    is_main="resultado" in name.lower() or "1x2" in name.lower(),
                )

            return None

        except Exception as e:
            logger.debug(f"Error parsing market section: {e}")
            return None

    # =========================================================================
    # PASSO 3: Coletar estatísticas históricas
    # =========================================================================

    async def get_event_stats(self, event: BetEvent) -> dict:
        """
        Coleta estatísticas e histórico do evento.
        """
        logger.info(f"Fetching stats for {event.home_team} vs {event.away_team}")

        # Procura aba de estatísticas
        stats_tab = await self.page.query_selector(
            "[data-tab='stats'], .stats-tab, .statistics-tab"
        )
        if stats_tab:
            await stats_tab.click()
            await asyncio.sleep(0.5)

        stats = {}

        # Coleta forma dos times
        form_els = await self.page.query_selector_all(".team-form, .form-indicator")
        if len(form_els) >= 2:
            event.home_form = await self._extract_form(form_els[0])
            event.away_form = await self._extract_form(form_els[1])

        # Coleta H2H
        h2h_section = await self.page.query_selector(".h2h-section, .head-to-head")
        if h2h_section:
            event.h2h = await self._extract_h2h(h2h_section)

        # Coleta estatísticas gerais
        stats_els = await self.page.query_selector_all(".stat-row, .statistic-item")
        for stat_el in stats_els:
            try:
                label_el = await stat_el.query_selector(".stat-label, .stat-name")
                value_el = await stat_el.query_selector(".stat-value, .stat-values")

                label = await label_el.inner_text() if label_el else ""
                value = await value_el.inner_text() if value_el else ""

                if label:
                    stats[label.strip()] = value.strip()
            except:
                pass

        event.stats = stats
        return stats

    async def _extract_form(self, form_el) -> str:
        """Extrai forma do time (ex: WDWLW)."""
        try:
            form_items = await form_el.query_selector_all(".form-item, .result-icon")
            form = ""
            for item in form_items[-5:]:  # Últimos 5 jogos
                text = await item.inner_text()
                cls = await item.get_attribute("class") or ""

                if "win" in cls.lower() or text.upper() == "V":
                    form += "W"
                elif "draw" in cls.lower() or text.upper() == "E":
                    form += "D"
                elif "loss" in cls.lower() or text.upper() == "D":
                    form += "L"

            return form
        except:
            return ""

    async def _extract_h2h(self, h2h_section) -> list[dict]:
        """Extrai histórico de confrontos."""
        h2h = []
        try:
            match_els = await h2h_section.query_selector_all(".h2h-match, .past-match")
            for match_el in match_els[:5]:
                score_el = await match_el.query_selector(".score, .result")
                date_el = await match_el.query_selector(".date, .match-date")

                score = await score_el.inner_text() if score_el else ""
                match_date = await date_el.inner_text() if date_el else ""

                h2h.append({
                    "score": score.strip(),
                    "date": match_date.strip(),
                })
        except:
            pass

        return h2h

    # =========================================================================
    # PASSO 4: Analisar e rankear eventos
    # =========================================================================

    async def analyze_events(self, events: list[BetEvent]) -> list[BetEvent]:
        """
        Analisa todos os eventos e calcula ranking de rentabilidade.
        """
        from src.models.markov_predictor import MarkovPredictor
        from src.models.advanced_predictors import EnsemblePredictor
        from src.models.value_detector import ValueDetector

        markov = MarkovPredictor()
        ensemble = EnsemblePredictor()
        value_detector = ValueDetector(min_edge=3.0)

        analyzed = []

        for event in events:
            try:
                # Previsão Markov
                markov_pred = markov.predict_match(
                    list(event.home_form) if event.home_form else ["D"],
                    list(event.away_form) if event.away_form else ["D"],
                )

                # Previsão Ensemble (simplificada)
                predictions = {
                    "home_win": markov_pred.home_win,
                    "draw": markov_pred.draw,
                    "away_win": markov_pred.away_win,
                }

                # Busca odds do mercado principal
                odds = {}
                main_market = next((m for m in event.markets if m.is_main), None)
                if main_market:
                    for sel in main_market.selections:
                        if "casa" in sel["name"].lower():
                            odds["home"] = sel["odds"]
                        elif "empate" in sel["name"].lower():
                            odds["draw"] = sel["odds"]
                        else:
                            odds["away"] = sel["odds"]

                # Detecta value bets
                if odds:
                    value_bets = value_detector.detect_value(
                        match_id=event.event_id,
                        home_team=event.home_team,
                        away_team=event.away_team,
                        predictions=predictions,
                        odds=odds,
                    )

                    if value_bets:
                        best = max(value_bets, key=lambda x: x.edge)
                        event.best_market = best.market
                        event.best_selection = best.selection
                        event.best_odds = best.odds
                        event.predicted_value = best.edge
                        event.confidence = markov_pred.confidence

                # Calcula rank score
                event.rank_score = self._calculate_rank_score(event, markov_pred)
                analyzed.append(event)

            except Exception as e:
                logger.error(f"Error analyzing event {event.event_id}: {e}")

        # Ordena por rank_score
        analyzed.sort(key=lambda x: x.rank_score, reverse=True)
        return analyzed

    def _calculate_rank_score(self, event: BetEvent, markov_pred) -> float:
        """Calcula score de ranking."""
        score = 0

        # Valor (edge)
        score += event.predicted_value * 5

        # Confiança do Markov
        score += markov_pred.confidence * 0.3

        # Dados disponíveis
        if event.home_form and event.away_form:
            score += 10
        if event.h2h:
            score += 5
        if len(event.markets) > 5:
            score += 5

        # Penaliza se não tem value
        if event.predicted_value <= 0:
            score -= 20

        return max(0, score)

    # =========================================================================
    # PASSO 5: Selecionar melhores eventos para live
    # =========================================================================

    async def get_top_events_for_live(
        self,
        min_rank: float = 20,
        max_events: int = 10,
    ) -> list[BetEvent]:
        """
        Retorna os melhores eventos para acompanhar ao vivo.

        Critérios:
        1. Rank score > min_rank
        2. Tem value bet detectado
        3. Dados históricos suficientes
        """
        # Coleta eventos
        events = await self.get_available_events()

        # Coleta detalhes de cada evento
        for event in events[:30]:  # Limita para não demorar muito
            await self.get_event_markets(event)
            await self.get_event_stats(event)
            await asyncio.sleep(0.5)  # Rate limiting

        # Analisa e rankeia
        analyzed = await self.analyze_events(events)

        # Filtra melhores
        top_events = [
            e for e in analyzed
            if e.rank_score >= min_rank and e.predicted_value > 0
        ]

        return top_events[:max_events]


# ============================================================================
# FLUXO COMPLETO
# ============================================================================

async def run_betista_analysis() -> list[dict]:
    """
    Executa fluxo completo de análise do Betista.

    1. Abre betista.com
    2. Lista eventos
    3. Coleta mercados e estatísticas
    4. Analisa com Markov + Ensemble
    5. Retorna ranking dos melhores

    Returns:
        Lista de eventos rankeados para live
    """
    logger.info("Starting Betista analysis flow...")

    async with BetistaCollector(headless=True) as collector:
        # Passo 1-3: Coleta dados
        top_events = await collector.get_top_events_for_live(
            min_rank=15,
            max_events=10,
        )

        # Formata resultado
        result = []
        for i, event in enumerate(top_events, 1):
            result.append({
                "rank": i,
                **event.to_dict(),
                "action": "ACOMPANHAR" if event.predicted_value > 5 else "ANALISAR",
                "markets": [
                    {
                        "name": m.name,
                        "selections": m.selections,
                    }
                    for m in event.markets
                ],
            })

        logger.info(f"Analysis complete. Found {len(result)} events to track")
        return result


if __name__ == "__main__":
    asyncio.run(run_betista_analysis())
