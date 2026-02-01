"""
Setup Script - LOBINHO-BET
==========================
Inicializa o ambiente completo.
"""

import asyncio
import subprocess
import sys
from pathlib import Path
from loguru import logger


async def setup_neo4j():
    """Configura Neo4j com índices e constraints."""
    from src.database.graph_db import GraphDatabase

    logger.info("Setting up Neo4j...")

    async with GraphDatabase() as db:
        await db.setup_indexes()

        # Cria alguns dados de exemplo
        await db.create_team("flamengo", "Flamengo", "Brazil", "brasileirao_a", 180.5)
        await db.create_team("palmeiras", "Palmeiras", "Brazil", "brasileirao_a", 165.0)
        await db.create_team("man_city", "Manchester City", "England", "premier_league", 1100.0)
        await db.create_team("liverpool", "Liverpool", "England", "premier_league", 850.0)

    logger.info("Neo4j setup complete!")


async def setup_database():
    """Configura banco de dados PostgreSQL."""
    logger.info("Setting up PostgreSQL...")
    # Aqui você rodaria migrations com Alembic
    logger.info("PostgreSQL setup complete!")


def install_playwright():
    """Instala navegadores do Playwright."""
    logger.info("Installing Playwright browsers...")
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
    logger.info("Playwright installed!")


def check_docker():
    """Verifica se Docker está rodando."""
    try:
        result = subprocess.run(
            ["docker", "ps"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            logger.info("Docker is running")
            return True
        else:
            logger.warning("Docker is not running")
            return False
    except FileNotFoundError:
        logger.error("Docker not found. Please install Docker.")
        return False


def start_docker_services():
    """Inicia serviços Docker."""
    logger.info("Starting Docker services...")
    subprocess.run(["docker-compose", "up", "-d"])
    logger.info("Docker services started!")


def create_env_file():
    """Cria arquivo .env a partir do exemplo."""
    env_example = Path(".env.example")
    env_file = Path(".env")

    if not env_file.exists() and env_example.exists():
        env_file.write_text(env_example.read_text())
        logger.info("Created .env file from .env.example")
    else:
        logger.info(".env file already exists")


async def main():
    """Setup completo."""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   🐺 LOBINHO-BET - Setup                                  ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

    # 1. Cria .env
    create_env_file()

    # 2. Verifica Docker
    if check_docker():
        start_docker_services()

        # Aguarda serviços iniciarem
        logger.info("Waiting for services to start...")
        await asyncio.sleep(10)

        # 3. Setup Neo4j
        try:
            await setup_neo4j()
        except Exception as e:
            logger.warning(f"Neo4j setup skipped: {e}")

    # 4. Instala Playwright
    install_playwright()

    print("""
    ✅ Setup completo!

    Próximos passos:
    1. Edite o arquivo .env com suas chaves de API
    2. Execute: python main.py --status
    3. Acesse o dashboard: python -m src.api.dashboard

    Documentação:
    - Neo4j Browser: http://localhost:7474
    - Dashboard: http://localhost:8000
    """)


if __name__ == "__main__":
    asyncio.run(main())
