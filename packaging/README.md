# Bookstore Management MVP

Local bookstore management for inventory, sales, purchase orders, and customer special orders.

## Staff PIN

The app requires a shared staff PIN before you can use it. Set it in a local `.env` file in **this folder** (next to `Bookstore.exe`):

1. Copy `.env.example` to `.env` in this folder.
2. Edit `.env` and set your PIN:
   ```text
   BOOKSTORE_PIN=your-pin
   ```
   Replace `your-pin` with a real value. The example file uses `demo` only as a placeholder.
3. Restart `Bookstore.exe` after creating or changing `.env`.

On launch, your browser opens to `http://localhost:8501`. Enter the same PIN on the lock screen to unlock the app.

If `.env` is missing or `BOOKSTORE_PIN` is blank, the console shows an error and the app exits. Keep `.env` private and do not share it.

## Run

1. Complete the **Staff PIN** steps above if you have not already.
2. Keep this entire folder together. Do not move only `Bookstore.exe` — the `_internal` directory is required.
3. Double-click `Bookstore.exe`, or run it from a terminal.
4. A console window opens and must stay open while you use the app. Closing it stops the server and your browser will show a connection error.
5. Your browser opens to `http://localhost:8501` once the server is ready. Enter the PIN on the lock screen, then use the sidebar to navigate.
6. Stop the app with `Ctrl+C` in the console window.

## Data

On first run, the app creates `bookstore.db` in this folder (next to `Bookstore.exe`).

To back up your data, stop the app and copy `bookstore.db` to a safe location. To restore, replace the file and restart.

Rebuilding the app from source preserves an existing `bookstore.db` and `.env` in this folder. Do not overwrite your real `.env` with `.env.example`.

## Notes

- Shared PIN only (`BOOKSTORE_PIN` in `.env`), not individual accounts. Intended for trusted local use on one machine.
- Windows Defender or SmartScreen may warn about unsigned PyInstaller binaries. You can allow the app if you trust this source.
