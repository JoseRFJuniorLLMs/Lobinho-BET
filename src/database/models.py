"""
SQLAlchemy Models - Persistência de Dados
==========================================
Modelos para armazenar todo histórico do sistema.
"""

from datetime import datetime, date
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Date,
    ForeignKey, Text, JSON, Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()


# ============================================================================
# ENUMS
# ============================================================================

class MatchStatus(enum.Enum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    FINISHED = "finished"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"


class BetStatus(enum.Enum):
    PENDING = "pending"
    WON = "won"
    LOST = "lost"
    VOID = "void"
    CASHOUT = "cashout"


class BetSignal(enum.Enum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    AVOID = "avoid"


# ============================================================================
# TIMES E LIGAS
# ============================================================================

class League(Base):
    """Campeonato/Liga."""
    __tablename__ = "leagues"

    id = Column(Integer, primary_key=True)
    external_id = Column(String(50), unique=True, index=True)
    name = Column(String(100), nullable=False)
    country = Column(String(50))
    season = Column(String(20))
    priority = Column(Integer, default=2)  # 1=HIGH, 2=MEDIUM, 3=LOW
    is_active = Column(Boolean, default=True)

    # IDs externos
    footystats_id = Column(Integer)
    odds_api_key = Column(String(100))
    fbref_path = Column(String(200))

    # Configurações
    min_edge = Column(Float, default=5.0)
    max_stake = Column(Float, default=3.0)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relacionamentos
    teams = relationship("Team", back_populates="league")
    matches = relationship("Match", back_populates="league")


class Team(Base):
    """Time de futebol."""
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    external_id = Column(String(50), unique=True, index=True)
    name = Column(String(100), nullable=False)
    short_name = Column(String(20))
    country = Column(String(50))
    league_id = Column(Integer, ForeignKey("leagues.id"))

    # Valor e estatísticas
    squad_value = Column(Float, default=0)  # Em milhões EUR
    avg_age = Column(Float)
    total_spent = Column(Float, default=0)  # Transferências
    total_earned = Column(Float, default=0)

    # Ratings
    elo_rating = Column(Float, default=1500)
    attack_strength = Column(Float, default=1.0)
    defense_strength = Column(Float, default=1.0)

    # IDs externos
    footystats_id = Column(Integer)
    transfermarkt_id = Column(String(50))
    fbref_id = Column(String(50))

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relacionamentos
    league = relationship("League", back_populates="teams")
    home_matches = relationship("Match", foreign_keys="Match.home_team_id", back_populates="home_team")
    away_matches = relationship("Match", foreign_keys="Match.away_team_id", back_populates="away_team")
    players = relationship("Player", back_populates="team")

    __table_args__ = (
        Index("ix_teams_name", "name"),
    )


class Player(Base):
    """Jogador."""
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    external_id = Column(String(50), unique=True, index=True)
    name = Column(String(100), nullable=False)
    position = Column(String(30))
    age = Column(Integer)
    nationality = Column(String(50))
    team_id = Column(Integer, ForeignKey("teams.id"))

    market_value = Column(Float, default=0)  # Em milhões EUR
    contract_until = Column(Date)

    # Status
    is_injured = Column(Boolean, default=False)
    is_suspended = Column(Boolean, default=False)
    injury_type = Column(String(100))
    return_date = Column(Date)

    # Stats da temporada
    goals = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    minutes_played = Column(Integer, default=0)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relacionamentos
    team = relationship("Team", back_populates="players")


# ============================================================================
# PARTIDAS
# ============================================================================

class Match(Base):
    """Partida de futebol."""
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True)
    external_id = Column(String(50), unique=True, index=True)

    home_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    away_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    league_id = Column(Integer, ForeignKey("leagues.id"))

    kickoff = Column(DateTime, nullable=False, index=True)
    status = Column(SQLEnum(MatchStatus), default=MatchStatus.SCHEDULED)

    # Resultado
    home_goals = Column(Integer)
    away_goals = Column(Integer)
    home_goals_ht = Column(Integer)  # Primeiro tempo
    away_goals_ht = Column(Integer)

    # Estatísticas do jogo
    home_xg = Column(Float)
    away_xg = Column(Float)
    home_shots = Column(Integer)
    away_shots = Column(Integer)
    home_shots_on_target = Column(Integer)
    away_shots_on_target = Column(Integer)
    home_possession = Column(Float)
    away_possession = Column(Float)
    home_corners = Column(Integer)
    away_corners = Column(Integer)

    # Previsões do modelo
    pred_home_win = Column(Float)
    pred_draw = Column(Float)
    pred_away_win = Column(Float)
    pred_over_25 = Column(Float)
    pred_btts = Column(Float)
    prediction_confidence = Column(Float)

    # Metadados
    venue = Column(String(100))
    referee = Column(String(100))
    attendance = Column(Integer)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relacionamentos
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_matches")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_matches")
    league = relationship("League", back_populates="matches")
    odds_history = relationship("OddsHistory", back_populates="match")
    value_bets = relationship("ValueBet", back_populates="match")
    bets = relationship("Bet", back_populates="match")

    __table_args__ = (
        Index("ix_matches_kickoff", "kickoff"),
        Index("ix_matches_status", "status"),
    )


# ============================================================================
# ODDS E VALUE BETS
# ============================================================================

