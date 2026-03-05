"""Database configuration and session management for async SQLAlchemy."""

import logging
from urllib.parse import quote_plus
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config.settings import settings

logger = logging.getLogger(__name__)


class Database:
    """Manage a singleton async connection to PostgreSQL.

    Attributes:
        engine: Async engine instance.
        session_factory: Factory for async sessions.
    """

    def __init__(self):
        self.engine = self._create_engine()
        self.session_factory = self._create_session_factory()

    def _build_url(self) -> str:
        """Build the async SQLAlchemy URL with an escaped password.

        Returns:
            str: Async PostgreSQL connection URL.
        """
        safe_password = quote_plus(settings.POSTGRES_PASSWORD)
        return (
            f"postgresql+asyncpg://{settings.POSTGRES_USER}:{safe_password}"
            f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        )

    def _create_engine(self):
        """Create the async engine.

        Returns:
            AsyncEngine: SQLAlchemy async engine instance.
        """
        url = self._build_url()
        return create_async_engine(url, echo=settings.DB_ECHO)

    def _create_session_factory(self):
        """Create the async session factory.

        Returns:
            sessionmaker: Async session factory.
        """
        return sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def check_connection(self) -> bool:
        """Check database connectivity.

        Returns:
            bool: True if a connection can be opened, otherwise False.
        """
        try:
            async with self.engine.connect():
                logger.info("✅ Conectado a PostgreSQL")
                return True
        except Exception as e:
            logger.error(f"❌ Error conectando a PostgreSQL: {e}")
            return False


# Singleton instance for the application
db = Database()


async def get_db():
    """Yield an async session for request-scoped database access.

    Yields:
        AsyncSession: Database session.
    """
    async with db.session_factory() as session:
        yield session


class Base(DeclarativeBase):
    """Declarative base for ORM models."""

    pass
