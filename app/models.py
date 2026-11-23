from enum import Enum
from typing import Optional
from sqlmodel import SQLModel, Field

class Categorie(str, Enum):
    roman = "roman"
    science = "science"
    histoire = "histoire"
    informatique = "informatique"
    autre = "autre"

class Livre(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    titre: str
    auteur: str
    annee: int
    categorie: Categorie
    isbn: Optional[str] = Field(default=None, unique=True, index=True)
    disponible: bool = True