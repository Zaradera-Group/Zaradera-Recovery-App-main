from io import BytesIO

import pandas as pd

from tests.test_parser import REAL_COLUMNS


def _upload_file(loan_rows: list[list]):
    df = pd.DataFrame(loan_rows, columns=REAL_COLUMNS)
    buffer = BytesIO()
    df.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)
    return buffer


def _row(loan_id, days, product="Boom Business Loan", sheet_classification="Doubtful"):
    return [
        loan_id, 1, f"Borrower {loan_id}", product, "a@example.com", "2348000000000",
        "2026-01-01", 6, 100000, 0, 100000, 10000, 0, 10000, 0, 0, 0, 0, 0, 0, 0,
        110000, 5000, 4000, 1, "2026-08-19", "2026-08-19", "2026-12-19", "2026-12-19", days,
        sheet_classification, "Test Address", 111.0, "Test Manager",
    ]


def test_upload_endpoint_rejects_non_excel_file(client):
    response = client.post(
        "/api/uploads",
        files={"file": ("data.csv", BytesIO(b"not excel"), "text/csv")},
    )
    assert response.status_code == 400


def test_upload_then_dashboard_views(client):
    file_bytes = _upload_file([
        _row("L1", 20, "Boom Business Loan"),
        _row("L2", 400, "Capacity Loan (PayDay)"),
    ])

    upload_response = client.post(
        "/api/uploads",
        files={"file": ("week1.xlsx", file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert upload_response.status_code == 200
    body = upload_response.json()
    assert body["row_count"] == 2

    by_days = client.get("/api/dashboard/by-days").json()
    assert [row["loan_id"] for row in by_days] == ["L2", "L1"]  # highest days first

    by_category = client.get("/api/dashboard/by-category").json()
    assert "Lost" in by_category
    assert "Performing" in by_category

    by_product = client.get("/api/dashboard/by-product").json()
    assert "Boom Business Loan" in by_product
    assert "Capacity Loan (PayDay)" in by_product

    summary = client.get("/api/dashboard/summary").json()
    assert summary["total_loans"] == 2


def test_loan_history_endpoint(client):
    file_bytes = _upload_file([_row("L1", 20)])
    client.post(
        "/api/uploads",
        files={"file": ("week1.xlsx", file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )

    history = client.get("/api/loans/L1/history")
    assert history.status_code == 200
    assert len(history.json()) == 1

    missing = client.get("/api/loans/UNKNOWN/history")
    assert missing.status_code == 404
