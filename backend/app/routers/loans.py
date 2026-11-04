from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas import LoanHistoryPoint

router = APIRouter(prefix="/api/loans", tags=["loans"])


@router.get("/{loan_id}/history", response_model=list[LoanHistoryPoint])
def loan_history(loan_id: str, db: Session = Depends(get_db)):
    history = crud.get_loan_history(db, loan_id)
    if not history:
        raise HTTPException(404, f"No history found for loan {loan_id}")
    return history
