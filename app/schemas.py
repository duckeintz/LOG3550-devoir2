from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models import Categorie


def verifier_annee(v):
    if v is not None and not (1450 <= v <= date.today().year):
        raise ValueError(f"L'année doit être entre 1450 et {date.today().year}")
    return v


class LivreCreate(BaseModel):
    titre: str = Field(min_length=2, max_length=200, examples=["Gouverneurs de la rosée"])
    auteur: str = Field(min_length=2, max_length=200, examples=["Jacques Roumain"])
    annee: int = Field(examples=[1944])
    categorie: Categorie = Field(examples=["roman"])
    isbn: Optional[str] = Field(default=None, pattern=r"^(\d{10}|\d{13})$", examples=["9782070360000"])
    disponible: bool = True

    _check_annee = field_validator("annee")(verifier_annee)


class LivreUpdate(BaseModel):
    titre: Optional[str] = Field(default=None, min_length=2, max_length=200)
    auteur: Optional[str] = Field(default=None, min_length=2, max_length=200)
    annee: Optional[int] = None
    categorie: Optional[Categorie] = None
    isbn: Optional[str] = Field(default=None, pattern=r"^(\d{10}|\d{13})$")
    disponible: Optional[bool] = None

    _check_annee = field_validator("annee")(verifier_annee)


class LivreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titre: str
    auteur: str
    annee: int
    categorie: Categorie
    isbn: Optional[str] = None
    disponible: bool