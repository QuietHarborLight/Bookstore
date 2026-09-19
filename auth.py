"""Shared PIN gate for the Bookstore MVP (local .env file)."""

from __future__ import annotations

import hmac
import os
import sys
from pathlib import Path

import streamlit as st

PIN_ENV_VAR = "BOOKSTORE_PIN"
ENV_FILE_NAME = ".env"
SESSION_UNLOCKED_KEY = "pin_ok"

_env_loaded = False


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def env_file_path() -> Path:
    return app_dir() / ENV_FILE_NAME


def _parse_env_value(raw: str) -> str:
    value = raw.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def load_env_file(path: Path | None = None) -> None:
    """Load KEY=VALUE pairs from a .env file without overriding existing env vars."""
    global _env_loaded
    env_path = path or env_file_path()
    if not env_path.is_file():
        _env_loaded = True
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("export "):
            stripped = stripped[len("export ") :].strip()
        key, sep, value = stripped.partition("=")
        if not sep:
            continue
        key = key.strip()
        if not key or key in os.environ:
            continue
        os.environ[key] = _parse_env_value(value)

    _env_loaded = True


def _ensure_env_loaded() -> None:
    if not _env_loaded:
        load_env_file()


def configured_pin() -> str | None:
    """Return the configured PIN from .env / environment, or None if unset/blank."""
    _ensure_env_loaded()
    value = os.environ.get(PIN_ENV_VAR)
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None


def pins_match(entered: str, expected: str) -> bool:
    """Compare PINs without leaking length via early return."""
    return hmac.compare_digest(entered.encode("utf-8"), expected.encode("utf-8"))


def _show_pin_not_configured() -> None:
    st.error("Staff PIN is not configured.")
    st.markdown(
        f"""
        Create a `{ENV_FILE_NAME}` file in the app folder with your shared PIN:

        ```text
        {PIN_ENV_VAR}=your-pin
        ```

        For a source checkout, copy [`.env.example`](.env.example) to `{ENV_FILE_NAME}`
        and edit the value. Restart the app after changing the file.

        An existing shell environment variable named `{PIN_ENV_VAR}` also works and
        takes precedence over `{ENV_FILE_NAME}`.
        """
    )
    st.stop()


def _show_lock_screen(expected_pin: str) -> None:
    st.title("Bookstore — Staff access")
    st.caption("Enter the shared PIN to use the app.")

    with st.form("pin_unlock_form"):
        entered = st.text_input("PIN", type="password", autocomplete="off")
        submitted = st.form_submit_button("Unlock", type="primary")

    if submitted:
        if pins_match(entered, expected_pin):
            st.session_state[SESSION_UNLOCKED_KEY] = True
            st.rerun()
        st.error("Incorrect PIN. Try again.")


def _show_logout_button() -> None:
    with st.sidebar:
        if st.button("Lock app", use_container_width=True):
            st.session_state.pop(SESSION_UNLOCKED_KEY, None)
            st.rerun()


def require_unlock() -> None:
    """Block page rendering until the shared PIN is entered."""
    expected = configured_pin()
    if expected is None:
        _show_pin_not_configured()

    if st.session_state.get(SESSION_UNLOCKED_KEY):
        _show_logout_button()
        return

    _show_lock_screen(expected)
    st.stop()


def reset_env_cache_for_tests() -> None:
    """Clear the one-time .env load flag for unit tests."""
    global _env_loaded
    _env_loaded = False
