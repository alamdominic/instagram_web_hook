# app/config/database.py
import logging
from urllib.parse import quote_plus
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config.settings import settings

logger = logging.getLogger(__name__)


class Database:
    """
    Gestiona la conexión a PostgreSQL usando SQLAlchemy async.

    Patrón Singleton: una sola instancia para toda la app.
    El engine y la sesión se crean una vez y se reutilizan.

    Atributos:
        engine: Motor de conexión async a PostgreSQL
        session_factory: Fábrica de sesiones async

    Uso:
        from app.config.database import db, get_db
    """

    def __init__(self):
        self.engine = self._create_engine()
        self.session_factory = self._create_session_factory()

    def _build_url(self) -> str:
        """
        Construye la URL de conexión con el password codificado.
        Usa asyncpg como driver (requerido para FastAPI async).
        """
        safe_password = quote_plus(settings.POSTGRES_PASSWORD)
        return (
            f"postgresql+asyncpg://{settings.POSTGRES_USER}:{safe_password}"
            f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        )

    def _create_engine(self):
        """
        Crea el engine async.
        echo=True en DEBUG para ver los SQL en consola.
        """
        url = self._build_url()
        return create_async_engine(url, echo=settings.DEBUG)

    def _create_session_factory(self):
        """
        Crea la fábrica de sesiones.
        expire_on_commit=False evita errores al acceder
        a objetos después del commit en contexto async.
        """
        return sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def check_connection(self) -> bool:
        """Verifica que la conexión a PostgreSQL funciona."""
        try:
            async with self.engine.connect():
                logger.info("✅ Conectado a PostgreSQL")
                return True
        except Exception as e:
            logger.error(f"❌ Error conectando a PostgreSQL: {e}")
            return False


# Instancia única (Singleton) para toda la app
db = Database()


# Dependencia para inyectar la sesión en las rutas de FastAPI
async def get_db():
    async with db.session_factory() as session:
        yield session


# Base para todos los modelos (tablas)
class Base(DeclarativeBase):
    pass
