import datetime
from pathlib import Path

from sqlalchemy import Column, DateTime, Integer, String, create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False, unique=True)
    r2_url = Column(String(512), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    event_id = Column(String(16), nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "filename": self.filename,
            "r2_url": self.r2_url,
            "timestamp": self.timestamp.isoformat(),
            "event_id": self.event_id,
        }


def init_db(db_path: Path) -> sessionmaker:
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    # Migrate: add event_id column to existing photos tables that predate this feature
    with engine.connect() as conn:
        cols = [row[1] for row in conn.execute(text("PRAGMA table_info(photos)"))]
        if "event_id" not in cols:
            conn.execute(text("ALTER TABLE photos ADD COLUMN event_id VARCHAR(16)"))
            conn.commit()
    return sessionmaker(engine)
