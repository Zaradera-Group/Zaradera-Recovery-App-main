"""
Parses the weekly "Past Due Loans" Excel export into a list of plain dicts
keyed by canonical field names, ready to be turned into Snapshot rows.

Column matching is tolerant of spacing/case/underscore differences (the
source sheet mixes styles, e.g. "Loan ID" vs "user_id" vs "total_fees_paid")
so a re-exported sheet with slightly different header formatting doesn't
break the upload.
"""
import re
from datetime import date, datetime
from io import BytesIO
import math

import pandas as pd

REQUIRED_FIELDS = ["loan_id", "loan_product", "days_past_due"]
# performance_classification is Zaradera's own system-assigned risk category,
# kept for reference only (see app/categorization.py for what actually
# drives the app's risk category — CBN day bands).

# canonical_field: list of header variants seen (or reasonably expected) in the sheet
_COLUMN_ALIASES: dict[str, list[str]] = {
    "loan_id": ["loan id", "loanid"],
    "user_id": ["user id", "userid"],
    "borrower": ["borrower"],
    "loan_product": ["loan product", "product"],
    "email": ["email"],
    "phone": ["phone"],
    "approved": ["approved"],
    "loan_schedules": ["loan schedules"],
    "principal": ["principal"],
    "principal_paid": ["principal paid"],
    "principal_due": ["principal due"],
    "interest": ["interest"],
    "interest_paid": ["interest paid"],
    "interest_due": ["interest due"],
    "fees": ["fees"],
    "total_fees_paid": ["total fees paid"],
    "fees_due": ["fees due"],
    "penalty": ["penalty"],
    "total_penalty_paid": ["total penalty paid"],
    "penalty_due": ["penalty due"],
    "total_amount_paid": ["total amount paid"],
    "total_amount_due": ["total amount due"],
    "past_due_amount": ["past due amount"],
    "portfolio_at_risk": ["portfolio at risk"],
    "past_due_schedules": ["past due schedules"],
    "date_due": ["date due"],
    "first_past_due": ["first past due"],
    "last_past_due": ["last past due"],
    "scheduled_last_day": ["scheduled last day"],
    "days_past_due": ["days past due"],
    "performance_classification": ["performance classification", "classification"],
    "address": ["address"],
    "manager_id": ["manager id"],
    "account_manager_name": ["account manager name", "account manager"],
}

_INT_FIELDS = {"loan_schedules", "past_due_schedules", "days_past_due"}
_FLOAT_FIELDS = {
    "principal", "principal_paid", "principal_due",
    "interest", "interest_paid", "interest_due",
    "fees", "total_fees_paid", "fees_due",
    "penalty", "total_penalty_paid", "penalty_due",
    "total_amount_paid", "total_amount_due",
    "past_due_amount", "portfolio_at_risk",
}
_DATE_FIELDS = {"approved", "date_due", "first_past_due", "last_past_due", "scheduled_last_day"}
_STR_FIELDS = {
    "loan_id", "user_id", "borrower", "loan_product", "email", "phone",
    "performance_classification", "address", "account_manager_name",
}
# IDs that arrive as floats (e.g. 17745.0) because of blank cells elsewhere in the
# column, but should be stored/displayed as plain identifiers, not numbers.
_ID_STR_FIELDS = {"manager_id"}


def _normalize(header: str) -> str:
    return re.sub(r"[\s_]+", " ", str(header).strip().lower()).strip()


class SheetParseError(ValueError):
    """Raised when the uploaded sheet is missing required columns."""


def _build_column_map(columns: list[str]) -> dict[str, str]:
    """Map each canonical field name to the actual dataframe column that matches it."""
    normalized_to_actual = {_normalize(c): c for c in columns}

    resolved: dict[str, str] = {}
    for canonical, aliases in _COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in normalized_to_actual:
                resolved[canonical] = normalized_to_actual[alias]
                break
    return resolved


