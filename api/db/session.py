import os
from collections.abc import Generator

from datetime import datetime, timezone
import sqlite3
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from api.core.config import settings

database_url = settings.DATABASE_URL
if database_url.startswith(("postgresql://", "postgres://")):
	database_url = database_url.replace("://", "+psycopg://", 1)
elif database_url.startswith("postgresql+psycopg2://"):
	database_url = database_url.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)

connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}

engine = create_engine(database_url, connect_args=connect_args)


@event.listens_for(engine, "connect")
def register_sqlite_functions(dbapi_connection, connection_record):
	if isinstance(dbapi_connection, sqlite3.Connection):
		dbapi_connection.create_function("now", 0, lambda: datetime.now(timezone.utc).isoformat())


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()

