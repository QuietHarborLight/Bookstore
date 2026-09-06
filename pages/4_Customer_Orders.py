"""Customer special order tracking page."""

import streamlit as st

import db

st.set_page_config(page_title="Customer Orders", page_icon="🧾", layout="wide")
db.init_db()

st.title("Customer Orders")
st.caption("Capture special-order requests and track status through fulfillment.")

with db.connect() as conn:
    books = db.list_books(conn)

with st.form("create_customer_order_form", clear_on_submit=True):
    st.subheader("New customer order")
    customer_name = st.text_input("Customer name")
    book_title = st.text_input("Requested book title")

    link_options = ["None (title only)"] + [
        f"{book['title']} — {book['author']}" for book in books
    ]
    link_choice = st.selectbox("Link to inventory book (optional)", options=link_options)
    quantity = st.number_input("Quantity", min_value=1, step=1, value=1)
    notes = st.text_area("Notes", placeholder="Edition, condition, contact details...")

    create_order = st.form_submit_button("Create customer order", type="primary")
    if create_order:
        book_id = None
        if link_choice != "None (title only)":
            index = link_options.index(link_choice) - 1
            book_id = books[index]["id"]
        try:
            with db.connect() as conn:
                order = db.create_customer_order(
                    conn,
                    customer_name=customer_name,
                    book_title=book_title,
                    quantity=int(quantity),
                    book_id=book_id,
                    notes=notes,
                )
            st.success(f"Customer order #{order['id']} created.")
            st.rerun()
        except db.BookstoreError as exc:
            st.error(str(exc))

search = st.text_input(
    "Search customer orders",
    placeholder="Customer name, book title, or notes",
)
status_filter = st.selectbox(
    "Status filter",
    options=["All"] + list(db.CUSTOMER_ORDER_STATUSES),
    index=0,
)

with db.connect() as conn:
    orders = db.list_customer_orders(
        conn,
        search=search,
        status=None if status_filter == "All" else status_filter,
    )

st.subheader("Customer orders")
if not orders:
    st.info("No customer orders yet.")
else:
    st.dataframe(
        [
            {
                "ID": order["id"],
                "Customer": order["customer_name"],
                "Book": order["book_title"],
                "Linked book": order.get("linked_book_title") or "",
                "Qty": order["quantity"],
                "Status": order["status"],
                "Notes": order["notes"],
                "Created": order["created_at"],
                "Updated": order["updated_at"],
            }
            for order in orders
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Update status")
    order_labels = {
        order["id"]: (
            f"#{order['id']} — {order['customer_name']} / {order['book_title']} "
            f"({order['status']})"
        )
        for order in orders
    }
    order_id = st.selectbox(
        "Select order",
        options=list(order_labels.keys()),
        format_func=lambda value: order_labels[value],
    )
    current = next(order for order in orders if order["id"] == order_id)
    new_status = st.selectbox(
        "New status",
        options=list(db.CUSTOMER_ORDER_STATUSES),
        index=list(db.CUSTOMER_ORDER_STATUSES).index(current["status"]),
    )
    if st.button("Update status", type="primary"):
        try:
            with db.connect() as conn:
                updated = db.update_customer_order_status(conn, order_id, new_status)
            st.success(f"Order status updated to {updated['status']}.")
            st.rerun()
        except db.BookstoreError as exc:
            st.error(str(exc))
