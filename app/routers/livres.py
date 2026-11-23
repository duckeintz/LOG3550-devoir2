from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, or_, select

from app.database import get_session
from app.models import Categorie, Livre
from app.schemas import LivreCreate, LivreRead, LivreUpdate

router = APIRouter(prefix="/livres", tags=["Livres"])


def trouver_livre(session: Session, livre_id: int) -> Livre:
    livre = session.get(Livre, livre_id)
    if livre is None:
        raise HTTPException(status_code=404, detail="Livre introuvable")
    return livre


def enregistrer(session: Session, livre: Livre) -> Livre:
    session.add(livre)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Un livre avec cet ISBN existe déjà")
    session.refresh(livre)
    return livre


@router.get("", response_model=list[LivreRead], summary="Lister les livres",
            description="Filtres : q (titre ou auteur), categorie, disponible. Pagination : skip et limit (max 100).")
def lister_livres(
    q: Optional[str] = None,
    categorie: Optional[Categorie] = None,
    disponible: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    requete = select(Livre)
    if q:
        motif = f"%{q}%"
        requete = requete.where(or_(col(Livre.titre).ilike(motif), col(Livre.auteur).ilike(motif)))
    if categorie is not None:
        requete = requete.where(Livre.categorie == categorie)
    if disponible is not None:
        requete = requete.where(Livre.disponible == disponible)
    return session.exec(requete.order_by(Livre.id).offset(skip).limit(limit)).all()


@router.get("/{livre_id}", response_model=LivreRead, summary="Lire un livre")
def lire_livre(livre_id: int, session: Session = Depends(get_session)):
    return trouver_livre(session, livre_id)


@router.post("", response_model=LivreRead, status_code=201, summary="Créer un livre")
def creer_livre(livre: LivreCreate, response: Response, session: Session = Depends(get_session)):
    nouveau = enregistrer(session, Livre(**livre.model_dump()))
    response.headers["Location"] = f"/livres/{nouveau.id}"
    return nouveau


@router.put("/{livre_id}", response_model=LivreRead, summary="Remplacer un livre")
def remplacer_livre(livre_id: int, donnees: LivreCreate, session: Session = Depends(get_session)):
    livre = trouver_livre(session, livre_id)
    for champ, valeur in donnees.model_dump().items():
        setattr(livre, champ, valeur)
    return enregistrer(session, livre)


@router.patch("/{livre_id}", response_model=LivreRead, summary="Modifier partiellement un livre")
def modifier_livre(livre_id: int, donnees: LivreUpdate, session: Session = Depends(get_session)):
    livre = trouver_livre(session, livre_id)
    for champ, valeur in donnees.model_dump(exclude_unset=True).items():
        setattr(livre, champ, valeur)
    return enregistrer(session, livre)


@router.delete("/{livre_id}", status_code=204, summary="Supprimer un livre")
def supprimer_livre(livre_id: int, session: Session = Depends(get_session)):
    livre = trouver_livre(session, livre_id)
    session.delete(livre)
    session.commit()