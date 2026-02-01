"""Initial schema with all models

Revision ID: 0001
Revises:
Create Date: 2025-01-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create leagues table
    op.create_table(
        'leagues',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('external_id', sa.String(50), nullable=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('country', sa.String(50), nullable=True),
        sa.Column('season', sa.String(20), nullable=True),
        sa.Column('priority', sa.Integer(), default=2),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('footystats_id', sa.Integer(), nullable=True),
        sa.Column('odds_api_key', sa.String(100), nullable=True),
        sa.Column('fbref_path', sa.String(200), nullable=True),
        sa.Column('min_edge', sa.Float(), default=5.0),
        sa.Column('max_stake', sa.Float(), default=3.0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_leagues_external_id', 'leagues', ['external_id'], unique=True)

    # Create teams table
    op.create_table(
        'teams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('external_id', sa.String(50), nullable=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('short_name', sa.String(20), nullable=True),
        sa.Column('country', sa.String(50), nullable=True),
        sa.Column('league_id', sa.Integer(), sa.ForeignKey('leagues.id'), nullable=True),
        sa.Column('squad_value', sa.Float(), default=0),
        sa.Column('avg_age', sa.Float(), nullable=True),
        sa.Column('total_spent', sa.Float(), default=0),
        sa.Column('total_earned', sa.Float(), default=0),
        sa.Column('elo_rating', sa.Float(), default=1500),
        sa.Column('attack_strength', sa.Float(), default=1.0),
        sa.Column('defense_strength', sa.Float(), default=1.0),
        sa.Column('footystats_id', sa.Integer(), nullable=True),
        sa.Column('transfermarkt_id', sa.String(50), nullable=True),
        sa.Column('fbref_id', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_teams_external_id', 'teams', ['external_id'], unique=True)
    op.create_index('ix_teams_name', 'teams', ['name'])

    # Create players table
    op.create_table(
        'players',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('external_id', sa.String(50), nullable=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('position', sa.String(30), nullable=True),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('nationality', sa.String(50), nullable=True),
        sa.Column('team_id', sa.Integer(), sa.ForeignKey('teams.id'), nullable=True),
        sa.Column('market_value', sa.Float(), default=0),
        sa.Column('contract_until', sa.Date(), nullable=True),
        sa.Column('is_injured', sa.Boolean(), default=False),
        sa.Column('is_suspended', sa.Boolean(), default=False),
        sa.Column('injury_type', sa.String(100), nullable=True),
        sa.Column('return_date', sa.Date(), nullable=True),
        sa.Column('goals', sa.Integer(), default=0),
        sa.Column('assists', sa.Integer(), default=0),
        sa.Column('minutes_played', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_players_external_id', 'players', ['external_id'], unique=True)

    # Create matches table
    op.create_table(
        'matches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('external_id', sa.String(50), nullable=True),
        sa.Column('home_team_id', sa.Integer(), sa.ForeignKey('teams.id'), nullable=False),
        sa.Column('away_team_id', sa.Integer(), sa.ForeignKey('teams.id'), nullable=False),
        sa.Column('league_id', sa.Integer(), sa.ForeignKey('leagues.id'), nullable=True),
        sa.Column('kickoff', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(20), default='scheduled'),
        sa.Column('home_goals', sa.Integer(), nullable=True),
        sa.Column('away_goals', sa.Integer(), nullable=True),
        sa.Column('home_goals_ht', sa.Integer(), nullable=True),
        sa.Column('away_goals_ht', sa.Integer(), nullable=True),
        sa.Column('home_xg', sa.Float(), nullable=True),
        sa.Column('away_xg', sa.Float(), nullable=True),
        sa.Column('home_shots', sa.Integer(), nullable=True),
        sa.Column('away_shots', sa.Integer(), nullable=True),
        sa.Column('home_shots_on_target', sa.Integer(), nullable=True),
        sa.Column('away_shots_on_target', sa.Integer(), nullable=True),
        sa.Column('home_possession', sa.Float(), nullable=True),
        sa.Column('away_possession', sa.Float(), nullable=True),
        sa.Column('home_corners', sa.Integer(), nullable=True),
        sa.Column('away_corners', sa.Integer(), nullable=True),
        sa.Column('pred_home_win', sa.Float(), nullable=True),
        sa.Column('pred_draw', sa.Float(), nullable=True),
        sa.Column('pred_away_win', sa.Float(), nullable=True),
        sa.Column('pred_over_25', sa.Float(), nullable=True),
        sa.Column('pred_btts', sa.Float(), nullable=True),
        sa.Column('prediction_confidence', sa.Float(), nullable=True),
        sa.Column('venue', sa.String(100), nullable=True),
        sa.Column('referee', sa.String(100), nullable=True),
        sa.Column('attendance', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_matches_external_id', 'matches', ['external_id'], unique=True)
    op.create_index('ix_matches_kickoff', 'matches', ['kickoff'])
    op.create_index('ix_matches_status', 'matches', ['status'])

    # Create odds_history table
    op.create_table(
        'odds_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('match_id', sa.Integer(), sa.ForeignKey('matches.id'), nullable=False),
        sa.Column('bookmaker', sa.String(50), nullable=False),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('home_odds', sa.Float(), nullable=True),
        sa.Column('draw_odds', sa.Float(), nullable=True),
        sa.Column('away_odds', sa.Float(), nullable=True),
        sa.Column('over_25_odds', sa.Float(), nullable=True),
        sa.Column('under_25_odds', sa.Float(), nullable=True),
        sa.Column('over_15_odds', sa.Float(), nullable=True),
        sa.Column('under_15_odds', sa.Float(), nullable=True),
        sa.Column('btts_yes_odds', sa.Float(), nullable=True),
        sa.Column('btts_no_odds', sa.Float(), nullable=True),
        sa.Column('handicap_line', sa.Float(), nullable=True),
        sa.Column('handicap_home_odds', sa.Float(), nullable=True),
        sa.Column('handicap_away_odds', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_odds_history_timestamp', 'odds_history', ['timestamp'])
    op.create_index('ix_odds_match_time', 'odds_history', ['match_id', 'timestamp'])

    # Create value_bets table
    op.create_table(
        'value_bets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('match_id', sa.Integer(), sa.ForeignKey('matches.id'), nullable=False),
        sa.Column('market', sa.String(50), nullable=False),
        sa.Column('selection', sa.String(100), nullable=False),
        sa.Column('bookmaker', sa.String(50), nullable=True),
        sa.Column('odds', sa.Float(), nullable=False),
        sa.Column('fair_odds', sa.Float(), nullable=True),
        sa.Column('probability', sa.Float(), nullable=True),
        sa.Column('edge', sa.Float(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('kelly_stake', sa.Float(), nullable=True),
        sa.Column('ev', sa.Float(), nullable=True),
        sa.Column('signal', sa.String(20), nullable=True),
        sa.Column('detected_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('notified', sa.Boolean(), default=False),
        sa.Column('notified_at', sa.DateTime(), nullable=True),
        sa.Column('outcome', sa.String(20), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_valuebets_detected', 'value_bets', ['detected_at'])
    op.create_index('ix_valuebets_signal', 'value_bets', ['signal'])

    # Create bets table
    op.create_table(
        'bets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('match_id', sa.Integer(), sa.ForeignKey('matches.id'), nullable=True),
        sa.Column('value_bet_id', sa.Integer(), sa.ForeignKey('value_bets.id'), nullable=True),
        sa.Column('bookmaker', sa.String(50), nullable=False),
        sa.Column('market', sa.String(50), nullable=False),
        sa.Column('selection', sa.String(100), nullable=False),
        sa.Column('odds', sa.Float(), nullable=False),
        sa.Column('stake', sa.Float(), nullable=False),
        sa.Column('potential_return', sa.Float(), nullable=True),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('profit', sa.Float(), default=0),
        sa.Column('placed_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('settled_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('screenshot_path', sa.String(500), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_bets_status', 'bets', ['status'])
    op.create_index('ix_bets_placed', 'bets', ['placed_at'])

    # Create bankroll_history table
    op.create_table(
        'bankroll_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('balance', sa.Float(), nullable=False),
        sa.Column('change', sa.Float(), default=0),
        sa.Column('reason', sa.String(100), nullable=True),
        sa.Column('bet_id', sa.Integer(), sa.ForeignKey('bets.id'), nullable=True),
        sa.Column('total_bets', sa.Integer(), default=0),
        sa.Column('total_wins', sa.Integer(), default=0),
        sa.Column('total_profit', sa.Float(), default=0),
        sa.Column('roi', sa.Float(), default=0),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_bankroll_timestamp', 'bankroll_history', ['timestamp'])

    # Create match_analyses table
    op.create_table(
        'match_analyses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('match_id', sa.Integer(), sa.ForeignKey('matches.id'), nullable=True, unique=True),
        sa.Column('pre_analysis', sa.JSON(), nullable=True),
        sa.Column('stats_analysis', sa.JSON(), nullable=True),
        sa.Column('markov_prediction', sa.JSON(), nullable=True),
        sa.Column('poisson_prediction', sa.JSON(), nullable=True),
        sa.Column('elo_prediction', sa.JSON(), nullable=True),
        sa.Column('dixon_coles_prediction', sa.JSON(), nullable=True),
        sa.Column('ensemble_prediction', sa.JSON(), nullable=True),
        sa.Column('final_recommendation', sa.JSON(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

    # Create model_performance table
    op.create_table(
        'model_performance',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model_name', sa.String(50), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('total_predictions', sa.Integer(), default=0),
        sa.Column('correct_predictions', sa.Integer(), default=0),
        sa.Column('brier_score', sa.Float(), nullable=True),
        sa.Column('log_loss', sa.Float(), nullable=True),
        sa.Column('calibration_error', sa.Float(), nullable=True),
        sa.Column('roi', sa.Float(), nullable=True),
        sa.Column('predictions_detail', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('model_name', 'date', name='uq_model_date')
    )
    op.create_index('ix_model_perf_date', 'model_performance', ['date'])

    # Create system_config table
    op.create_table(
        'system_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(100), nullable=False, unique=True),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('value_type', sa.String(20), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

    # Create system_logs table
    op.create_table(
        'system_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('level', sa.String(20), nullable=True),
        sa.Column('module', sa.String(100), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_logs_timestamp', 'system_logs', ['timestamp'])
    op.create_index('ix_logs_level', 'system_logs', ['level'])


def downgrade() -> None:
    op.drop_table('system_logs')
    op.drop_table('system_config')
    op.drop_table('model_performance')
    op.drop_table('match_analyses')
    op.drop_table('bankroll_history')
    op.drop_table('bets')
    op.drop_table('value_bets')
    op.drop_table('odds_history')
    op.drop_table('matches')
    op.drop_table('players')
    op.drop_table('teams')
    op.drop_table('leagues')
