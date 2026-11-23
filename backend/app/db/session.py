import logging
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

logger = logging.getLogger("stenovision.db")


class Base(DeclarativeBase):
    pass


def build_engine():
    target_url = settings.DATABASE_URL
    fallback_url = "sqlite:///./stenovision.db"

    if target_url.startswith("postgresql"):
        try:
            # Attempt to initialize PostgreSQL engine with pooling
            pg_engine = create_engine(
                target_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
            )
            # Verify live connectivity
            with pg_engine.connect() as conn:
                logger.info("[DATABASE] Connected successfully to Primary PostgreSQL Database.")
                return pg_engine
        except (OperationalError, Exception) as exc:
            logger.warning(
                f"[DATABASE] Primary PostgreSQL ({target_url}) is not reachable on host ({exc}). "
                f"Activating persistent local database fallback ({fallback_url}) to maintain uninterrupted service."
            )
            # Fall back to local persistent storage engine
            return create_engine(
                fallback_url,
                connect_args={"check_same_thread": False},
                pool_pre_ping=True,
            )
    else:
        connect_args = {"check_same_thread": False} if target_url.startswith("sqlite") else {}
        return create_engine(target_url, connect_args=connect_args, pool_pre_ping=True)


engine = build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
