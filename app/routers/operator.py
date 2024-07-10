from typing import Any, Union
from datetime import datetime, timedelta

import jwt
import os
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing_extensions import Annotated
from sqlalchemy.orm import Session
from jose import JWTError

from app.utils.auth import authenticate_operator, create_token, get_current_active_operator

from..helpers.database import SessionLocal
from ..services import operator as operator_service
from app.helpers import schemas



router = APIRouter(tags=["operator"])
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


@router.post("/token", response_model=schemas.Token)
def login_for_access_token(response: Response, 
                           db: Session = Depends(get_db), 
                           form_data: OAuth2PasswordRequestForm = Depends()
                           ):
    """
    login pour avoir un token d'acces
    """
    operator = authenticate_operator(form_data.username, form_data.password, db)
    if not operator:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES) # type: ignore
    access_token = create_token(
        data={"sub": operator.nom}, expires_delta=access_token_expires
    )
    
    # Créer un refresh token et sauvegarder dans la base de donnée
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS) # type: ignore
    refresh_token = create_token(
        data={"sub": operator.nom}, expires_delta=refresh_token_expires
    )
    
    # Mettre à jour le refresh token de l'Operator
    operator_service.update(db, operator.__dict__["id"], {"refresh_token": refresh_token})
    
    response.set_cookie(
        key="refresh_token", 
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite='strict'
    )
     
    return schemas.Token(access_token=access_token, token_type="bearer")


@router.post("/refresh_token")
def refresh_token(request: Request, db: Session = Depends(get_db)):
    """
    rafraîchir le token d'accès
    """
    refresh_token = request.cookies.get("refresh_token")
    # S'il n'y a pas de refresh token, on retourne une erreur 401
    if refresh_token is None:
        raise HTTPException(
            status_code=401,
            detail="Refresh token non fourni",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM]) # type: ignore
        operator_name: str = payload.get("sub")
        # S'il m'y a pas de operator name dans le refresh token, on retourne une erreur
        if operator_name is None:
            raise HTTPException(
                status_code=401, 
                detail="Refresh token non valid"
            )
        
        # Récuperer l'operateur de la BD
        operator = operator_service.get_operator(db, operator_name)
        if operator.refresh_token != refresh_token: # type: ignore
            raise HTTPException(
                status_code=401, 
                detail="Refresh token non valid"
            )
        
        # mettre à jour l'access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES) # type: ignore
        access_token = create_token(
            data={"sub": operator.nom}, expires_delta=access_token_expires
        )
        
        return schemas.Token(access_token=access_token, token_type="bearer")
    except JWTError:
        raise HTTPException(
            status_code=401, 
            detail="Refresh token non valid"
        )        

@router.get("/operator/me", response_model=None)
async def read_operator_me(
    current_op: Annotated[schemas.Operator, Depends(get_current_active_operator)]
    ):
        
    return current_op


@router.post("/operator")
async def create_operator(
    operator: schemas.OperatorCreate, 
    db: Session = Depends(get_db)
    ):
    db_operator = operator_service.create(db, operator)
    return db_operator


@router.post("/logout", response_model=Any)
async def logout(
    current_op: Annotated[schemas.Operator, Depends(get_current_active_operator)],
    db: Session = Depends(get_db)
    ):
    operator_service.update(db, current_op.id, {"refresh_token": None})
    return {"message": "Vous avez été déconnecté"}
    