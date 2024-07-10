from typing import Union

from datetime import datetime
from pydantic import BaseModel, EmailStr


class QR_CodeBase(BaseModel):
    expire_date: datetime
    is_valid: bool = True
    data: str
    created_at: datetime


class QR_CodeCreate(QR_CodeBase):
    id_etudiant: int


class QR_Code(QR_CodeBase):
    id: int

    class Config:
        orm_mode = True


class EtudiantBase(BaseModel):
    nom: str
    prenom: str
    dob: datetime
    cin: Union[str, None] = None
    cin_date: Union[datetime, None] = None
    tel: str
    email: EmailStr
    adresse: str
    niveau: str
    parcours: str
    matricule: str
    annee_univ: str


class EtudiantCreate(EtudiantBase):
    pass


class EtudiantUpdate(BaseModel):
    # Cette classe n'inhérite pas de EtudiantBase car les attributs peuvent être null
    nom: Union[str, None] = None
    prenom: Union[str, None] = None
    dob: Union[datetime, None] = None
    cin: Union[str, None] = None
    cin_date: Union[datetime, None] = None
    tel: Union[str, None] = None
    email: Union[EmailStr, None] = None
    adresse: Union[str, None] = None
    niveau: Union[str, None] = None
    parcours: Union[str, None] = None
    annee_univ: Union[str, None] = None
    matricule: Union[str, None] = None


class Etudiant(EtudiantBase):
    id: int
    qrcode: Union[list[QR_Code], None] = None

    class Config:
        orm_mode = True


class OperatorBase(BaseModel):
    nom: str
    disabled: bool = False
    refresh_token: Union[str, None] = None


class OperatorCreate(OperatorBase):
    password: str
    

class OperatorInDB(OperatorBase):
    id: int
    hashed_password: str
    
    class Config:
        orm_mode = True


class Operator(OperatorBase):
    id: int

    class Config:
        orm_mode = True
        
class OperatorUdpate(BaseModel):
    nom: Union[str, None] = None
    disabled: Union[bool, None] = None
    refresh_token: Union[str, None] = None


class JournalBase(BaseModel):
    operation: str
    date: datetime


class JournalCreate(JournalBase):
    im_etudiant: Union[str, None] = None
    

class JournalToDB(JournalCreate):
    id_operator: int


class Journal(JournalBase):
    id: int
    effectue_par: Operator
    etudiant: Union[Etudiant, str] = "Etudiant indisponible"

    class Config:
        orm_mode = True
        

class Token(BaseModel):
    access_token: str
    token_type: str
    

class TokenData(BaseModel):
    op_name: str
