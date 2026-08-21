import pytest

from shared.db import get_connection


def test_get_connection_raises_when_database_url_unset(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(RuntimeError):
        get_connection()
