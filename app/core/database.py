from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from alembic import command
from alembic.config import Config
from app.core.config import settings

engine = create_engine(settings.database_url.unicode_string())
session_factory = sessionmaker(bind=engine)

Base = declarative_base()


def get_db():
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


def run_migrations():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
