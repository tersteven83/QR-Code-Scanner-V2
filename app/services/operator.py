
import json
from sqlalchemy.orm import Session

from app.helpers import models
from app.helpers import schemas
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_operator(db:Session, op_name: str):
    return db.query(models.Operator).filter(models.Operator.nom == op_name).first()

def create(db: Session, op_param: schemas.OperatorCreate):
    hashed_password = pwd_context.hash(op_param.password)
    db_operator = models.Operator(
        nom=op_param.nom,
        hashed_password=hashed_password,
    )
    db.add(db_operator)
    db.commit()
    db.refresh(db_operator)
    return schemas.Operator(**db_operator.__dict__)


def update(db: Session, id_operator: int, data_to_update: dict):
    db.query(models.Operator).filter(models.Operator.id == id_operator)\
        .update(data_to_update)
    db.commit()
    return get_by_id(db, id_operator)


def get_by_id(db: Session, id_operator: int):
    return db.query(models.Operator).filter(models.Operator.id == id_operator).first()


def delete(db: Session, id_operator: int):
    db.query(models.Operator).filter(models.Operator.id == id_operator).delete()
    db.commit()
    return json.dumps({"message": "Opérateur supprimé avec succès"})


def get_operators(db: Session):
    return db.query(models.Operator).all()
