"""Inventory management page."""

import streamlit as st

import db

st.set_page_config(page_title="Inventory", page_icon="📖", layout="wide")
db.init_db()

st.title("Inventory")
st.caption("Add, edit, and adjust stock for books in the catalog.")

search = st.text_input("Search inventory", placeholder="Title, author, or ISBN")

with st.form("add_book_form", clear_on_submit=True):
    st.subheader("Add book")
    col1, col2 = st.columns(2)
    with col1:
        title = st.text_input("Title", key="add_title")
        author = st.text_input("Author", key="add_author")
        isbn = st.text_input("ISBN", key="add_isbn")
    with col2:
        price = st.number_input("Price", min_value=0.0, step=0.01, format="%.2f")
        stock = st.number_input("Initial stock", min_value=0, step=1, value=0)
        notes = st.text_area("Notes", placeholder="Edition, condition, rarity...")
    submitted = st.form_submit_button("Add book", type="primary")
    if submitted:
        try:
            with db.connect() as conn:
                db.create_book(
                    conn,
                    title=title,
                    author=author,
                    isbn=isbn,
                    price=price,
                    stock=int(stock),
                    notes=notes,
                )
            st.success("Book added.")
            st.rerun()
        except db.BookstoreError as exc:
            st.error(str(exc))

with db.connect() as conn:
    books = db.list_books(conn, search=search)

if not books:
    st.info("No books found. Add your first book above.")
else:
    st.subheader("Catalog")
    st.dataframe(
        [
            {
                "ID": book["id"],
                "Title": book["title"],
                "Author": book["author"],
                "ISBN": book["isbn"],
                "Price": f"${book['price']:.2f}",
                "Stock": book["stock"],
                "Notes": book["notes"],
            }
            for book in books
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Edit book")
    book_labels = {
        book["id"]: f"{book['title']} — {book['author']} (stock: {book['stock']})"
        for book in books
    }
    selected_id = st.selectbox(
        "Select book",
        options=list(book_labels.keys()),
        format_func=lambda book_id: book_labels[book_id],
    )
    selected = next(book for book in books if book["id"] == selected_id)

    with st.form("edit_book_form"):
        col1, col2 = st.columns(2)
        with col1:
            edit_title = st.text_input("Title", value=selected["title"])
            edit_author = st.text_input("Author", value=selected["author"])
            edit_isbn = st.text_input("ISBN", value=selected["isbn"])
        with col2:
            edit_price = st.number_input(
                "Price",
                min_value=0.0,
                step=0.01,
                format="%.2f",
                value=float(selected["price"]),
            )
            edit_notes = st.text_area("Notes", value=selected["notes"])
        save_changes = st.form_submit_button("Save changes")
        if save_changes:
            try:
                with db.connect() as conn:
                    db.update_book(
                        conn,
                        selected_id,
                        title=edit_title,
                        author=edit_author,
                        isbn=edit_isbn,
                        price=edit_price,
                        notes=edit_notes,
                    )
                st.success("Book updated.")
                st.rerun()
            except db.BookstoreError as exc:
                st.error(str(exc))

    st.subheader("Adjust stock")
    with st.form("adjust_stock_form"):
        delta = st.number_input(
            "Change amount (use negative to decrease)",
            value=0,
            step=1,
            help="Example: +3 to add copies, -1 to remove one copy.",
        )
        adjust = st.form_submit_button("Apply stock change")
        if adjust:
            if delta == 0:
                st.warning("Enter a non-zero change amount.")
            else:
                try:
                    with db.connect() as conn:
                        updated = db.adjust_stock(conn, selected_id, int(delta))
                    st.success(f"Stock updated to {updated['stock']}.")
                    st.rerun()
                except db.BookstoreError as exc:
                    st.error(str(exc))
