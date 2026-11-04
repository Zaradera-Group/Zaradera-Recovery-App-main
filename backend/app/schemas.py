from datetime import date, datetime
from pydantic import BaseModel, ConfigDict


class UploadResult(BaseModel):
    upload_id: int
    upload_date: date
    filename: str
    row_count: int
    skipped_rows: int
    new_loans: int
    disappeared_loans: int


class SnapshotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    loan_id: str
    borrower: str | None = None
    loan_product: str | None = None
    email: str | None = None
    phone: str | None = None
    account_manager_name: str | None = None
    approved: date | None = None
    principal: float | None = None
    total_amount_due: float | None = None
    past_due_amount: float | None = None
    portfolio_at_risk: float | None = None
    days_past_due: int
    category: str
    sheet_classification: str | None = None
    upload_date: date


class LoanHistoryPoint(BaseModel):
    upload_date: date
    days_past_due: int
    category: str
    sheet_classification: str | None = None
    past_due_amount: float | None = None
    portfolio_at_risk: float | None = None


class TrendEntry(BaseModel):
    loan_id: str
    borrower: str | None = None
    loan_product: str | None = None
    previous_days_past_due: int
    current_days_past_due: int
    previous_category: str
    current_category: str
    direction: str  # "worsening" | "improving" | "unchanged"


class DashboardSummary(BaseModel):
    latest_upload_date: date | None
    previous_upload_date: date | None
    total_loans: int
    total_past_due_amount: float
    total_portfolio_at_risk: float
    by_category_counts: dict[str, int]
