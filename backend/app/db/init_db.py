from pathlib import Path
import sqlite3

from app.db.models import ExamSession, Measurement, Patient, Snapshot, User, UserSession  # noqa: F401
from app.db.session import Base, engine


def init_db() -> None:
    db_file = Path(str(engine.url).replace("sqlite:///", ""))
    db_file.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    _run_lightweight_migrations(db_file)


def _run_lightweight_migrations(db_file: Path) -> None:
    if not db_file.exists():
        return

    conn = sqlite3.connect(str(db_file))
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(patients)")
        columns = [row[1] for row in cursor.fetchall()]
        if "user_id" not in columns:
            cursor.execute("ALTER TABLE patients ADD COLUMN user_id INTEGER")
            conn.commit()
    finally:
        conn.close()
