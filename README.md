# Bookstore Management MVP

A local bookstore management app for inventory, sales, manufacturer purchase orders, and customer special orders. Built with Python, Streamlit, and SQLite.

## Requirements

- Python 3.11+
- No external database server
- Internet not required for normal use

## Setup

From the project root (the directory containing `app.py` and `requirements.txt`):

```bash
python -m venv .venv
```

**Windows (PowerShell / cmd):**

```bash
.venv\Scripts\activate
pip install -r requirements.txt
```

**Windows (Git Bash):**

```bash
cd /path/to/project
source .venv/Scripts/activate
pip install -r requirements.txt
```

**macOS / Linux:**

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the app

Activate the virtual environment first (see Setup above), then:

```bash
streamlit run app.py
```

**Git Bash on Windows (full example):**

```bash
cd /path/to/project
source .venv/Scripts/activate
streamlit run app.py
```

Your browser opens to the home page (usually `http://localhost:8501`). Press `Ctrl+C` in the terminal to stop the app. Use the sidebar to navigate:

- **Inventory** — add, edit, and adjust stock
- **Sales** — record sales and view history
- **Purchase Orders** — create POs and mark them received
- **Customer Orders** — track special-order requests and status

On first run, the app creates `bookstore.db` in the project root.

## Run tests

Activate the virtual environment, then:

```bash
python -m pytest
```

**Git Bash on Windows:**

```bash
source .venv/Scripts/activate
python -m pytest
```

Tests cover database rules: stock updates on sales and purchase-order receipt, validation for insufficient stock, duplicate ISBNs, and customer-order status changes.

## Backup

All data lives in a single SQLite file:

```text
bookstore.db
```

To back up, stop the app and copy that file to a safe location. To restore, replace the file and restart the app.

## Security note

This MVP has no authentication. It is intended for trusted local use on a single machine by the bookstore owner or staff.

## Daily workflow smoke test

1. Add or review a book in Inventory
2. Record a sale in Sales
3. Create a purchase order and mark it received
4. Log a customer special order and advance its status

This should complete in a few minutes once you are familiar with the UI.
