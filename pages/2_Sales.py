"""Sales recording and history page."""

import streamlit as st

import db

st.set_page_config(page_title="Sales", page_icon="💵", layout="wide")
db.init_db()

st.title("Sales")
st.caption("Record sales and review history. Stock decreases automatically.")

with db.connect() as conn:
    books = db.list_books(conn)

if not books:
    st.warning("Add books to inventory before recording sales.")
else:
    with st.form("record_sale_form"):
        st.subheader("Record sale")
        book_labels = {
            book["id"]: f"{book['title']} — stock: {book['stock']} @ ${book['price']:.2f}"
            for book in books
        }
        book_id = st.selectbox(
            "Book",
            options=list(book_labels.keys()),
            format_func=lambda value: book_labels[value],
        )
        quantity = st.number_input("Quantity", min_value=1, step=1, value=1)
        submit_sale = st.form_submit_button("Record sale", type="primary")
        if submit_sale:
            try:
                with db.connect() as conn:
                    sale = db.record_sale(conn, book_id, int(quantity))
                st.success(
                    f"Recorded sale of {sale['quantity']} at ${sale['unit_price']:.2f} each."
                )
                st.rerun()
            except db.BookstoreError as exc:
                st.error(str(exc))

search = st.text_input("Search sales history", placeholder="Title, author, or ISBN")

with db.connect() as conn:
    sales = db.list_sales(conn, search=search)

st.subheader("Sales history")
if not sales:
    st.info("No sales recorded yet.")
else:
    st.dataframe(
        [
            {
                "ID": sale["id"],
                "Book": sale["book_title"],
                "Author": sale["book_author"],
                "ISBN": sale["book_isbn"],
                "Qty": sale["quantity"],
                "Unit price": f"${sale['unit_price']:.2f}",
                "Total": f"${sale['quantity'] * sale['unit_price']:.2f}",
                "Sold at": sale["sold_at"],
            }
            for sale in sales
        ],
        use_container_width=True,
        hide_index=True,
    )
