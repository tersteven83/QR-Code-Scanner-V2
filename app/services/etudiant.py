import base64
from datetime import datetime, timedelta
from typing import Type, Union
from uuid import uuid1, uuid4
import zlib

from sqlalchemy.orm import Session
import json

from app.services.qrcode import generate_qr_code, send_email

from ..helpers import models, schemas
from ..services import journal as journal_service
from ..services import qrcode as qrcode_service


def create(db: Session, 
           etudiant: schemas.EtudiantCreate, 
           operateur: schemas.Operator):
    """
    Création d'un étudiant et logger l'operation dans la base de donnée
    """
    # Créer un étudiant
    db_etudiant = models.Etudiant(**etudiant.model_dump())
    db.add(db_etudiant)
    db.commit()
    db.refresh(db_etudiant)

    # créer un code QR pour ce dernier
    qr_code_data = str(db_etudiant.id) + "_" + str(uuid4())
    qcode_dict = {
        "id_etudiant": db_etudiant.id,
        "expire_date": datetime.now() + timedelta(days=365),
        "is_valid": True,
        "data": qr_code_data,
        "created_at": datetime.now()
    }
    db_qcode = models.QR_Code(**qcode_dict)
    db.add(db_qcode)
    db.commit() 
    
    # Insertion dans le journal
    creation_journal = schemas.JournalCreate(
        operation="Création d'un étudiant",
        date=datetime.now(),
        im_etudiant=db_etudiant.matricule
    )
    insert_into_journal(current_op=operateur, journal=creation_journal, db=db)

    # Rafraîchir avant de retourner vers la route
    db.refresh(db_etudiant)
    db.refresh(db_qcode)
    
    # Envoyer le QR code à l'@ email de l'étudiant
    qr_code_image = generate_qr_code(qr_code_data)
    send_email(to_email=db_etudiant.email, qr_code_image=qr_code_image)

    return db_etudiant


def update(db: Session, id_etudiant: int, etudiant_param: dict, operateur: schemas.Operator):
    db.query(models.Etudiant).filter(models.Etudiant.id == id_etudiant)\
        .update(etudiant_param)
    db.commit()
    
    db_etudiant = get_by_id(db, id_etudiant)
    #insertion dans le journal
    update_journal = schemas.JournalCreate(
        operation="Modification d'un étudiant",
        date=datetime.now(),
        im_etudiant=db_etudiant.matricule
    )
    insert_into_journal(current_op=operateur, journal=update_journal, db=db)

    return db_etudiant


def delete(db: Session, id_etudiant: int, operateur: schemas.Operator):
    """
    Suppression d'un étudiant et insertion dans le journal
    """
    # Récuperer d'abord l'immatricule de l'étudiant avant de le supprimer
    db_etudiant = get_by_id(db, id_etudiant).__dict__
    db.query(models.Etudiant).filter(models.Etudiant.id == id_etudiant).delete()
    db.commit()
    
    # insertion dans le journal
    delete_journal = schemas.JournalCreate(
        operation=f"Suppression de {db_etudiant['nom']} {db_etudiant['prenom']} IM: {db_etudiant['matricule']} classe: {db_etudiant['niveau']} {db_etudiant['parcours']} année: {db_etudiant['annee_univ']}",
        date=datetime.now()
    )
    insert_into_journal(current_op=operateur, journal=delete_journal, db=db)

    return json.dumps({"message": "Étudiant supprimé avec succès"})


def get_by_id(db: Session, id_etudiant: int) -> models.Etudiant:
    return db.query(models.Etudiant).filter(models.Etudiant.id == id_etudiant).first()


def get_by_im(db: Session, im: str) -> models.Etudiant:
    return db.query(models.Etudiant).filter(models.Etudiant.matricule == im).first()


def get_all(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Etudiant)\
        .offset(skip).limit(limit).all()


def get_by_cin(db: Session, cin: str):
    return db.query(models.Etudiant).filter(models.Etudiant.cin == cin).first()


def get_by_qrcode(db: Session, qcode_data: str):
    """
    Récupère l'étudiant associé à un code QR
    """
    # Rechercher d'abord le qr code dans la base de donnée
    qcode = qrcode_service.get_by_data(db, qcode_data)
    if qcode is not None:
        return get_by_id(db, qcode.id_etudiant)
    else:
        return None


def insert_into_journal(current_op: schemas.Operator, 
                        journal: schemas.JournalCreate,
                        db: Session):
    """
    Insertion dans le journal
    """
    journal_schema_to_db = schemas.JournalToDB(
        id_operator=current_op.id,
        **journal.model_dump()
    )
    journal = journal_service.create(db, journal_schema_to_db)
    return journal