"""SQLite data access for the Bookstore MVP."""

from __future__ import annotations

import sqlite3
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


def default_db_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "bookstore.db"
    return Path(__file__).resolve().parent / "bookstore.db"


DEFAULT_DB_PATH = default_db_path()

CUSTOMER_ORDER_STATUSES = ("pending", "ordered", "received", "fulfilled")


class BookstoreError(Exception):
    """Base error for bookstore operations."""


class ValidationError(BookstoreError):
    """Invalid input or business rule violation."""


class NotFoundError(BookstoreError):
    """Requested record does not exist."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def get_connection(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def connect(db_path: str | Path = DEFAULT_DB_PATH) -> Iterator[sqlite3.Connection]:
    conn = get_connection(db_path)
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def init_db(db_path: str | Path = DEFAULT_DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                isbn TEXT NOT NULL UNIQUE,
                price REAL NOT NULL CHECK (price >= 0),
                stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                unit_price REAL NOT NULL CHECK (unit_price >= 0),
                sold_at TEXT NOT NULL,
                FOREIGN KEY (book_id) REFERENCES books(id)
            );

            CREATE TABLE IF NOT EXISTS purchase_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                ordered_at TEXT NOT NULL,
                received INTEGER NOT NULL DEFAULT 0 CHECK (received IN (0, 1)),
                received_at TEXT,
                FOREIGN KEY (book_id) REFERENCES books(id)
            );

            CREATE TABLE IF NOT EXISTS customer_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                book_title TEXT NOT NULL,
                book_id INTEGER,
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                status TEXT NOT NULL DEFAULT 'pending',
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (book_id) REFERENCES books(id)
            );
            """
        )
        conn.commit()


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def _require_non_empty(value: str, field: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValidationError(f"{field} is required.")
    return cleaned


def create_book(
    conn: sqlite3.Connection,
    *,
    title: str,
    author: str,
    isbn: str,
    price: float,
    stock: int,
    notes: str = "",
) -> dict[str, Any]:
    title = _require_non_empty(title, "Title")
    author = _require_non_empty(author, "Author")
    isbn = _require_non_empty(isbn, "ISBN")
    if price < 0:
        raise ValidationError("Price cannot be negative.")
    if stock < 0:
        raise ValidationError("Stock cannot be negative.")

    now = utc_now()
    try:
        with transaction(conn):
            cursor = conn.execute(
                """
                INSERT INTO books (title, author, isbn, price, stock, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (title, author, isbn, price, stock, notes.strip(), now, now),
            )
    except sqlite3.IntegrityError as exc:
        if "isbn" in str(exc).lower():
            raise ValidationError("A book with this ISBN already exists.") from exc
        raise

    return get_book(conn, int(cursor.lastrowid))


def get_book(conn: sqlite3.Connection, book_id: int) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    book = row_to_dict(row)
    if book is None:
        raise NotFoundError(f"Book {book_id} not found.")
    return book


def list_books(conn: sqlite3.Connection, search: str = "") -> list[dict[str, Any]]:
    query = "SELECT * FROM books"
    params: list[Any] = []
    if search.strip():
        term = f"%{search.strip()}%"
        query += " WHERE title LIKE ? OR author LIKE ? OR isbn LIKE ?"
        params.extend([term, term, term])
    query += " ORDER BY title COLLATE NOCASE, author COLLATE NOCASE"
    rows = conn.execute(query, params).fetchall()
    return rows_to_dicts(rows)


def update_book(
    conn: sqlite3.Connection,
    book_id: int,
    *,
    title: str,
    author: str,
    isbn: str,
    price: float,
    notes: str,
) -> dict[str, Any]:
    title = _require_non_empty(title, "Title")
    author = _require_non_empty(author, "Author")
    isbn = _require_non_empty(isbn, "ISBN")
    if price < 0:
        raise ValidationError("Price cannot be negative.")

    get_book(conn, book_id)
    now = utc_now()
    try:
        with transaction(conn):
            conn.execute(
                """
                UPDATE books
                SET title = ?, author = ?, isbn = ?, price = ?, notes = ?, updated_at = ?
                WHERE id = ?
                """,
                (title, author, isbn, price, notes.strip(), now, book_id),
            )
    except sqlite3.IntegrityError as exc:
        if "isbn" in str(exc).lower():
            raise ValidationError("A book with this ISBN already exists.") from exc
        raise

    return get_book(conn, book_id)


def adjust_stock(conn: sqlite3.Connection, book_id: int, delta: int) -> dict[str, Any]:
    book = get_book(conn, book_id)
    new_stock = book["stock"] + delta
    if new_stock < 0:
        raise ValidationError("Stock cannot go below zero.")

    now = utc_now()
    with transaction(conn):
        conn.execute(
            "UPDATE books SET stock = ?, updated_at = ? WHERE id = ?",
            (new_stock, now, book_id),
        )
    return get_book(conn, book_id)


def record_sale(conn: sqlite3.Connection, book_id: int, quantity: int) -> dict[str, Any]:
    if quantity <= 0:
        raise ValidationError("Quantity must be greater than zero.")

    book = get_book(conn, book_id)
    if book["stock"] < quantity:
        raise ValidationError(
            f"Insufficient stock. Available: {book['stock']}, requested: {quantity}."
        )

    sold_at = utc_now()
    with transaction(conn):
        cursor = conn.execute(
            """
            INSERT INTO sales (book_id, quantity, unit_price, sold_at)
            VALUES (?, ?, ?, ?)
            """,
            (book_id, quantity, book["price"], sold_at),
        )
        conn.execute(
            "UPDATE books SET stock = stock - ?, updated_at = ? WHERE id = ?",
            (quantity, sold_at, book_id),
        )

    sale = conn.execute("SELECT * FROM sales WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return row_to_dict(sale)


def list_sales(conn: sqlite3.Connection, search: str = "") -> list[dict[str, Any]]:
    query = """
        SELECT s.*, b.title AS book_title, b.author AS book_author, b.isbn AS book_isbn
        FROM sales s
        JOIN books b ON b.id = s.book_id
    """
    params: list[Any] = []
    if search.strip():
        term = f"%{search.strip()}%"
        query += """
            WHERE b.title LIKE ? OR b.author LIKE ? OR b.isbn LIKE ?
        """
        params.extend([term, term, term])
    query += " ORDER BY s.sold_at DESC, s.id DESC"
    rows = conn.execute(query, params).fetchall()
    return rows_to_dicts(rows)


def create_purchase_order(
    conn: sqlite3.Connection, book_id: int, quantity: int
) -> dict[str, Any]:
    if quantity <= 0:
        raise ValidationError("Quantity must be greater than zero.")
    get_book(conn, book_id)

    ordered_at = utc_now()
    with transaction(conn):
        cursor = conn.execute(
            """
            INSERT INTO purchase_orders (book_id, quantity, ordered_at, received, received_at)
            VALUES (?, ?, ?, 0, NULL)
            """,
            (book_id, quantity, ordered_at),
        )

    return get_purchase_order(conn, int(cursor.lastrowid))


def get_purchase_order(conn: sqlite3.Connection, po_id: int) -> dict[str, Any]:
    row = conn.execute(
        "SELECT * FROM purchase_orders WHERE id = ?", (po_id,)
    ).fetchone()
    po = row_to_dict(row)
    if po is None:
        raise NotFoundError(f"Purchase order {po_id} not found.")
    return po


def list_purchase_orders(
    conn: sqlite3.Connection, search: str = "", received: int | None = None
) -> list[dict[str, Any]]:
    query = """
        SELECT po.*, b.title AS book_title, b.author AS book_author, b.isbn AS book_isbn
        FROM purchase_orders po
        JOIN books b ON b.id = po.book_id
        WHERE 1 = 1
    """
    params: list[Any] = []
    if received is not None:
        query += " AND po.received = ?"
        params.append(received)
    if search.strip():
        term = f"%{search.strip()}%"
        query += " AND (b.title LIKE ? OR b.author LIKE ? OR b.isbn LIKE ?)"
        params.extend([term, term, term])
    query += " ORDER BY po.ordered_at DESC, po.id DESC"
    rows = conn.execute(query, params).fetchall()
    return rows_to_dicts(rows)


def mark_po_received(conn: sqlite3.Connection, po_id: int) -> dict[str, Any]:
    po = get_purchase_order(conn, po_id)
    if po["received"] == 1:
        raise ValidationError("Purchase order has already been marked as received.")

    received_at = utc_now()
    with transaction(conn):
        updated = conn.execute(
            """
            UPDATE purchase_orders
            SET received = 1, received_at = ?
            WHERE id = ? AND received = 0
            """,
            (received_at, po_id),
        )
        if updated.rowcount == 0:
            raise ValidationError("Purchase order has already been marked as received.")
        conn.execute(
            "UPDATE books SET stock = stock + ?, updated_at = ? WHERE id = ?",
            (po["quantity"], received_at, po["book_id"]),
        )

    return get_purchase_order(conn, po_id)


def create_customer_order(
    conn: sqlite3.Connection,
    *,
    customer_name: str,
    book_title: str,
    quantity: int,
    book_id: int | None = None,
    notes: str = "",
) -> dict[str, Any]:
    customer_name = _require_non_empty(customer_name, "Customer name")
    book_title = _require_non_empty(book_title, "Book title")
    if quantity <= 0:
        raise ValidationError("Quantity must be greater than zero.")
    if book_id is not None:
        get_book(conn, book_id)

    now = utc_now()
    with transaction(conn):
        cursor = conn.execute(
            """
            INSERT INTO customer_orders
                (customer_name, book_title, book_id, quantity, status, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'pending', ?, ?, ?)
            """,
            (customer_name, book_title, book_id, quantity, notes.strip(), now, now),
        )

    return get_customer_order(conn, int(cursor.lastrowid))


def get_customer_order(conn: sqlite3.Connection, order_id: int) -> dict[str, Any]:
    row = conn.execute(
        "SELECT * FROM customer_orders WHERE id = ?", (order_id,)
    ).fetchone()
    order = row_to_dict(row)
    if order is None:
        raise NotFoundError(f"Customer order {order_id} not found.")
    return order


def list_customer_orders(
    conn: sqlite3.Connection, search: str = "", status: str | None = None
) -> list[dict[str, Any]]:
    query = """
        SELECT co.*, b.title AS linked_book_title
        FROM customer_orders co
        LEFT JOIN books b ON b.id = co.book_id
        WHERE 1 = 1
    """
    params: list[Any] = []
    if status:
        query += " AND co.status = ?"
        params.append(status)
    if search.strip():
        term = f"%{search.strip()}%"
        query += " AND (co.customer_name LIKE ? OR co.book_title LIKE ? OR co.notes LIKE ?)"
        params.extend([term, term, term])
    query += " ORDER BY co.created_at DESC, co.id DESC"
    rows = conn.execute(query, params).fetchall()
    return rows_to_dicts(rows)


def update_customer_order_status(
    conn: sqlite3.Connection, order_id: int, status: str
) -> dict[str, Any]:
    if status not in CUSTOMER_ORDER_STATUSES:
        raise ValidationError(
            f"Invalid status. Allowed values: {', '.join(CUSTOMER_ORDER_STATUSES)}."
        )

    get_customer_order(conn, order_id)
    now = utc_now()
    with transaction(conn):
        conn.execute(
            "UPDATE customer_orders SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, order_id),
        )
    return get_customer_order(conn, order_id)
