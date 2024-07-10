from datetime import datetime
from typing_extensions import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.helpers import schemas
from app.helpers.database import SessionLocal
from app.utils.auth import get_current_active_operator

from ..services import journal as journal_service


router = APIRouter(
    prefix="/journal",
    tags=["Journals"]
)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
        
@router.get("/", response_model=list[schemas.Journal])
async def read_journals(current_op: Annotated[schemas.Operator, Depends(get_current_active_operator)],
                        skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    journals = journal_service.get_all(db, skip=skip, limit=limit)
    return journals


@router.get("/{id_operation}", response_model=schemas.Journal)
async def read_journal(current_op: Annotated[schemas.Operator, Depends(get_current_active_operator)],
                       id_operation: int, db: Session = Depends(get_db)):
    journal = journal_service.get_by_id(db, id_operation)
    if journal is None:
        raise HTTPException(status_code=404, detail="Opération non enregistrée.")
    return journal


@router.get("/date", response_model=list[schemas.Journal])
async def read_journals_by_date(current_op: Annotated[schemas.Operator, Depends(get_current_active_operator)],
                                debut: datetime, fin: datetime|None = None, db: Session = Depends(get_db)):
    if fin is None:
        journals = journal_service.get_by_date(db, debut)
    else:
        journals = journal_service.get_by_date(db, debut, fin)
    
    return journals


@router.post("/", response_model=schemas.Journal)
async def create_journal(current_op: Annotated[schemas.Operator, Depends(get_current_active_operator)],
                         journal: schemas.JournalCreate, db: Session = Depends(get_db)):
    """Insertion dans le journal"""
    journal_schema_to_db = schemas.JournalToDB(
        id_operator=current_op.id,
        **journal.model_dump()
    )
    journal = journal_service.create(db, journal_schema_to_db)
    return journal



@router.delete("/{id_operation}")
async def delete_journal(current_op: Annotated[schemas.Operator, Depends(get_current_active_operator)],
                         id_operation: int, db: Session = Depends(get_db)):
    """Suppression d'une opération"""
    return journal_service.delete(db, id_operation)