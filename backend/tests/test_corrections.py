from datetime import date, timedelta
from io import BytesIO

import pytest

from app.config import get_settings
from tests.test_api import _row, _upload_file


def upload(client, rows, day=None, filename="loans.xlsx"):
    return client.post(
        "/api/uploads",
        files={"file": (filename, _upload_file(rows))},
        data={"upload_date": day.isoformat()} if day else {},
    )


def test_historical_summary_and_comparison(client):
    first = date.today() - timedelta(days=14)
    second = first + timedelta(days=7)
    assert upload(client, [_row("A", 10), _row("B", 20)], first).status_code == 200
    assert upload(client, [_row("A", 50)], second).status_code == 200
    assert upload(client, [_row("A", 5), _row("C", 15)]).status_code == 200
    query = f"?upload_date={second.isoformat()}"
    summary = client.get("/api/dashboard/summary" + query).json()
    assert summary["total_loans"] == 1
    assert summary["previous_upload_date"] == first.isoformat()
    assert client.get("/api/dashboard/trend" + query).json()[0]["direction"] == "worsening"
    assert client.get("/api/dashboard/disappeared" + query).json() == ["B"]
    assert client.get(f"/api/dashboard/trend?upload_date={first}").json() == []


def test_invalid_replacement_preserves_previous_batch(client):
    assert upload(client, [_row("A", 10)]).status_code == 200
    response = upload(client, [_row("B", 20), _row("B", 30)])
    assert response.status_code == 422
    assert "duplicate Loan ID" in response.json()["detail"]
    assert client.get("/api/dashboard/by-days").json()[0]["loan_id"] == "A"


@pytest.mark.parametrize("days", [-1, 1.5, "invalid", "inf"])
def test_invalid_days_rejected(client, days):
    assert upload(client, [_row("A", days)]).status_code == 422


def test_corrupt_and_legacy_workbooks(client):
    response = client.post("/api/uploads", files={"file": ("broken.xlsx", BytesIO(b"broken"))})
    assert response.status_code == 422
    assert upload(client, [_row("A", 10)], filename="old.xls").status_code == 400


def test_upload_size_limit(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "max_upload_bytes", 10)
    assert upload(client, [_row("A", 10)]).status_code == 413


def test_numeric_ids_stay_consistent_with_blank_rows(client):
    result = upload(client, [_row(123, 10), [None] * 34])
    assert result.status_code == 200
    assert result.json()["new_loans"] == 1
    assert client.get("/api/dashboard/by-days").json()[0]["loan_id"] == "123"


def test_backup_can_be_restored_and_refuses_overwrite(tmp_path, monkeypatch):
    import sqlite3
    import sys
    from backup_sqlite import main

    source = tmp_path / "source.db"
    destination = tmp_path / "backup.db"
    with sqlite3.connect(source) as db:
        db.execute("CREATE TABLE sample (value TEXT)")
        db.execute("INSERT INTO sample VALUES ('preserved')")
    monkeypatch.setattr(get_settings(), "database_url", f"sqlite:///{source.as_posix()}")
    monkeypatch.setattr(sys, "argv", ["backup_sqlite.py", str(destination)])
    main()
    with sqlite3.connect(destination) as restored:
        assert restored.execute("SELECT value FROM sample").fetchone() == ("preserved",)
    with pytest.raises(SystemExit, match="existing files"):
        main()
