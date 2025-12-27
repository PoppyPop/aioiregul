import pytest

from aioiregul.v1 import ConnectionOptions


def test_connection_options_loads_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("IREGUL_USERNAME", "env_user")
    monkeypatch.setenv("IREGUL_PASSWORD", "env_pass")
    monkeypatch.setenv("IREGUL_BASE_URL", "https://example.com/modules/")

    opts = ConnectionOptions()

    assert opts.username == "env_user"
    assert opts.password == "env_pass"
    assert opts.iregul_base_url == "https://example.com/modules/"


def test_connection_options_missing_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("IREGUL_USERNAME", raising=False)
    monkeypatch.delenv("IREGUL_PASSWORD", raising=False)

    with pytest.raises(ValueError):
        ConnectionOptions()
