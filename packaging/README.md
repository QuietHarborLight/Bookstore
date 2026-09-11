# Bookstore Management MVP

Local bookstore management for inventory, sales, purchase orders, and customer special orders.

## Run

1. Keep this entire folder together. Do not move only `Bookstore.exe` — the `_internal` directory is required.
2. Double-click `Bookstore.exe`, or run it from a terminal.
3. A console window opens and must stay open while you use the app. Closing it stops the server and your browser will show a connection error.
4. Your browser opens to `http://localhost:8501` once the server is ready. Use the sidebar to navigate.
5. Stop the app with `Ctrl+C` in the console window.

## Data

On first run, the app creates `bookstore.db` in this folder (next to `Bookstore.exe`).

To back up your data, stop the app and copy `bookstore.db` to a safe location. To restore, replace the file and restart.

## Notes

- No login. Intended for trusted local use on one machine.
- Windows Defender or SmartScreen may warn about unsigned PyInstaller binaries. You can allow the app if you trust this source.
