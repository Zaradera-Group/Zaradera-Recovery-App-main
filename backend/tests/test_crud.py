from datetime import date, timedelta

from app import crud


def _row(loan_id, days_past_due, product="Boom Business Loan", sheet_classification="Doubtful", **extra):
    base = {
        "loan_id": loan_id,
        "user_id": "u1",
        "borrower": f"Borrower {loan_id}",
        "loan_product": product,
        "days_past_due": days_past_due,
        "performance_classification": sheet_classification,
        "principal": 100000.0,
        "past_due_amount": 5000.0,
        "portfolio_at_risk": 4000.0,
    }
    base.update(extra)
    return base


def test_create_upload_persists_snapshots_with_cbn_category(db_session):
    week1 = date.today() - timedelta(days=7)
    rows = [_row("L1", 20), _row("L2", 400)]

    crud.create_upload(db_session, filename="week1.xlsx", rows=rows, upload_date=week1)

    snapshots = crud.get_snapshots_for_date(db_session, week1)
    by_id = {s.loan_id: s for s in snapshots}
    assert by_id["L1"].category == "Performing"
    assert by_id["L2"].category == "Lost"


def test_category_is_computed_from_days_not_sheet_classification(db_session):
    """
    The category the app uses (for sorting, grouping, trend) is always
    computed from days-past-due via CBN bands, regardless of what
    Zaradera's own 'Performance Classification' column says — that value
    is kept only as a reference field.
    """
    week1 = date.today()
    rows = [_row("L1", 9, sheet_classification="Doubtful")]

    crud.create_upload(db_session, filename="week1.xlsx", rows=rows, upload_date=week1)

    snapshot = crud.get_snapshots_for_date(db_session, week1)[0]
    assert snapshot.category == "Performing"  # 9 days -> CBN "Performing"
    assert snapshot.sheet_classification == "Doubtful"  # kept for reference


def test_sheet_classification_optional(db_session):
    week1 = date.today()
    rows = [_row("L1", 9, sheet_classification=None)]

    crud.create_upload(db_session, filename="week1.xlsx", rows=rows, upload_date=week1)

    snapshot = crud.get_snapshots_for_date(db_session, week1)[0]
    assert snapshot.category == "Performing"
    assert snapshot.sheet_classification is None


def test_history_accumulates_across_uploads_without_overwriting(db_session):
    week1 = date.today() - timedelta(days=7)
    week2 = date.today()

    crud.create_upload(db_session, filename="w1.xlsx", rows=[_row("L1", 10)], upload_date=week1)
    crud.create_upload(db_session, filename="w2.xlsx", rows=[_row("L1", 45)], upload_date=week2)

    history = crud.get_loan_history(db_session, "L1")

    assert len(history) == 2
    assert history[0].upload_date == week1
    assert history[0].days_past_due == 10
    assert history[1].upload_date == week2
    assert history[1].days_past_due == 45


def test_reupload_same_date_replaces_not_duplicates(db_session):
    today = date.today()
    crud.create_upload(db_session, filename="v1.xlsx", rows=[_row("L1", 10)], upload_date=today)
    crud.create_upload(db_session, filename="v2-corrected.xlsx", rows=[_row("L1", 15)], upload_date=today)

    history = crud.get_loan_history(db_session, "L1")

    assert len(history) == 1
    assert history[0].days_past_due == 15


def test_disappeared_loans_detected(db_session):
    week1 = date.today() - timedelta(days=7)
    week2 = date.today()

    crud.create_upload(db_session, filename="w1.xlsx", rows=[_row("L1", 10), _row("L2", 20)], upload_date=week1)
    crud.create_upload(db_session, filename="w2.xlsx", rows=[_row("L1", 15)], upload_date=week2)

    disappeared = crud.get_disappeared_loans(db_session)

    assert disappeared == ["L2"]


def test_trend_flags_worsening_and_improving(db_session):
    week1 = date.today() - timedelta(days=7)
    week2 = date.today()

    crud.create_upload(
        db_session, filename="w1.xlsx",
        rows=[_row("WORSE", 10), _row("BETTER", 100), _row("SAME", 10)],
        upload_date=week1,
    )
    crud.create_upload(
        db_session, filename="w2.xlsx",
        rows=[_row("WORSE", 95), _row("BETTER", 10), _row("SAME", 10)],
        upload_date=week2,
    )

    trend = {t["loan_id"]: t["direction"] for t in crud.get_trend(db_session)}

    assert trend["WORSE"] == "worsening"
    assert trend["BETTER"] == "improving"
    assert trend["SAME"] == "unchanged"


def test_trend_excludes_new_loans(db_session):
    week1 = date.today() - timedelta(days=7)
    week2 = date.today()

    crud.create_upload(db_session, filename="w1.xlsx", rows=[_row("L1", 10)], upload_date=week1)
    crud.create_upload(db_session, filename="w2.xlsx", rows=[_row("L1", 10), _row("NEW", 5)], upload_date=week2)

    trend_ids = {t["loan_id"] for t in crud.get_trend(db_session)}

    assert "NEW" not in trend_ids
    assert "L1" in trend_ids
