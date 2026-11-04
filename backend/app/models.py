from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Upload(Base):
    """One row per weekly sheet upload (a 'batch')."""

    __tablename__ = "uploads"

    id = Column(Integer, primary_key=True)
    upload_date = Column(Date, nullable=False, index=True)
    filename = Column(String, nullable=False)
    row_count = Column(Integer, nullable=False, default=0)
    uploaded_by = Column(String, nullable=True)  # ready for auth: store username/user id later
    created_at = Column(DateTime, server_default=func.now())

    snapshots = relationship("Snapshot", back_populates="upload", cascade="all, delete-orphan")


class Snapshot(Base):
    """
    One row per loan per upload. This is the append-only history: every
    weekly upload adds a new set of Snapshot rows rather than overwriting
    the previous week's, which is what makes loan-level trend tracking
    possible.
    """

    __tablename__ = "snapshots"
    __table_args__ = (
        UniqueConstraint("loan_id", "upload_date", name="uq_loan_per_upload_date"),
        Index("ix_snapshots_upload_date_days", "upload_date", "days_past_due"),
    )

    id = Column(Integer, primary_key=True)
    upload_id = Column(Integer, ForeignKey("uploads.id"), nullable=False)
    upload_date = Column(Date, nullable=False, index=True)

    loan_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=True)
    borrower = Column(String, nullable=True)
    loan_product = Column(String, nullable=True, index=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    approved = Column(Date, nullable=True)
    loan_schedules = Column(Integer, nullable=True)

    principal = Column(Float, nullable=True)
    principal_paid = Column(Float, nullable=True)
    principal_due = Column(Float, nullable=True)

    interest = Column(Float, nullable=True)
    interest_paid = Column(Float, nullable=True)
    interest_due = Column(Float, nullable=True)

    fees = Column(Float, nullable=True)
    total_fees_paid = Column(Float, nullable=True)
    fees_due = Column(Float, nullable=True)

    penalty = Column(Float, nullable=True)
    total_penalty_paid = Column(Float, nullable=True)
    penalty_due = Column(Float, nullable=True)

    total_amount_paid = Column(Float, nullable=True)
    total_amount_due = Column(Float, nullable=True)
    past_due_amount = Column(Float, nullable=True)
    portfolio_at_risk = Column(Float, nullable=True)
    past_due_schedules = Column(Integer, nullable=True)

    date_due = Column(Date, nullable=True)
    first_past_due = Column(Date, nullable=True)
    last_past_due = Column(Date, nullable=True)
    scheduled_last_day = Column(Date, nullable=True)

    address = Column(String, nullable=True)
    manager_id = Column(String, nullable=True)
    account_manager_name = Column(String, nullable=True)

    days_past_due = Column(Integer, nullable=False, default=0)
    # Computed from days_past_due using CBN (Deposit Money Bank) bands —
    # see app/categorization.py. This is what every view/sort/trend uses.
    category = Column(String, nullable=False, index=True)
    # Zaradera's own "Performance Classification" from the sheet, kept for
    # reference/comparison only — it does not drive `category` above.
    sheet_classification = Column(String, nullable=True)

    upload = relationship("Upload", back_populates="snapshots")


class User(Base):
    """
    Not used yet (no login required initially), but kept here so adding
    auth later is additive rather than a rewrite: wire up a real auth
    library against this table and start populating uploaded_by.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
