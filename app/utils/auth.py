from datetime import datetime, timedelta, UTC
import os
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError
import jwt

from typing import Annotated, Union
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.helpers import schemas
from app.helpers.database import SessionLocal
from app.services import operator as operator_service


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")) # type: ignore
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS")) # type: ignore

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
        
def verify_password(plain_password, hashed_password):
    """
    Vérification de mot de passe
    """
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_operator(operator_name: str, password: str, db: Session):
    """
    Authentification de l'opérateur
    """
    db_operator = operator_service.get_operator(db, operator_name)
    if not db_operator:
        return False
    if not verify_password(password, db_operator.hashed_password):
        return False
    
    return schemas.Operator(**db_operator.__dict__)

async def get_current_operator(db: Annotated[Session, Depends(get_db)], token: Annotated[str, Depends(oauth2_scheme)]):
    """
    Récupération de l'opérateur courant
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]) # type: ignore
        op_name: str = payload.get("sub")
        if op_name is None:
            raise HTTPException(status_code=400, detail="Token non validé")
        
        token_data = schemas.TokenData(op_name=op_name)
    except (jwt.InvalidTokenError, jwt.exceptions.DecodeError):
        raise HTTPException(status_code=400, detail="Token non tay aminamany")
    
    operator = operator_service.get_operator(db, token_data.op_name)
    if operator is None:
        raise HTTPException(status_code=404, detail="Opérateur non enregistré.")
    
    return schemas.Operator(**operator.__dict__)

async def get_current_active_operator(
    current_op: Annotated[schemas.Operator, Depends(get_current_operator)]
    ) -> schemas.Operator:
    """
    Récupération de l'opérateur courant
    """
    if current_op.disabled:
        raise HTTPException(status_code=400, detail="Opérateur désactivé.")
    return current_op

def create_token(data: dict, expires_delta: timedelta):
    """
    Création d'un token
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + expires_delta
    
    # mettre à jour le data à encoder
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

   