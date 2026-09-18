import sqlite3
from contextlib import contextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()
DATABASE_PATH = Path(__file__).with_name("users.db")


class User(BaseModel):
    id: int
    username: str
    email: str


class UserCreate(BaseModel):
    username: str
    email: str


INITIAL_USERS = [
    ("alice", "alice@example.com"),
    ("bob", "bob@example.com"),
    ("carol", "carol@example.com"),
]


@contextmanager
def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


def init_db() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT NOT NULL
            )
            """
        )
        user_count = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if user_count == 0:
            connection.executemany(
                "INSERT INTO users (username, email) VALUES (?, ?)",
                INITIAL_USERS,
            )
        connection.commit()


def row_to_user(row: sqlite3.Row) -> User:
    return User(id=row["id"], username=row["username"], email=row["email"])


init_db()


@app.get("/users/")
def get_all_users():
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT id, username, email FROM users ORDER BY id"
        ).fetchall()
    return [row_to_user(row) for row in rows]


@app.get("/users/{user_id}")
def get_user(user_id: int):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id, username, email FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")
    return row_to_user(row)


@app.post("/create_user", response_model=User, status_code=201)
def create_user(user_data: UserCreate):
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO users (username, email) VALUES (?, ?)",
            (user_data.username, user_data.email),
        )
        connection.commit()
        new_user_id = cursor.lastrowid
        row = connection.execute(
            "SELECT id, username, email FROM users WHERE id = ?", (new_user_id,)
        ).fetchone()
    return row_to_user(row)
