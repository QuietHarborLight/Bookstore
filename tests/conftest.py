import sqlite3
from pathlib import Path

import pytest

import db


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test_bookstore.db"


@pytest.fixture
def conn(db_path: Path) -> sqlite3.Connection:
    db.init_db(db_path)
    connection = db.get_connection(db_path)
    yield connection
    connection.close()
