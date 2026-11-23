from sqlmodel import SQLModel, Session, create_engine, select

from app.models import Categorie, Livre

engine = create_engine(
    "sqlite:///./bibliotheque.db",
    connect_args={"check_same_thread": False},
)

LIVRES_DEPART = [
    {"titre": "Gouverneurs de la rosée", "auteur": "Jacques Roumain", "annee": 1944, "categorie": Categorie.roman},
    {"titre": "Compère Général Soleil", "auteur": "Jacques Stephen Alexis", "annee": 1955, "categorie": Categorie.roman},
    {"titre": "Le Petit Prince", "auteur": "Antoine de Saint-Exupéry", "annee": 1943, "categorie": Categorie.roman},
    {"titre": "Une brève histoire du temps", "auteur": "Stephen Hawking", "annee": 1988, "categorie": Categorie.science},
    {"titre": "Cosmos", "auteur": "Carl Sagan", "annee": 1980, "categorie": Categorie.science},
    {"titre": "Sapiens", "auteur": "Yuval Noah Harari", "annee": 2011, "categorie": Categorie.histoire},
    {"titre": "Clean Code", "auteur": "Robert C. Martin", "annee": 2008, "categorie": Categorie.informatique},
    {"titre": "Introduction to Algorithms", "auteur": "Thomas H. Cormen", "annee": 2009, "categorie": Categorie.informatique},
]


def creer_tables():
    SQLModel.metadata.create_all(engine)


def charger_donnees_depart():
    with Session(engine) as session:
        if session.exec(select(Livre)).first() is None:
            for donnees in LIVRES_DEPART:
                session.add(Livre(**donnees))
            session.commit()


def get_session():
    with Session(engine) as session:
        yield session