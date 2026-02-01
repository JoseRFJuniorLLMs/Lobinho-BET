"""
Repository - Operações de Banco de Dados
=========================================
CRUD operations para todas as entidades.
"""

from datetime import datetime, date, timedelta
from typing import Optional, List
from sqlalchemy import select, update, delete, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import selectinload
from loguru import logger

from .models import (
    Base, League, Team, Player, Match, MatchStatus,
    OddsHistory, ValueBet, Bet, BetStatus, BankrollHistory,
    MatchAnalysis, ModelPerformance, SystemConfig, SystemLog, BetSignal
)
from config import get_settings


class Database:
    """Gerenciador de conexão com banco de dados."""

    def __init__(self, database_url: Optional[str] = None):
        settings = get_settings()
        self.database_url = database_url or settings.database_url
        self.engine = create_async_engine(
            self.database_url,
            echo=False,
            pool_size=10,
            max_overflow=20,
        )
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def create_tables(self):
        """Cria todas as tabelas."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")

    async def drop_tables(self):
        """Remove todas as tabelas."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.warning("Database tables dropped")

    def get_session(self) -> AsyncSession:
        """Retorna nova sessão."""
        return self.session_factory()


# ============================================================================
# REPOSITÓRIOS
# ============================================================================

class LeagueRepository:
    """Operações para League."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> League:
        league = League(**kwargs)
        self.session.add(league)
        await self.session.commit()
        await self.session.refresh(league)
        return league

    async def get_by_id(self, league_id: int) -> Optional[League]:
        result = await self.session.execute(
            select(League).where(League.id == league_id)
        )
        return result.scalar_one_or_none()

    async def get_by_external_id(self, external_id: str) -> Optional[League]:
        result = await self.session.execute(
            select(League).where(League.external_id == external_id)
        )
        return result.scalar_one_or_none()

    async def get_active(self) -> List[League]:
        result = await self.session.execute(
            select(League)
            .where(League.is_active == True)
            .order_by(League.priority)
        )
        return result.scalars().all()

    async def get_by_priority(self, priority: int) -> List[League]:
        result = await self.session.execute(
            select(League)
            .where(and_(League.is_active == True, League.priority == priority))
        )
        return result.scalars().all()


class TeamRepository:
    """Operações para Team."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> Team:
        team = Team(**kwargs)
        self.session.add(team)
        await self.session.commit()
        await self.session.refresh(team)
        return team

    async def get_by_id(self, team_id: int) -> Optional[Team]:
        result = await self.session.execute(
            select(Team).where(Team.id == team_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Team]:
        result = await self.session.execute(
            select(Team).where(Team.name.ilike(f"%{name}%"))
        )
        return result.scalar_one_or_none()

    async def get_by_league(self, league_id: int) -> List[Team]:
        result = await self.session.execute(
            select(Team)
            .where(Team.league_id == league_id)
            .order_by(Team.name)
        )
        return result.scalars().all()

    async def update_elo(self, team_id: int, new_elo: float):
        await self.session.execute(
            update(Team)
            .where(Team.id == team_id)
            .values(elo_rating=new_elo, updated_at=datetime.now())
        )
        await self.session.commit()

    async def update_strengths(self, team_id: int, attack: float, defense: float):
        await self.session.execute(
            update(Team)
            .where(Team.id == team_id)
            .values(
                attack_strength=attack,
                defense_strength=defense,
                updated_at=datetime.now()
            )
        )
        await self.session.commit()


class MatchRepository:
    """Operações para Match."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> Match:
        match = Match(**kwargs)
        self.session.add(match)
        await self.session.commit()
        await self.session.refresh(match)
        return match

    async def get_by_id(self, match_id: int) -> Optional[Match]:
        result = await self.session.execute(
            select(Match)
            .options(
                selectinload(Match.home_team),
                selectinload(Match.away_team),
                selectinload(Match.league),
            )
            .where(Match.id == match_id)
        )
        return result.scalar_one_or_none()

    async def get_by_external_id(self, external_id: str) -> Optional[Match]:
        result = await self.session.execute(
            select(Match).where(Match.external_id == external_id)
        )
        return result.scalar_one_or_none()

    async def get_today(self) -> List[Match]:
        today = date.today()
        tomorrow = today + timedelta(days=1)
        result = await self.session.execute(
            select(Match)
            .options(
                selectinload(Match.home_team),
                selectinload(Match.away_team),
            )
            .where(and_(
                Match.kickoff >= datetime.combine(today, datetime.min.time()),
                Match.kickoff < datetime.combine(tomorrow, datetime.min.time()),
            ))
            .order_by(Match.kickoff)
        )
        return result.scalars().all()

    async def get_live(self) -> List[Match]:
        result = await self.session.execute(
            select(Match)
            .options(
                selectinload(Match.home_team),
                selectinload(Match.away_team),
            )
            .where(Match.status == MatchStatus.LIVE)
            .order_by(Match.kickoff)
        )
        return result.scalars().all()

    async def get_upcoming(self, hours: int = 24) -> List[Match]:
        now = datetime.now()
        until = now + timedelta(hours=hours)
        result = await self.session.execute(
            select(Match)
            .options(
                selectinload(Match.home_team),
                selectinload(Match.away_team),
            )
            .where(and_(
                Match.kickoff >= now,
                Match.kickoff <= until,
                Match.status == MatchStatus.SCHEDULED,
            ))
            .order_by(Match.kickoff)
        )
        return result.scalars().all()

    async def get_team_matches(
        self,
        team_id: int,
        limit: int = 10,
        finished_only: bool = True,
    ) -> List[Match]:
        query = (
            select(Match)
            .where(or_(
                Match.home_team_id == team_id,
                Match.away_team_id == team_id,
            ))
        )
        if finished_only:
            query = query.where(Match.status == MatchStatus.FINISHED)

        query = query.order_by(desc(Match.kickoff)).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_h2h(
        self,
        team1_id: int,
        team2_id: int,
        limit: int = 10,
    ) -> List[Match]:
        result = await self.session.execute(
            select(Match)
            .where(and_(
                Match.status == MatchStatus.FINISHED,
                or_(
                    and_(Match.home_team_id == team1_id, Match.away_team_id == team2_id),
                    and_(Match.home_team_id == team2_id, Match.away_team_id == team1_id),
                )
            ))
            .order_by(desc(Match.kickoff))
            .limit(limit)
        )
        return result.scalars().all()

    async def update_result(
        self,
        match_id: int,
        home_goals: int,
        away_goals: int,
        status: MatchStatus = MatchStatus.FINISHED,
    ):
        await self.session.execute(
            update(Match)
            .where(Match.id == match_id)
            .values(
                home_goals=home_goals,
                away_goals=away_goals,
                status=status,
                updated_at=datetime.now(),
            )
        )
        await self.session.commit()

    async def update_predictions(
        self,
        match_id: int,
        home_win: float,
        draw: float,
        away_win: float,
        confidence: float,
    ):
        await self.session.execute(
            update(Match)
            .where(Match.id == match_id)
            .values(
                pred_home_win=home_win,
                pred_draw=draw,
                pred_away_win=away_win,
                prediction_confidence=confidence,
                updated_at=datetime.now(),
            )
        )
        await self.session.commit()


class ValueBetRepository:
    """Operações para ValueBet."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> ValueBet:
        vb = ValueBet(**kwargs)
        self.session.add(vb)
        await self.session.commit()
        await self.session.refresh(vb)
        return vb

    async def get_today(self) -> List[ValueBet]:
        today = date.today()
        result = await self.session.execute(
            select(ValueBet)
            .where(ValueBet.detected_at >= datetime.combine(today, datetime.min.time()))
            .order_by(desc(ValueBet.edge))
        )
        return result.scalars().all()

    async def get_pending(self) -> List[ValueBet]:
        result = await self.session.execute(
            select(ValueBet)
            .where(ValueBet.outcome == None)
            .order_by(desc(ValueBet.detected_at))
        )
        return result.scalars().all()

    async def get_by_signal(self, signal: BetSignal) -> List[ValueBet]:
        result = await self.session.execute(
            select(ValueBet)
            .where(and_(
                ValueBet.signal == signal,
                ValueBet.outcome == None,
            ))
            .order_by(desc(ValueBet.edge))
        )
        return result.scalars().all()

    async def mark_notified(self, vb_id: int):
        await self.session.execute(
            update(ValueBet)
            .where(ValueBet.id == vb_id)
            .values(notified=True, notified_at=datetime.now())
        )
        await self.session.commit()

    async def resolve(self, vb_id: int, outcome: str):
        await self.session.execute(
            update(ValueBet)
            .where(ValueBet.id == vb_id)
            .values(outcome=outcome, resolved_at=datetime.now())
        )
        await self.session.commit()

    async def get_stats(self, days: int = 30) -> dict:
        since = datetime.now() - timedelta(days=days)
        result = await self.session.execute(
            select(
                func.count(ValueBet.id).label("total"),
                func.sum(func.case((ValueBet.outcome == "won", 1), else_=0)).label("wins"),
                func.avg(ValueBet.edge).label("avg_edge"),
            )
            .where(and_(
                ValueBet.detected_at >= since,
                ValueBet.outcome != None,
            ))
        )
        row = result.one()
        return {
            "total": row.total or 0,
            "wins": row.wins or 0,
            "hit_rate": (row.wins / row.total * 100) if row.total else 0,
            "avg_edge": round(row.avg_edge or 0, 2),
        }


class BetRepository:
    """Operações para Bet."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> Bet:
        bet = Bet(**kwargs)
        self.session.add(bet)
        await self.session.commit()
        await self.session.refresh(bet)
        return bet

    async def get_pending(self) -> List[Bet]:
        result = await self.session.execute(
            select(Bet)
            .where(Bet.status == BetStatus.PENDING)
            .order_by(desc(Bet.placed_at))
        )
        return result.scalars().all()

    async def settle(self, bet_id: int, status: BetStatus, profit: float):
        await self.session.execute(
            update(Bet)
            .where(Bet.id == bet_id)
            .values(
                status=status,
                profit=profit,
                settled_at=datetime.now(),
            )
        )
        await self.session.commit()

    async def get_stats(self, days: int = 30) -> dict:
        since = datetime.now() - timedelta(days=days)
        result = await self.session.execute(
            select(
                func.count(Bet.id).label("total"),
                func.sum(func.case((Bet.status == BetStatus.WON, 1), else_=0)).label("wins"),
                func.sum(Bet.stake).label("total_staked"),
                func.sum(Bet.profit).label("total_profit"),
            )
            .where(and_(
                Bet.placed_at >= since,
                Bet.status != BetStatus.PENDING,
            ))
        )
        row = result.one()
        total_staked = row.total_staked or 0
        total_profit = row.total_profit or 0

        return {
            "total_bets": row.total or 0,
            "wins": row.wins or 0,
            "losses": (row.total or 0) - (row.wins or 0),
            "hit_rate": (row.wins / row.total * 100) if row.total else 0,
            "total_staked": round(total_staked, 2),
            "total_profit": round(total_profit, 2),
            "roi": round(total_profit / total_staked * 100, 2) if total_staked else 0,
        }


class BankrollRepository:
    """Operações para BankrollHistory."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def record(self, balance: float, change: float, reason: str, bet_id: int = None):
        # Busca stats atuais
        result = await self.session.execute(
            select(BankrollHistory)
            .order_by(desc(BankrollHistory.timestamp))
            .limit(1)
        )
        last = result.scalar_one_or_none()

        entry = BankrollHistory(
            balance=balance,
            change=change,
            reason=reason,
            bet_id=bet_id,
            total_bets=(last.total_bets or 0) + (1 if bet_id else 0),
            total_wins=(last.total_wins or 0) + (1 if change > 0 and bet_id else 0),
            total_profit=(last.total_profit or 0) + change,
        )

        # Calcula ROI
        if entry.total_bets > 0:
            # Simplificado - em produção calcular corretamente
            entry.roi = entry.total_profit / (entry.total_bets * 10) * 100

        self.session.add(entry)
        await self.session.commit()
        return entry

    async def get_current(self) -> Optional[BankrollHistory]:
        result = await self.session.execute(
            select(BankrollHistory)
            .order_by(desc(BankrollHistory.timestamp))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_history(self, days: int = 30) -> List[BankrollHistory]:
        since = datetime.now() - timedelta(days=days)
        result = await self.session.execute(
            select(BankrollHistory)
            .where(BankrollHistory.timestamp >= since)
            .order_by(BankrollHistory.timestamp)
        )
        return result.scalars().all()


class ModelPerformanceRepository:
    """Operações para ModelPerformance."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def record(self, model_name: str, metrics: dict):
        today = date.today()

        # Verifica se já existe
        result = await self.session.execute(
            select(ModelPerformance)
            .where(and_(
                ModelPerformance.model_name == model_name,
                ModelPerformance.date == today,
            ))
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Atualiza
            existing.total_predictions = metrics.get("total", 0)
            existing.correct_predictions = metrics.get("correct", 0)
            existing.brier_score = metrics.get("brier_score")
            existing.log_loss = metrics.get("log_loss")
            existing.calibration_error = metrics.get("calibration_error")
            existing.roi = metrics.get("roi")
        else:
            # Cria novo
            perf = ModelPerformance(
                model_name=model_name,
                date=today,
                total_predictions=metrics.get("total", 0),
                correct_predictions=metrics.get("correct", 0),
                brier_score=metrics.get("brier_score"),
                log_loss=metrics.get("log_loss"),
                calibration_error=metrics.get("calibration_error"),
                roi=metrics.get("roi"),
            )
            self.session.add(perf)

        await self.session.commit()

    async def get_model_stats(self, model_name: str, days: int = 30) -> dict:
        since = date.today() - timedelta(days=days)
        result = await self.session.execute(
            select(
                func.sum(ModelPerformance.total_predictions).label("total"),
                func.sum(ModelPerformance.correct_predictions).label("correct"),
                func.avg(ModelPerformance.brier_score).label("avg_brier"),
                func.avg(ModelPerformance.roi).label("avg_roi"),
            )
            .where(and_(
                ModelPerformance.model_name == model_name,
                ModelPerformance.date >= since,
            ))
        )
        row = result.one()
        return {
            "model": model_name,
            "total_predictions": row.total or 0,
            "correct_predictions": row.correct or 0,
            "accuracy": (row.correct / row.total * 100) if row.total else 0,
            "avg_brier_score": round(row.avg_brier or 0, 4),
            "avg_roi": round(row.avg_roi or 0, 2),
        }

    async def get_best_model(self, days: int = 30) -> Optional[str]:
        since = date.today() - timedelta(days=days)
        result = await self.session.execute(
            select(
                ModelPerformance.model_name,
                func.avg(ModelPerformance.brier_score).label("avg_brier"),
            )
            .where(ModelPerformance.date >= since)
            .group_by(ModelPerformance.model_name)
            .order_by(func.avg(ModelPerformance.brier_score))
            .limit(1)
        )
        row = result.first()
        return row[0] if row else None


# ============================================================================
# UNIT OF WORK
# ============================================================================

class UnitOfWork:
    """
    Unit of Work pattern para gerenciar transações.

    Uso:
        async with UnitOfWork() as uow:
            team = await uow.teams.create(name="Flamengo")
            await uow.commit()
    """

    def __init__(self, db: Database = None):
        self.db = db or Database()

    async def __aenter__(self):
        self.session = self.db.get_session()
        self.leagues = LeagueRepository(self.session)
        self.teams = TeamRepository(self.session)
        self.matches = MatchRepository(self.session)
        self.value_bets = ValueBetRepository(self.session)
        self.bets = BetRepository(self.session)
        self.bankroll = BankrollRepository(self.session)
        self.model_performance = ModelPerformanceRepository(self.session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.session.rollback()
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()
