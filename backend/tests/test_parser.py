from io import BytesIO

import pandas as pd
import pytest

from app.parser import parse_workbook, SheetParseError


def _make_xlsx_bytes(columns: list[str], rows: list[list]) -> bytes:
    df = pd.DataFrame(rows, columns=columns)
    buffer = BytesIO()
    df.to_excel(buffer, index=False, engine="openpyxl")
    return buffer.getvalue()


REAL_COLUMNS = [
    "Loan ID", "user_id", "Borrower", "Loan Product", "Email", "Phone", "Approved",
    "Loan Schedules", "Principal", "Principal Paid", "Principal Due", "Interest",
    "Interest Paid", "Interest Due", "Fees", "total_fees_paid", "Fees Due", "Penalty",
    "total_penalty_paid", "Penalty Due", "total_amount_paid", "Total Amount Due",
    "past_due_amount", "portfolio_at_risk", "Past Due Schedules", "Date Due",
    "First Past Due", "Last Past Due", "Scheduled Last Day", "Days Past Due",
    "Performance Classification", "Address", "manager_id", "account_manager_name",
]


def test_parses_real_column_layout():
    row = [
        551412, 3681222, "Oluchi Ema-etokudo", "Boom Business Loan", "oluchiee@gmail.com",
        "2348036701154", "2026-06-19", 6, 17400000, 2900000, 14500000, 10440000,
        3059334, 7380666, 0, 0, 0, 746414, 680666, 65748, 6640000, 21946414,
        3386414, 2900000, 1, "2026-08-19", "2026-08-19", "2026-12-19", "2026-12-19", 20,
        "Doubtful", "12 Marina Road, Lagos", 17745.0, "Okedi Chelam",
    ]
    data = _make_xlsx_bytes(REAL_COLUMNS, [row])

    parsed = parse_workbook(data)

    assert len(parsed) == 1
    loan = parsed[0]
    assert loan["loan_id"] == "551412"
    assert loan["loan_product"] == "Boom Business Loan"
    assert loan["days_past_due"] == 20
    assert loan["principal"] == 17400000.0
    assert loan["performance_classification"] == "Doubtful"
    assert loan["manager_id"] == "17745"
    assert loan["account_manager_name"] == "Okedi Chelam"


def test_missing_required_column_raises():
    columns = [c for c in REAL_COLUMNS if c != "Days Past Due"]
    data = _make_xlsx_bytes(columns, [["1"] + [None] * (len(columns) - 1)])

    with pytest.raises(SheetParseError, match="days_past_due"):
        parse_workbook(data)


def test_blank_rows_are_skipped():
    row = ["551412", 1, "A", "Boom Business Loan"] + [None] * 29 + [20]
    blank_row = [None] * 34
    data = _make_xlsx_bytes(REAL_COLUMNS, [row, blank_row])

    parsed = parse_workbook(data)

    assert len(parsed) == 1


def test_missing_days_past_due_defaults_to_zero():
    row = ["551412", 1, "A", "Boom Business Loan"] + [None] * 29 + [None]
    data = _make_xlsx_bytes(REAL_COLUMNS, [row])

    parsed = parse_workbook(data)

    assert parsed[0]["days_past_due"] == 0
