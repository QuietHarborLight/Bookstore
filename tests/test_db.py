import sqlite3

import pytest

import db


def test_init_creates_tables(conn: sqlite3.Connection) -> None:
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    assert tables >= {"books", "sales", "purchase_orders", "customer_orders"}


def _create_sample_book(conn: sqlite3.Connection, **overrides) -> dict:
    payload = {
        "title": "The Hobbit",
        "author": "J.R.R. Tolkien",
        "isbn": "978-0-261-10221-7",
        "price": 12.99,
        "stock": 5,
        "notes": "First edition",
    }
    payload.update(overrides)
    return db.create_book(conn, **payload)


def test_create_get_update_book(conn: sqlite3.Connection) -> None:
    book = _create_sample_book(conn)
    assert book["stock"] == 5

    fetched = db.get_book(conn, book["id"])
    assert fetched["title"] == "The Hobbit"

    updated = db.update_book(
        conn,
        book["id"],
        title="The Hobbit",
        author="J.R.R. Tolkien",
        isbn="978-0-261-10221-7",
        price=14.99,
        notes="Updated note",
    )
    assert updated["price"] == 14.99
    assert updated["notes"] == "Updated note"


def test_unique_isbn_violation(conn: sqlite3.Connection) -> None:
    _create_sample_book(conn)
    with pytest.raises(db.ValidationError, match="ISBN"):
        _create_sample_book(conn, isbn="978-0-261-10221-7")


def test_adjust_stock(conn: sqlite3.Connection) -> None:
    book = _create_sample_book(conn, stock=3)
    increased = db.adjust_stock(conn, book["id"], 2)
    assert increased["stock"] == 5

    decreased = db.adjust_stock(conn, book["id"], -2)
    assert decreased["stock"] == 3

    with pytest.raises(db.ValidationError, match="below zero"):
        db.adjust_stock(conn, book["id"], -10)


def test_list_books_filter(conn: sqlite3.Connection) -> None:
    _create_sample_book(conn, title="Dune", author="Frank Herbert", isbn="978-0441172719")
    _create_sample_book(conn, title="Neuromancer", author="William Gibson", isbn="978-0441569595")

    results = db.list_books(conn, search="dune")
    assert len(results) == 1
    assert results[0]["title"] == "Dune"


def test_record_sale_decreases_stock(conn: sqlite3.Connection) -> None:
    book = _create_sample_book(conn, stock=5)
    sale = db.record_sale(conn, book["id"], 2)

    assert sale["quantity"] == 2
    assert sale["unit_price"] == book["price"]
    assert db.get_book(conn, book["id"])["stock"] == 3


def test_record_sale_insufficient_stock(conn: sqlite3.Connection) -> None:
    book = _create_sample_book(conn, stock=3)
    with pytest.raises(db.ValidationError, match="Insufficient stock"):
        db.record_sale(conn, book["id"], 10)
    assert db.get_book(conn, book["id"])["stock"] == 3


def test_list_sales_filter(conn: sqlite3.Connection) -> None:
    book = _create_sample_book(conn)
    db.record_sale(conn, book["id"], 1)
    sales = db.list_sales(conn, search="hobbit")
    assert len(sales) == 1
    assert sales[0]["book_title"] == "The Hobbit"


def test_purchase_order_receive_increases_stock(conn: sqlite3.Connection) -> None:
    book = _create_sample_book(conn, stock=2)
    po = db.create_purchase_order(conn, book["id"], 4)
    assert db.get_book(conn, book["id"])["stock"] == 2

    received = db.mark_po_received(conn, po["id"])
    assert received["received"] == 1
    assert db.get_book(conn, book["id"])["stock"] == 6


def test_purchase_order_double_receive_blocked(conn: sqlite3.Connection) -> None:
    book = _create_sample_book(conn, stock=1)
    po = db.create_purchase_order(conn, book["id"], 2)
    db.mark_po_received(conn, po["id"])

    with pytest.raises(db.ValidationError, match="already been marked"):
        db.mark_po_received(conn, po["id"])
    assert db.get_book(conn, book["id"])["stock"] == 3


def test_customer_order_with_and_without_book(conn: sqlite3.Connection) -> None:
    book = _create_sample_book(conn)
    linked = db.create_customer_order(
        conn,
        customer_name="Alice",
        book_title=book["title"],
        quantity=1,
        book_id=book["id"],
        notes="Signed copy",
    )
    assert linked["status"] == "pending"
    assert linked["book_id"] == book["id"]

    title_only = db.create_customer_order(
        conn,
        customer_name="Bob",
        book_title="Rare Manuscript",
        quantity=1,
    )
    assert title_only["book_id"] is None


def test_customer_order_status_updates(conn: sqlite3.Connection) -> None:
    order = db.create_customer_order(
        conn,
        customer_name="Carol",
        book_title="Out of Print Title",
        quantity=2,
    )
    for status in ("ordered", "received", "fulfilled"):
        order = db.update_customer_order_status(conn, order["id"], status)
        assert order["status"] == status


def test_invalid_customer_order_status(conn: sqlite3.Connection) -> None:
    order = db.create_customer_order(
        conn,
        customer_name="Dan",
        book_title="Some Book",
        quantity=1,
    )
    with pytest.raises(db.ValidationError, match="Invalid status"):
        db.update_customer_order_status(conn, order["id"], "shipped")
