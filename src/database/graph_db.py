"""
Graph Database - Neo4j
======================
Banco de grafos para modelar relações entre:
- Times ↔ Times (confrontos)
- Times ↔ Jogadores
- Times ↔ Ligas
- Jogadores ↔ Transferências
- Técnicos ↔ Times
- Times ↔ Resultados

Permite queries complexas como:
- "Times que sempre perdem para times com técnico X"
- "Jogadores que marcaram contra time Y nos últimos 5 jogos"
- "Padrão de resultados quando time A joga fora"
"""

from typing import Optional, Any
from dataclasses import dataclass
from datetime import datetime, date
from loguru import logger


@dataclass
class Neo4jConfig:
    """Configuração do Neo4j."""
    uri: str = "bolt://localhost:7687"
    user: str = "neo4j"
    password: str = "password"
    database: str = "lobinho"


class GraphDatabase:
    """
    Interface com Neo4j para análise de relações.

    Nós (Nodes):
    - Team: Time de futebol
    - Player: Jogador
    - Coach: Técnico
    - League: Campeonato
    - Match: Partida
    - Season: Temporada

    Relacionamentos (Edges):
    - PLAYED_AGAINST: Time → Time
    - PLAYS_FOR: Jogador → Time
    - COACHES: Técnico → Time
    - BELONGS_TO: Time → Liga
    - SCORED_IN: Jogador → Partida
    - TRANSFERRED_TO: Jogador → Time
    """

    def __init__(self, config: Optional[Neo4jConfig] = None):
        self.config = config or Neo4jConfig()
        self.driver = None

    async def connect(self):
        """Conecta ao Neo4j."""
        try:
            from neo4j import AsyncGraphDatabase
            self.driver = AsyncGraphDatabase.driver(
                self.config.uri,
                auth=(self.config.user, self.config.password),
            )
            logger.info("Connected to Neo4j")
        except ImportError:
            logger.warning("Neo4j driver not installed. Using in-memory graph.")
            self.driver = None
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self.driver = None

    async def close(self):
        """Fecha conexão."""
        if self.driver:
            await self.driver.close()

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    # =========================================================================
    # CRIAÇÃO DE NÓS
    # =========================================================================

    async def create_team(
        self,
        team_id: str,
        name: str,
        country: str,
        league: str,
        squad_value: float = 0,
    ):
        """Cria nó de time."""
        query = """
        MERGE (t:Team {id: $team_id})
        SET t.name = $name,
            t.country = $country,
            t.league = $league,
            t.squad_value = $squad_value,
            t.updated_at = datetime()
        RETURN t
        """
        await self._run_query(query, {
            "team_id": team_id,
            "name": name,
            "country": country,
            "league": league,
            "squad_value": squad_value,
        })

    async def create_match(
        self,
        match_id: str,
        home_team_id: str,
        away_team_id: str,
        home_goals: int,
        away_goals: int,
        match_date: date,
        league: str,
    ):
        """Cria nó de partida e relacionamentos."""
        query = """
        MATCH (home:Team {id: $home_team_id})
        MATCH (away:Team {id: $away_team_id})

        MERGE (m:Match {id: $match_id})
        SET m.home_goals = $home_goals,
            m.away_goals = $away_goals,
            m.date = $match_date,
            m.league = $league

        MERGE (home)-[ph:PLAYED_HOME]->(m)
        MERGE (away)-[pa:PLAYED_AWAY]->(m)

        MERGE (home)-[h2h:PLAYED_AGAINST]->(away)
        ON CREATE SET h2h.matches = 1, h2h.home_wins = 0, h2h.draws = 0, h2h.away_wins = 0
        ON MATCH SET h2h.matches = h2h.matches + 1

        WITH home, away, m, h2h,
             CASE WHEN $home_goals > $away_goals THEN 1 ELSE 0 END as home_win,
             CASE WHEN $home_goals = $away_goals THEN 1 ELSE 0 END as draw,
             CASE WHEN $home_goals < $away_goals THEN 1 ELSE 0 END as away_win

        SET h2h.home_wins = h2h.home_wins + home_win,
            h2h.draws = h2h.draws + draw,
            h2h.away_wins = h2h.away_wins + away_win

        RETURN m
        """
        await self._run_query(query, {
            "match_id": match_id,
            "home_team_id": home_team_id,
            "away_team_id": away_team_id,
            "home_goals": home_goals,
            "away_goals": away_goals,
            "match_date": match_date.isoformat(),
            "league": league,
        })

    async def create_player(
        self,
        player_id: str,
        name: str,
        position: str,
        team_id: str,
        market_value: float = 0,
    ):
        """Cria nó de jogador."""
        query = """
        MERGE (p:Player {id: $player_id})
        SET p.name = $name,
            p.position = $position,
            p.market_value = $market_value

        WITH p
        MATCH (t:Team {id: $team_id})
        MERGE (p)-[:PLAYS_FOR]->(t)

        RETURN p
        """
        await self._run_query(query, {
            "player_id": player_id,
            "name": name,
            "position": position,
            "team_id": team_id,
            "market_value": market_value,
        })

    # =========================================================================
    # QUERIES DE ANÁLISE
    # =========================================================================

    async def get_h2h_stats(self, team1_id: str, team2_id: str) -> dict:
        """Retorna estatísticas de confrontos diretos."""
        query = """
        MATCH (t1:Team {id: $team1_id})-[h2h:PLAYED_AGAINST]->(t2:Team {id: $team2_id})
        RETURN h2h.matches as total_matches,
               h2h.home_wins as team1_home_wins,
               h2h.draws as draws,
               h2h.away_wins as team2_away_wins
        """
        result = await self._run_query(query, {
            "team1_id": team1_id,
            "team2_id": team2_id,
        })
        return result[0] if result else {}

    async def get_team_form_graph(self, team_id: str, last_n: int = 10) -> list[dict]:
        """Retorna forma do time como grafo de resultados."""
        query = """
        MATCH (t:Team {id: $team_id})-[:PLAYED_HOME|PLAYED_AWAY]->(m:Match)
        WITH t, m ORDER BY m.date DESC LIMIT $last_n

        RETURN m.id as match_id,
               m.home_goals as home_goals,
               m.away_goals as away_goals,
               m.date as date,
               CASE
                   WHEN (t)-[:PLAYED_HOME]->(m) THEN 'home'
                   ELSE 'away'
               END as venue
        """
        return await self._run_query(query, {
            "team_id": team_id,
            "last_n": last_n,
        })

    async def find_patterns(self, team_id: str) -> dict:
        """
        Encontra padrões no grafo de resultados.

        Retorna:
        - Sequências de vitórias/derrotas
        - Times que sempre perde
        - Times que sempre vence
        - Padrões em casa vs fora
        """
        query = """
        // Times que sempre perde para
        MATCH (t:Team {id: $team_id})-[h2h:PLAYED_AGAINST]->(opponent:Team)
        WHERE h2h.matches >= 3 AND h2h.home_wins = 0 AND h2h.draws = 0
        WITH collect({team: opponent.name, matches: h2h.matches}) as always_loses

        // Times que sempre vence
        MATCH (t:Team {id: $team_id})-[h2h:PLAYED_AGAINST]->(opponent:Team)
        WHERE h2h.matches >= 3 AND h2h.away_wins = 0 AND h2h.draws = 0
        WITH always_loses, collect({team: opponent.name, matches: h2h.matches}) as always_wins

        // Performance em casa
        MATCH (t:Team {id: $team_id})-[:PLAYED_HOME]->(m:Match)
        WITH always_loses, always_wins,
             count(m) as home_matches,
             sum(CASE WHEN m.home_goals > m.away_goals THEN 1 ELSE 0 END) as home_wins

        RETURN always_loses, always_wins, home_matches, home_wins,
               toFloat(home_wins) / home_matches as home_win_rate
        """
        result = await self._run_query(query, {"team_id": team_id})
        return result[0] if result else {}

    async def get_connected_teams(self, team_id: str, depth: int = 2) -> list[dict]:
        """
        Encontra times conectados até N níveis de profundidade.

        Útil para encontrar padrões indiretos:
        "Time A perdeu para B, que perdeu para C, então A pode ter dificuldade contra C"
        """
        query = """
        MATCH path = (t:Team {id: $team_id})-[:PLAYED_AGAINST*1..$depth]-(connected:Team)
        WHERE connected.id <> $team_id
        WITH connected, length(path) as distance,
             [r in relationships(path) | {
                 matches: r.matches,
                 home_wins: r.home_wins,
                 draws: r.draws,
                 away_wins: r.away_wins
             }] as relationships
        RETURN connected.id as team_id,
               connected.name as team_name,
               distance,
               relationships
        ORDER BY distance
        LIMIT 20
        """
        return await self._run_query(query, {
            "team_id": team_id,
            "depth": depth,
        })

    async def predict_match_graph(self, home_id: str, away_id: str) -> dict:
        """
        Previsão baseada no grafo de relações.

        Considera:
        - H2H direto
        - Conexões indiretas (times em comum)
        - Padrões de resultados
        """
        query = """
        // H2H direto
        OPTIONAL MATCH (home:Team {id: $home_id})-[h2h:PLAYED_AGAINST]-(away:Team {id: $away_id})

        // Times em comum que ambos enfrentaram
        OPTIONAL MATCH (home)-[r1:PLAYED_AGAINST]-(common:Team)-[r2:PLAYED_AGAINST]-(away)
        WHERE common.id <> $home_id AND common.id <> $away_id

        WITH home, away, h2h,
             collect({
                 common_team: common.name,
                 home_vs_common: {wins: r1.home_wins + r1.away_wins, draws: r1.draws},
                 away_vs_common: {wins: r2.home_wins + r2.away_wins, draws: r2.draws}
             }) as common_opponents

        // Forma recente
        OPTIONAL MATCH (home)-[:PLAYED_HOME|PLAYED_AWAY]->(hm:Match)
        WITH home, away, h2h, common_opponents, collect(hm) as home_matches
        OPTIONAL MATCH (away)-[:PLAYED_HOME|PLAYED_AWAY]->(am:Match)

        RETURN {
            h2h: h2h,
            common_opponents: common_opponents,
            home_recent_matches: size(home_matches),
            away_recent_matches: count(am)
        } as analysis
        """
        result = await self._run_query(query, {
            "home_id": home_id,
            "away_id": away_id,
        })
        return result[0] if result else {}

    async def get_graph_ranking(self, league: str, limit: int = 20) -> list[dict]:
        """
        Ranking de times usando PageRank adaptado.

        Times que vencem times fortes ganham mais pontos.
        """
        query = """
        CALL gds.pageRank.stream({
            nodeProjection: 'Team',
            relationshipProjection: {
                BEAT: {
                    type: 'PLAYED_AGAINST',
                    properties: ['home_wins', 'away_wins'],
                    orientation: 'NATURAL'
                }
            },
            relationshipWeightProperty: 'home_wins'
        })
        YIELD nodeId, score
        WITH gds.util.asNode(nodeId) AS team, score
        WHERE team.league = $league
        RETURN team.name as team, score
        ORDER BY score DESC
        LIMIT $limit
        """
        try:
            return await self._run_query(query, {
                "league": league,
                "limit": limit,
            })
        except:
            # Fallback se GDS não estiver instalado
            return []

    # =========================================================================
    # UTILITÁRIOS
    # =========================================================================

    async def _run_query(self, query: str, params: dict = None) -> list[dict]:
        """Executa query no Neo4j."""
        if not self.driver:
            logger.debug("No Neo4j driver, returning empty result")
            return []

        async with self.driver.session() as session:
            result = await session.run(query, params or {})
            records = await result.data()
            return records

    async def setup_indexes(self):
        """Cria índices para performance."""
        indexes = [
            "CREATE INDEX team_id IF NOT EXISTS FOR (t:Team) ON (t.id)",
            "CREATE INDEX match_id IF NOT EXISTS FOR (m:Match) ON (m.id)",
            "CREATE INDEX player_id IF NOT EXISTS FOR (p:Player) ON (p.id)",
            "CREATE INDEX match_date IF NOT EXISTS FOR (m:Match) ON (m.date)",
        ]
        for idx in indexes:
            await self._run_query(idx)

        logger.info("Neo4j indexes created")

    async def clear_database(self):
        """Limpa todos os dados (use com cuidado!)."""
        await self._run_query("MATCH (n) DETACH DELETE n")
        logger.warning("Neo4j database cleared!")


