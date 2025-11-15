"""
Database configuration and models for suggestions storage.
"""

import os
from typing import List, Optional

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy import Column, Integer, MetaData, String, Table, Text, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

ph = PasswordHasher(
    time_cost=3, memory_cost=262144, parallelism=1, hash_len=32, salt_len=16
)

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/supikashi"
)

if "sqlite" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
metadata = MetaData()

users_table = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("username", String(50), unique=True, nullable=False, index=True),
    Column("password_hash", String(255), nullable=False),
)

suggestions_table = Table(
    "suggestions",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("user_id", Integer, nullable=False, index=True),
    Column("title", String(200), nullable=False),
    Column("text", Text, nullable=False),
    Column("status", String(50), default="new", index=True),
)


def init_db():
    """Initialize database tables."""
    metadata.create_all(bind=engine)


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_suggestion_db(
    user_id: int, title: str, text: str, status: str = "new"
) -> dict:
    """Create a new suggestion in the database."""
    with engine.connect() as conn:
        result = conn.execute(
            suggestions_table.insert()
            .values(user_id=user_id, title=title, text=text, status=status)
            .returning(
                suggestions_table.c.id,
                suggestions_table.c.user_id,
                suggestions_table.c.title,
                suggestions_table.c.text,
                suggestions_table.c.status,
            )
        )
        row = result.fetchone()
        conn.commit()
        return dict(row._mapping) if row else None


def get_suggestions_db(status: Optional[str] = None) -> List[dict]:
    """Get all suggestions, optionally filtered by status."""
    with engine.connect() as conn:
        query = suggestions_table.select()
        if status:
            query = query.where(suggestions_table.c.status == status)
        result = conn.execute(query)
        return [dict(row._mapping) for row in result.fetchall()]


def get_suggestion_by_id_db(suggestion_id: int) -> Optional[dict]:
    """Get a suggestion by ID."""
    with engine.connect() as conn:
        result = conn.execute(
            suggestions_table.select().where(suggestions_table.c.id == suggestion_id)
        )
        row = result.fetchone()
        return dict(row._mapping) if row else None


def update_suggestion_db(
    suggestion_id: int, title: str, text: str, status: str
) -> Optional[dict]:
    """Update a suggestion."""
    with engine.connect() as conn:
        result = conn.execute(
            suggestions_table.update()
            .where(suggestions_table.c.id == suggestion_id)
            .values(title=title, text=text, status=status)
            .returning(
                suggestions_table.c.id,
                suggestions_table.c.user_id,
                suggestions_table.c.title,
                suggestions_table.c.text,
                suggestions_table.c.status,
            )
        )
        row = result.fetchone()
        conn.commit()
        return dict(row._mapping) if row else None


def delete_suggestion_db(suggestion_id: int) -> bool:
    """Delete a suggestion."""
    with engine.connect() as conn:
        result = conn.execute(
            suggestions_table.delete().where(suggestions_table.c.id == suggestion_id)
        )
        rowcount = result.rowcount
        conn.commit()
        return rowcount > 0


def create_user_db(username: str, password: str) -> Optional[dict]:
    """Create a new user with hashed password."""
    password_hash = ph.hash(password)
    with engine.connect() as conn:
        try:
            result = conn.execute(
                users_table.insert()
                .values(username=username, password_hash=password_hash)
                .returning(users_table.c.id, users_table.c.username)
            )
            row = result.fetchone()
            conn.commit()
            return dict(row._mapping) if row else None
        except Exception:
            return None


def get_user_by_username_db(username: str) -> Optional[dict]:
    """Get user by username."""
    with engine.connect() as conn:
        result = conn.execute(
            users_table.select().where(users_table.c.username == username)
        )
        row = result.fetchone()
        return dict(row._mapping) if row else None


def verify_password_db(username: str, password: str) -> Optional[dict]:
    """Verify user password and return user data if valid."""
    user = get_user_by_username_db(username)
    if not user:
        return None

    try:
        ph.verify(user["password_hash"], password)

        if ph.check_needs_rehash(user["password_hash"]):
            new_hash = ph.hash(password)
            with engine.connect() as conn:
                conn.execute(
                    users_table.update()
                    .where(users_table.c.username == username)
                    .values(password_hash=new_hash)
                )
                conn.commit()

        return {"id": user["id"], "username": user["username"]}
    except VerifyMismatchError:
        return None
