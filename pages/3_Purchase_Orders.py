"""Purchase order management page."""

import streamlit as st

import db

st.set_page_config(page_title="Purchase Orders", page_icon="📦", layout="wide")
db.init_db()

st.title("Purchase Orders")
st.caption("Order stock from manufacturers and mark orders as received.")

with db.connect() as conn:
    books = db.list_books(conn)

if not books:
    st.warning("Add books to inventory before creating purchase orders.")
else:
    with st.form("create_po_form"):
        st.subheader("Create purchase order")
        book_labels = {
            book["id"]: f"{book['title']} — {book['author']} (stock: {book['stock']})"
            for book in books
        }
        book_id = st.selectbox(
            "Book",
            options=list(book_labels.keys()),
            format_func=lambda value: book_labels[value],
        )
        quantity = st.number_input("Quantity to order", min_value=1, step=1, value=1)
        create_po = st.form_submit_button("Create purchase order", type="primary")
        if create_po:
            try:
                with db.connect() as conn:
                    po = db.create_purchase_order(conn, book_id, int(quantity))
                st.success(f"Purchase order #{po['id']} created.")
                st.rerun()
            except db.BookstoreError as exc:
                st.error(str(exc))

search = st.text_input("Search purchase orders", placeholder="Title, author, or ISBN")
status_filter = st.selectbox(
    "Status filter",
    options=["All", "Open", "Received"],
    index=0,
)

received_filter = None
if status_filter == "Open":
    received_filter = 0
elif status_filter == "Received":
    received_filter = 1

with db.connect() as conn:
    orders = db.list_purchase_orders(conn, search=search, received=received_filter)

st.subheader("Purchase orders")
if not orders:
    st.info("No purchase orders yet.")
else:
    st.dataframe(
        [
            {
                "ID": order["id"],
                "Book": order["book_title"],
                "Author": order["book_author"],
                "ISBN": order["book_isbn"],
                "Qty": order["quantity"],
                "Ordered at": order["ordered_at"],
                "Status": "Received" if order["received"] else "Open",
                "Received at": order["received_at"] or "",
            }
            for order in orders
        ],
        use_container_width=True,
        hide_index=True,
    )

    open_orders = [order for order in orders if order["received"] == 0]
    if open_orders:
        st.subheader("Mark received")
        open_labels = {
            order["id"]: (
                f"PO #{order['id']} — {order['book_title']} "
                f"(qty {order['quantity']})"
            )
            for order in open_orders
        }
        po_id = st.selectbox(
            "Open purchase order",
            options=list(open_labels.keys()),
            format_func=lambda value: open_labels[value],
        )
        if st.button("Mark as received", type="primary"):
            try:
                with db.connect() as conn:
                    db.mark_po_received(conn, po_id)
                st.success("Purchase order marked as received. Stock updated.")
                st.rerun()
            except db.BookstoreError as exc:
                st.error(str(exc))
