import auth


def _reset(monkeypatch):
    monkeypatch.delenv(auth.PIN_ENV_VAR, raising=False)
    auth.reset_env_cache_for_tests()


def test_configured_pin_missing(monkeypatch):
    _reset(monkeypatch)
    assert auth.configured_pin() is None


def test_configured_pin_blank(monkeypatch):
    _reset(monkeypatch)
    monkeypatch.setenv(auth.PIN_ENV_VAR, "   ")
    assert auth.configured_pin() is None


def test_configured_pin_strips_whitespace(monkeypatch):
    _reset(monkeypatch)
    monkeypatch.setenv(auth.PIN_ENV_VAR, "  demo  ")
    assert auth.configured_pin() == "demo"


def test_configured_pin_from_env_file(monkeypatch, tmp_path):
    _reset(monkeypatch)
    env_file = tmp_path / ".env"
    env_file.write_text("BOOKSTORE_PIN=file-pin\n", encoding="utf-8")
    auth.load_env_file(env_file)
    assert auth.configured_pin() == "file-pin"


def test_env_var_overrides_env_file(monkeypatch, tmp_path):
    _reset(monkeypatch)
    monkeypatch.setenv(auth.PIN_ENV_VAR, "shell-pin")
    env_file = tmp_path / ".env"
    env_file.write_text("BOOKSTORE_PIN=file-pin\n", encoding="utf-8")
    auth.load_env_file(env_file)
    assert auth.configured_pin() == "shell-pin"


def test_env_file_ignores_comments_and_blank_lines(monkeypatch, tmp_path):
    _reset(monkeypatch)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# comment\n\nBOOKSTORE_PIN=quoted\n",
        encoding="utf-8",
    )
    auth.load_env_file(env_file)
    assert auth.configured_pin() == "quoted"


def test_pins_match_success():
    assert auth.pins_match("demo", "demo") is True


def test_pins_match_mismatch():
    assert auth.pins_match("wrong", "demo") is False


def test_pins_match_empty_entered():
    assert auth.pins_match("", "demo") is False
