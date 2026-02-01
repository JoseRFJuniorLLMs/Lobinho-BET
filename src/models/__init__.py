# Imports com tratamento de dependências opcionais
__all__ = []

# LiveMarketAnalyzer não tem dependências externas pesadas
try:
    from .live_market_analyzer import (
        LiveMarketAnalyzer,
        LiveMatchData,
        MarketAnalysis,
        MarketType,
        OddsTrend,
        analisar_mercado_live
    )
    __all__.extend([
        "LiveMarketAnalyzer",
        "LiveMatchData",
        "MarketAnalysis",
        "MarketType",
        "OddsTrend",
        "analisar_mercado_live"
    ])
except ImportError as e:
    print(f"⚠️ LiveMarketAnalyzer não disponível: {e}")

# Predictor requer xgboost (opcional)
try:
    from .predictor import MatchPredictor
    __all__.append("MatchPredictor")
except ImportError as e:
    print(f"⚠️ MatchPredictor não disponível (instale xgboost): {e}")

# ValueDetector
try:
    from .value_detector import ValueDetector, ValueBet
    __all__.extend(["ValueDetector", "ValueBet"])
except ImportError as e:
    print(f"⚠️ ValueDetector não disponível: {e}")