class OddsHistory(Base):
    """Histórico de odds de uma partida."""
    __tablename__ = "odds_history"

    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    bookmaker = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=func.now(), index=True)

    # Odds 1X2
    home_odds = Column(Float)
    draw_odds = Column(Float)
    away_odds = Column(Float)

    # Over/Under
    over_25_odds = Column(Float)
    under_25_odds = Column(Float)
    over_15_odds = Column(Float)
    under_15_odds = Column(Float)

    # BTTS
    btts_yes_odds = Column(Float)
    btts_no_odds = Column(Float)

    # Handicap
    handicap_line = Column(Float)
    handicap_home_odds = Column(Float)
    handicap_away_odds = Column(Float)

    # Relacionamentos
    match = relationship("Match", back_populates="odds_history")

    __table_args__ = (
        Index("ix_odds_match_time", "match_id", "timestamp"),
    )


class ValueBet(Base):
    """Value bet detectado."""
    __tablename__ = "value_bets"

    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)

    market = Column(String(50), nullable=False)  # home, draw, away, over_25, etc
    selection = Column(String(100), nullable=False)
    bookmaker = Column(String(50))

    odds = Column(Float, nullable=False)
    fair_odds = Column(Float)
    probability = Column(Float)
    edge = Column(Float)
    confidence = Column(Float)
    kelly_stake = Column(Float)
    ev = Column(Float)

    signal = Column(SQLEnum(BetSignal))

    detected_at = Column(DateTime, default=func.now())
    notified = Column(Boolean, default=False)
    notified_at = Column(DateTime)

    # Resultado
    outcome = Column(String(20))  # won, lost, void
    resolved_at = Column(DateTime)

    # Relacionamentos
    match = relationship("Match", back_populates="value_bets")

    __table_args__ = (
        Index("ix_valuebets_detected", "detected_at"),
        Index("ix_valuebets_signal", "signal"),
    )


# ============================================================================
# APOSTAS E BANCA
# ============================================================================

class Bet(Base):
    """Aposta realizada."""
    __tablename__ = "bets"

    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    value_bet_id = Column(Integer, ForeignKey("value_bets.id"))

    bookmaker = Column(String(50), nullable=False)
    market = Column(String(50), nullable=False)
    selection = Column(String(100), nullable=False)

    odds = Column(Float, nullable=False)
    stake = Column(Float, nullable=False)
    potential_return = Column(Float)

    status = Column(SQLEnum(BetStatus), default=BetStatus.PENDING)
    profit = Column(Float, default=0)

    placed_at = Column(DateTime, default=func.now())
    settled_at = Column(DateTime)

    # Metadados
    notes = Column(Text)
    screenshot_path = Column(String(500))

    # Relacionamentos
    match = relationship("Match", back_populates="bets")

    __table_args__ = (
        Index("ix_bets_status", "status"),
        Index("ix_bets_placed", "placed_at"),
    )


class BankrollHistory(Base):
    """Histórico de banca."""
    __tablename__ = "bankroll_history"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=func.now(), index=True)

    balance = Column(Float, nullable=False)
    change = Column(Float, default=0)
    reason = Column(String(100))  # bet_won, bet_lost, deposit, withdrawal

    bet_id = Column(Integer, ForeignKey("bets.id"))

    # Estatísticas acumuladas
    total_bets = Column(Integer, default=0)
    total_wins = Column(Integer, default=0)
    total_profit = Column(Float, default=0)
    roi = Column(Float, default=0)


# ============================================================================
# ANÁLISES E PREVISÕES
# ============================================================================

class MatchAnalysis(Base):
    """Análise completa de uma partida."""
    __tablename__ = "match_analyses"

    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"), unique=True)

    # Fase 1: Pré-análise
    pre_analysis = Column(JSON)  # investimentos, elenco, lesões

    # Fase 2: Estatísticas
    stats_analysis = Column(JSON)  # form, xG, H2H

    # Fase 3: Previsões de cada modelo
    markov_prediction = Column(JSON)
    poisson_prediction = Column(JSON)
    elo_prediction = Column(JSON)
    dixon_coles_prediction = Column(JSON)
    ensemble_prediction = Column(JSON)

    # Fase 4: Recomendação final
    final_recommendation = Column(JSON)
    confidence_score = Column(Float)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class ModelPerformance(Base):
    """Performance de cada modelo."""
    __tablename__ = "model_performance"

    id = Column(Integer, primary_key=True)
    model_name = Column(String(50), nullable=False)
    date = Column(Date, nullable=False)

    # Métricas
    total_predictions = Column(Integer, default=0)
    correct_predictions = Column(Integer, default=0)
    brier_score = Column(Float)
    log_loss = Column(Float)
    calibration_error = Column(Float)
    roi = Column(Float)

    # Detalhes
    predictions_detail = Column(JSON)

    __table_args__ = (
        UniqueConstraint("model_name", "date", name="uq_model_date"),
        Index("ix_model_perf_date", "date"),
    )


# ============================================================================
# CONFIGURAÇÕES E LOGS
# ============================================================================

class SystemConfig(Base):
    """Configurações do sistema."""
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    value_type = Column(String(20))  # string, int, float, json, bool
    description = Column(Text)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class SystemLog(Base):
    """Logs do sistema."""
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=func.now(), index=True)
    level = Column(String(20))  # INFO, WARNING, ERROR
    module = Column(String(100))
    message = Column(Text)
    details = Column(JSON)

    __table_args__ = (
        Index("ix_logs_level", "level"),
    )
