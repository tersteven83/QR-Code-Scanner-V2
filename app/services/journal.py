import json
from typing import Union

from datetime import datetime
from sqlalchemy.orm import Session

from ..helpers import models, schemas


def create(db: Session, operation: schemas.JournalToDB):
    db_journal = models.Journal(**operation.model_dump())
    db.add(db_journal)
    db.commit()
    db.refresh(db_journal)
    
    return db_journal


def get_by_id(db: Session, id_operation: int):
    return db.query(models.Journal).filter(models.Journal.id == id_operation).first()


def get_all(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Journal)\
        .offset(skip).limit(limit).all()
        

def get_by_date(db: Session, debut: datetime, fin: Union[datetime, None] = None):
    if fin is None:
        return db.query(models.Journal).filter(models.Journal.date >= debut).all()
    else:
        return db.query(models.Journal).filter(models.Journal.date >= debut).filter(models.Journal.date <= fin).all()
    

def delete(db: Session, id_operation: int):
    db.query(models.Journal).filter(models.Journal.id == id_operation).delete()
    db.commit()
    return json.dumps({"message": "Opération supprimée avec succès"})