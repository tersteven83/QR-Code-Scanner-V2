from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.utils.auth import get_current_active_operator

from ..services import etudiant as etudiant_service
from ..helpers.database import SessionLocal
from ..helpers import schemas


router = APIRouter(
    prefix="/etudiants",
    tags=["etudiants"]
)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=list[schemas.Etudiant])
async def read_etudiants(current_op: Annotated[schemas.Operator, Depends(get_current_active_operator)],
                         skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    etudiants = etudiant_service.get_all(db, skip=skip, limit=limit)
    return etudiants


@router.get("/{user_im}", response_model=schemas.Etudiant)
async def read_etudiant(im: str, db: Session = Depends(get_db)):
    etudiant = etudiant_service.get_by_im(db, im)
    if etudiant is None:
        raise HTTPException(status_code=404, detail="Le numéro matricule n'existe pas.")
    return etudiant


@router.get("/{qcode_data}", response_model=schemas.Etudiant)
async def read_etudiant_by_qrcode(qcode_data: str, db: Session = Depends(get_db)):
    etudiant = etudiant_service.get_by_qrcode(db, qcode_data)
    if etudiant is None:
        raise HTTPException(status_code=404, detail="Aucun étudiant associé au code QR.")
    return etudiant


@router.post("/", response_model=schemas.Etudiant)
async def create_etudiant(current_op: Annotated[schemas.Operator, Depends(get_current_active_operator)],
                          etudiant: schemas.EtudiantCreate, db: Session = Depends(get_db)):
    #     Vérifier d'abord si l'étudiant existe déjà dans la base de donnée
    is_present = etudiant_service.get_by_im(db=db, im=etudiant.matricule) or \
        etudiant_service.get_by_cin(db=db, cin=etudiant.cin) # type: ignore
    if is_present:
        raise HTTPException(status_code=400, detail="L'étudiant existe déja.")

    return etudiant_service.create(db, etudiant, current_op)


@router.put("/{id_etudiant}", response_model=schemas.Etudiant)
async def update_etudiant(current_op: Annotated[schemas.Operator, Depends(get_current_active_operator)],
                          id_etudiant: int, etudiant_to_update: schemas.EtudiantUpdate, db: Session = Depends(get_db)):
    is_present = etudiant_service.get_by_id(db, id_etudiant)
    if not is_present:
        raise HTTPException(status_code=404, detail="Étudiant non enregistré.")
      
    # effacer les clés à valeurs vides
    etudiant_to_update_dict = etudiant_to_update.model_dump(exclude_unset=True)
    return etudiant_service.update(db, id_etudiant=id_etudiant, etudiant_param=etudiant_to_update_dict, operateur=current_op)


@router.delete("/{id_etudiant}")
async def delete_etudiant(current_op: Annotated[schemas.Operator, Depends(get_current_active_operator)],
                          id_etudiant: int, db: Session = Depends(get_db)):
    is_present = etudiant_service.get_by_id(db, id_etudiant)
    if not is_present:
        raise HTTPException(status_code=404, detail="Étudiant non enregistré.")
    return etudiant_service.delete(db, id_etudiant, operateur=current_op)