from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas import DashboardSummary, SnapshotOut, TrendEntry

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _snapshots_for(db: Session, upload_date: date | None) -> list:
    if upload_date is not None:
        return crud.get_snapshots_for_date(db, upload_date)
    return crud.get_latest_snapshots(db)


@router.get("/summary", response_model=DashboardSummary)
def summary(upload_date: date | None = Query(None), db: Session = Depends(get_db)):
    latest = upload_date or crud.get_latest_upload_date(db)
    previous = crud.get_previous_upload_date(db, latest) if latest else None
    snapshots = crud.get_snapshots_for_date(db, latest) if latest else []

    by_category: dict[str, int] = {}
    total_past_due = 0.0
    total_par = 0.0
    for s in snapshots:
        by_category[s.category] = by_category.get(s.category, 0) + 1
        total_past_due += s.past_due_amount or 0
        total_par += s.portfolio_at_risk or 0

    return DashboardSummary(
        latest_upload_date=latest,
        previous_upload_date=previous,
        total_loans=len(snapshots),
        total_past_due_amount=total_past_due,
        total_portfolio_at_risk=total_par,
        by_category_counts=by_category,
    )


@router.get("/by-product", response_model=dict[str, list[SnapshotOut]])
def by_product(upload_date: date | None = Query(None), db: Session = Depends(get_db)):
    snapshots = _snapshots_for(db, upload_date)
    grouped: dict[str, list] = {}
    for s in sorted(snapshots, key=lambda s: s.days_past_due, reverse=True):
        grouped.setdefault(s.loan_product or "Unspecified", []).append(s)
    return grouped


@router.get("/by-days", response_model=list[SnapshotOut])
def by_days(upload_date: date | None = Query(None), db: Session = Depends(get_db)):
    snapshots = _snapshots_for(db, upload_date)
    return sorted(snapshots, key=lambda s: s.days_past_due, reverse=True)


@router.get("/by-category", response_model=dict[str, list[SnapshotOut]])
def by_category(upload_date: date | None = Query(None), db: Session = Depends(get_db)):
    snapshots = _snapshots_for(db, upload_date)
    grouped: dict[str, list] = {}
    for s in sorted(snapshots, key=lambda s: s.days_past_due, reverse=True):
        grouped.setdefault(s.category, []).append(s)
    return grouped


@router.get("/trend", response_model=list[TrendEntry])
def trend(upload_date: date | None = Query(None), db: Session = Depends(get_db)):
    return crud.get_trend(db, upload_date)


@router.get("/disappeared", response_model=list[str])
def disappeared(upload_date: date | None = Query(None), db: Session = Depends(get_db)):
    return crud.get_disappeared_loans(db, upload_date)


@router.get("/upload-dates", response_model=list[date])
def upload_dates(db: Session = Depends(get_db)):
    from sqlalchemy import select
    from app.models import Upload

    rows = db.scalars(select(Upload.upload_date).order_by(Upload.upload_date.desc())).all()
    return list(rows)
