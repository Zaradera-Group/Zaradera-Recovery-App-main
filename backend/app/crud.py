from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.categorization import categorize, category_rank
from app.config import business_today
from app.models import Snapshot, Upload


def get_latest_upload_date(db: Session) -> date | None:
    return db.scalar(select(func.max(Upload.upload_date)))


def get_previous_upload_date(db: Session, before: date) -> date | None:
    return db.scalar(
        select(func.max(Upload.upload_date)).where(Upload.upload_date < before)
    )


def get_loan_ids_for_date(db: Session, upload_date: date) -> set[str]:
    rows = db.scalars(
        select(Snapshot.loan_id).where(Snapshot.upload_date == upload_date)
    ).all()
    return set(rows)


def replace_upload_for_date(db: Session, upload_date: date) -> None:
    """
    If a batch was already uploaded for this exact date (e.g. someone
    re-uploads a corrected sheet the same day), remove it first so the
    re-upload replaces it cleanly instead of erroring on the unique
    constraint or duplicating rows. Any *earlier* week's history is
    untouched.
    """
    existing = db.scalar(select(Upload).where(Upload.upload_date == upload_date))
    if existing is not None:
        db.delete(existing)  # cascades to its snapshots
        db.flush()


def create_upload(
    db: Session, filename: str, rows: list[dict], upload_date: date | None = None, uploaded_by: str | None = None
) -> Upload:
    """
    Persist one weekly batch as a new Upload + a Snapshot row per loan.
    This never touches previous weeks' rows, which is what preserves history.
    """
    if upload_date is None:
        upload_date = business_today()

    replace_upload_for_date(db, upload_date)

    upload = Upload(upload_date=upload_date, filename=filename, row_count=len(rows), uploaded_by=uploaded_by)
    db.add(upload)
    db.flush()  # get upload.id without committing yet

    for row in rows:
        days_past_due = row.get("days_past_due") or 0
        category = categorize(days_past_due)

        snapshot = Snapshot(
            upload_id=upload.id,
            upload_date=upload_date,
            loan_id=str(row.get("loan_id")),
            user_id=row.get("user_id"),
            borrower=row.get("borrower"),
            loan_product=row.get("loan_product"),
            email=row.get("email"),
            phone=row.get("phone"),
            approved=row.get("approved"),
            loan_schedules=row.get("loan_schedules"),
            principal=row.get("principal"),
            principal_paid=row.get("principal_paid"),
            principal_due=row.get("principal_due"),
            interest=row.get("interest"),
            interest_paid=row.get("interest_paid"),
            interest_due=row.get("interest_due"),
            fees=row.get("fees"),
            total_fees_paid=row.get("total_fees_paid"),
            fees_due=row.get("fees_due"),
            penalty=row.get("penalty"),
            total_penalty_paid=row.get("total_penalty_paid"),
            penalty_due=row.get("penalty_due"),
            total_amount_paid=row.get("total_amount_paid"),
            total_amount_due=row.get("total_amount_due"),
            past_due_amount=row.get("past_due_amount"),
            portfolio_at_risk=row.get("portfolio_at_risk"),
            past_due_schedules=row.get("past_due_schedules"),
            date_due=row.get("date_due"),
            first_past_due=row.get("first_past_due"),
            last_past_due=row.get("last_past_due"),
            scheduled_last_day=row.get("scheduled_last_day"),
            address=row.get("address"),
            manager_id=row.get("manager_id"),
            account_manager_name=row.get("account_manager_name"),
            days_past_due=days_past_due,
            category=category,
            sheet_classification=row.get("performance_classification"),
        )
        db.add(snapshot)

    db.commit()
    db.refresh(upload)
    return upload


def get_snapshots_for_date(db: Session, upload_date: date) -> list[Snapshot]:
    return list(
        db.scalars(
            select(Snapshot).where(Snapshot.upload_date == upload_date)
        ).all()
    )


def get_latest_snapshots(db: Session) -> list[Snapshot]:
    latest = get_latest_upload_date(db)
    if latest is None:
        return []
    return get_snapshots_for_date(db, latest)


def get_loan_history(db: Session, loan_id: str) -> list[Snapshot]:
    return list(
        db.scalars(
            select(Snapshot)
            .where(Snapshot.loan_id == loan_id)
            .order_by(Snapshot.upload_date.asc())
        ).all()
    )


def get_disappeared_loans(db: Session, upload_date: date | None = None) -> list[str]:
    """Loans present in the previous upload but missing from the latest one."""
    latest = upload_date or get_latest_upload_date(db)
    if latest is None:
        return []
    previous = get_previous_upload_date(db, latest)
    if previous is None:
        return []

    latest_ids = get_loan_ids_for_date(db, latest)
    previous_ids = get_loan_ids_for_date(db, previous)
    return sorted(previous_ids - latest_ids)


def get_trend(db: Session, upload_date: date | None = None) -> list[dict]:
    """
    Compare the two most recent uploads loan-by-loan to flag who's
    worsening vs improving. Loans only in one of the two batches are
    excluded here (see get_disappeared_loans for the "vanished" case).
    """
    latest = upload_date or get_latest_upload_date(db)
    if latest is None:
        return []
    previous = get_previous_upload_date(db, latest)
    if previous is None:
        return []

    latest_snaps = {s.loan_id: s for s in get_snapshots_for_date(db, latest)}
    previous_snaps = {s.loan_id: s for s in get_snapshots_for_date(db, previous)}

    entries = []
    for loan_id, current in latest_snaps.items():
        prior = previous_snaps.get(loan_id)
        if prior is None:
            continue  # new loan this week, nothing to compare

        prior_rank = category_rank(prior.category)
        current_rank = category_rank(current.category)
        if current_rank > prior_rank or current.days_past_due > prior.days_past_due:
            direction = "worsening"
        elif current_rank < prior_rank or current.days_past_due < prior.days_past_due:
            direction = "improving"
        else:
            direction = "unchanged"

        entries.append(
            {
                "loan_id": loan_id,
                "borrower": current.borrower,
                "loan_product": current.loan_product,
                "previous_days_past_due": prior.days_past_due,
                "current_days_past_due": current.days_past_due,
                "previous_category": prior.category,
                "current_category": current.category,
                "direction": direction,
            }
        )

    return entries
