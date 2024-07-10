from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date
from datetime import datetime
from sqlalchemy.orm import relationship

from .database import Base


class Etudiant(Base):
    __tablename__ = "etudiants"

    id = Column(Integer, primary_key=True)
    nom = Column(String(100))
    prenom = Column(String(100))
    dob = Column(Date)
    cin = Column(String(20), unique=True, nullable=True)
    cin_date = Column(Date, nullable=True)
    tel = Column(String(20))
    email = Column(String(50), unique=True)
    matricule = Column(String(10), index=True)
    adresse = Column(String(100))
    parcours = Column(String(20))
    niveau = Column(String(4))
    annee_univ = Column(String(30))

    activites = relationship("Journal", back_populates="etudiant")
    qrcode = relationship("QR_Code", back_populates="owner")


class Operator(Base):
    __tablename__ = "Operators"

    id = Column(Integer, primary_key=True)
    nom = Column(String(100))
    hashed_password = Column(String(100))
    refresh_token = Column(String(255), nullable=True)
    disabled = Column(Boolean, default=False)

    activites = relationship("Journal", back_populates="effectue_par")


class Journal(Base):
    __tablename__ = "journals"

    id = Column(Integer, primary_key=True)
    operation = Column(String(200))
    id_operator = Column(Integer, ForeignKey("Operators.id", ondelete="CASCADE", onupdate="CASCADE"))
    im_etudiant = Column(String(20), ForeignKey("etudiants.matricule", ondelete="CASCADE", onupdate="CASCADE"))
    date = Column(Date, default=datetime.now())

    effectue_par = relationship("Operator", back_populates="activites")
    etudiant = relationship("Etudiant", back_populates="activites")


class QR_Code(Base):
    __tablename__ = "qrcode"

    id = Column(Integer, primary_key=True)
    id_etudiant = Column(Integer, ForeignKey("etudiants.id", ondelete="CASCADE", onupdate="CASCADE"))
    expire_date = Column(Date)
    is_valid = Column(Boolean, default=True)
    data = Column(String(255))
    created_at = Column(Date, default=datetime.now())

    owner = relationship("Etudiant", back_populates="qrcode")