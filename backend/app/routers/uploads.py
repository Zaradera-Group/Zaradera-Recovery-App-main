from datetime import date

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app import crud
from app.config import get_settings, business_today
from app.database import get_db
from app.parser import parse_workbook, SheetParseError
from app.schemas import UploadResult

router = APIRouter(prefix="/api/uploads", tags=["uploads"])


@router.post("", response_model=UploadResult)
async def upload_sheet(
    file: UploadFile = File(...),
    upload_date: date | None = Form(None),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(400, "Please upload an .xlsx workbook. Save older .xls files as .xlsx first.")

    target_date = upload_date or business_today()
    if target_date > business_today():
        raise HTTPException(400, "Upload date can't be in the future.")

    limit = get_settings().max_upload_bytes
    file_bytes = await file.read(limit + 1)
    if len(file_bytes) > limit:
        raise HTTPException(413, "Workbook exceeds the configured upload size limit.")

    try:
        rows = parse_workbook(file_bytes)
    except SheetParseError as exc:
        raise HTTPException(422, str(exc)) from exc

    if not rows:
        raise HTTPException(422, "No loan rows found in the sheet.")

    prev_date = crud.get_previous_upload_date(db, target_date)
    ids_before = crud.get_loan_ids_for_date(db, prev_date) if prev_date else set()

    upload = crud.create_upload(db, filename=file.filename, rows=rows, upload_date=target_date)

    ids_after = {r["loan_id"] for r in rows}
    new_loans = len(ids_after - ids_before)
    disappeared = len(ids_before - ids_after) if ids_before else 0

    return UploadResult(
        upload_id=upload.id,
        upload_date=upload.upload_date,
        filename=upload.filename,
        row_count=upload.row_count,
        skipped_rows=0,
        new_loans=new_loans,
        disappeared_loans=disappeared,
    )