# ============================================================================
# IN-MEMORY GRAPH (fallback se Neo4j não estiver disponível)
# ============================================================================

class InMemoryGraph:
    """
    Grafo em memória para quando Neo4j não está disponível.
    Implementação simples usando dicionários.
    """

    def __init__(self):
        self.nodes: dict[str, dict] = {}
        self.edges: list[dict] = []

    def add_node(self, node_id: str, label: str, properties: dict):
        """Adiciona nó."""
        self.nodes[node_id] = {
            "id": node_id,
            "label": label,
            **properties,
        }

    def add_edge(self, from_id: str, to_id: str, rel_type: str, properties: dict = None):
        """Adiciona aresta."""
        self.edges.append({
            "from": from_id,
            "to": to_id,
            "type": rel_type,
            **(properties or {}),
        })

    def get_neighbors(self, node_id: str, rel_type: str = None) -> list[str]:
        """Retorna vizinhos de um nó."""
        neighbors = []
        for edge in self.edges:
            if edge["from"] == node_id:
                if rel_type is None or edge["type"] == rel_type:
                    neighbors.append(edge["to"])
            elif edge["to"] == node_id:
                if rel_type is None or edge["type"] == rel_type:
                    neighbors.append(edge["from"])
        return neighbors

    def get_path(self, from_id: str, to_id: str, max_depth: int = 3) -> list[str]:
        """Encontra caminho entre dois nós (BFS)."""
        if from_id == to_id:
            return [from_id]

        visited = {from_id}
        queue = [(from_id, [from_id])]

        while queue:
            current, path = queue.pop(0)

            if len(path) > max_depth:
                continue

            for neighbor in self.get_neighbors(current):
                if neighbor == to_id:
                    return path + [neighbor]

                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return []

    def calculate_pagerank(self, damping: float = 0.85, iterations: int = 20) -> dict[str, float]:
        """Calcula PageRank simplificado."""
        n = len(self.nodes)
        if n == 0:
            return {}

        # Inicializa scores
        scores = {node_id: 1.0 / n for node_id in self.nodes}

        for _ in range(iterations):
            new_scores = {}

            for node_id in self.nodes:
                # Soma contribuições dos vizinhos
                incoming = [e["from"] for e in self.edges if e["to"] == node_id]
                rank_sum = sum(
                    scores[inc] / len(self.get_neighbors(inc))
                    for inc in incoming
                    if self.get_neighbors(inc)
                )

                new_scores[node_id] = (1 - damping) / n + damping * rank_sum

            scores = new_scores

        return scores