def _clean_value(field: str, raw):
    # pandas' isna() uniformly catches None, float NaN, and NaT (its null-date
    # marker) in one check. NaT is a special case: it quietly passes an
    # isinstance(..., datetime) check (by design, for duck-typing), so a
    # naive "is this already a date object" branch lets a genuinely missing
    # date slip through as if it were valid — which then fails later, at
    # the database layer, in a confusing way. Checking isna() first avoids
    # that entirely.
    try:
        is_na = pd.isna(raw)
    except (TypeError, ValueError):
        is_na = False
    if raw is None or bool(is_na) or (isinstance(raw, str) and not raw.strip()):
        return None

    if field in _INT_FIELDS:
        try:
            number = float(raw)
            if not math.isfinite(number) or not number.is_integer() or number < 0 or number > 2147483647:
                raise ValueError()
            return int(number)
        except (ValueError, TypeError, OverflowError):
            raise SheetParseError(f"{field} must be a non-negative whole number.")

    if field in _FLOAT_FIELDS:
        try:
            number = float(str(raw).replace(",", ""))
            if not math.isfinite(number):
                raise ValueError()
            return number
        except (ValueError, TypeError):
            raise SheetParseError(f"{field} must be a finite number.")

    if field in _DATE_FIELDS:
        if isinstance(raw, (datetime, date)):
            return raw if isinstance(raw, date) and not isinstance(raw, datetime) else raw.date()
        try:
            parsed = pd.to_datetime(raw, errors="coerce")
            if pd.isna(parsed):
                raise ValueError()
            return parsed.date()
        except Exception as exc:
            raise SheetParseError(f"{field} contains an invalid date.") from exc

    if field in _STR_FIELDS:
        if field in {"loan_id", "user_id", "phone"} and isinstance(raw, float) and raw.is_integer():
            return str(int(raw))
        text = str(raw).strip()
        return text or None

    if field in _ID_STR_FIELDS:
        # Whole-number floats (17745.0) -> "17745"; leave genuine text IDs untouched.
        if isinstance(raw, float) and raw.is_integer():
            return str(int(raw))
        text = str(raw).strip()
        return text or None

    return raw


def parse_workbook(file_bytes: bytes) -> list[dict]:
    """
    Parse the uploaded .xlsx bytes into a list of dicts with canonical field
    names. Raises SheetParseError if required columns can't be found.
    """
    try:
        df = pd.read_excel(BytesIO(file_bytes), engine="openpyxl", dtype=object, keep_default_na=False)
    except Exception as exc:
        raise SheetParseError("Could not read the workbook. Upload a valid, unencrypted .xlsx file.") from exc
    df.columns = [str(c) for c in df.columns]

    column_map = _build_column_map(list(df.columns))

    missing_required = [f for f in REQUIRED_FIELDS if f not in column_map]
    if missing_required:
        raise SheetParseError(
            "Could not find required column(s) in the sheet: "
            f"{', '.join(missing_required)}. "
            f"Columns found: {', '.join(df.columns)}"
        )

    rows: list[dict] = []
    seen_ids = set()
    for index, row in df.iterrows():
        if _clean_value("loan_id", row.get(column_map["loan_id"])) is None:
            continue
        record: dict = {}
        for canonical, actual_col in column_map.items():
            try:
                record[canonical] = _clean_value(canonical, row.get(actual_col))
            except SheetParseError as exc:
                raise SheetParseError(f"Excel row {index + 2}: {exc}") from exc

        # A blank/summary row at the bottom of the sheet has no loan id — skip it.
        if not record.get("loan_id"):
            continue

        if record["loan_id"] in seen_ids:
            raise SheetParseError(f"Excel row {index + 2}: duplicate Loan ID {record['loan_id']}.")
        seen_ids.add(record["loan_id"])
        if not record.get("loan_product"):
            raise SheetParseError(f"Excel row {index + 2}: Loan Product is required.")

        record["days_past_due"] = record.get("days_past_due") or 0

        # Belt-and-braces: whatever the source, no raw NaN float should ever
        # leave this function — it can't be stored (SQLAlchemy/SQLite reject
        # it for numeric columns) and every field above should already have
        # converted it to None, but this catches any edge case that slips
        # through unusual cell formatting in a given export.
        for key, value in record.items():
            if isinstance(value, float) and math.isnan(value):
                record[key] = None

        rows.append(record)

    return rows
