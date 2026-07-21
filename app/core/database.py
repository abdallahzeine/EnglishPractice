from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import DB_PATH, ensure_data_dir


class Base(DeclarativeBase):
    pass


ensure_data_dir()
engine = create_engine(f"sqlite:///{DB_PATH}")
SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)


def init_db() -> None:
    from app.domain import tables  # noqa: F401  — registers ORM models

    Base.metadata.create_all(engine)
