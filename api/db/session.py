import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

database_url = os.getenv("DATABASE_URL", "sqlite:///./us.db")
if database_url.startswith(("postgresql://", "postgres://")):
	database_url = database_url.replace("://", "+psycopg://", 1)
elif database_url.startswith("postgresql+psycopg2://"):
	database_url = database_url.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)

connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}

engine = create_engine(database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()
