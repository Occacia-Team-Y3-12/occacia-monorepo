# ruff: noqa: S101

from app.scripts import seed as seed_module


class _FakeInspector:
    def __init__(self, tables: set[str]):
        self._tables = tables

    def has_table(self, table_name: str) -> bool:
        return table_name in self._tables


class _FakeQuery:
    def __init__(self, session):
        self._session = session

    def first(self):
        self._session.query_first_called = True
        return None


class _FakeSession:
    def __init__(self):
        self.bind = object()
        self.closed = False
        self.query_called = False
        self.query_first_called = False

    def close(self):
        self.closed = True

    def query(self, _model):
        self.query_called = True
        return _FakeQuery(self)


def test_seed_data_skips_when_required_tables_missing(monkeypatch):
    session = _FakeSession()

    monkeypatch.setattr(seed_module, "SessionLocal", lambda: session)
    monkeypatch.setattr(
        seed_module,
        "inspect",
        lambda _bind: _FakeInspector(set()),
    )

    result = seed_module.seed_data()

    assert result is False
    assert session.closed is True
    assert session.query_called is False
