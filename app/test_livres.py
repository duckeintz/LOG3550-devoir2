import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.database import get_session
from app.main import app

LIVRE = {
    "titre": "Gouverneurs de la rosée",
    "auteur": "Jacques Roumain",
    "annee": 1944,
    "categorie": "roman",
}


@pytest.fixture(name="client")
def client_fixture():
    # Base de test séparée : SQLite en mémoire
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def get_session_test():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_session_test
    yield TestClient(app)
    app.dependency_overrides.clear()


def creer(client, **changements):
    return client.post("/livres", json={**LIVRE, **changements})


def test_sante(client):
    reponse = client.get("/sante")
    assert reponse.status_code == 200
    assert reponse.json() == {"statut": "ok"}


def test_creation(client):
    reponse = creer(client)
    assert reponse.status_code == 201
    livre = reponse.json()
    assert livre["id"] == 1
    assert livre["disponible"] is True
    assert reponse.headers["location"] == f"/livres/{livre['id']}"


def test_lecture(client):
    livre_id = creer(client).json()["id"]
    reponse = client.get(f"/livres/{livre_id}")
    assert reponse.status_code == 200
    assert reponse.json()["titre"] == "Gouverneurs de la rosée"


def test_liste_filtree(client):
    creer(client)
    creer(client, titre="Cosmos", auteur="Carl Sagan", annee=1980, categorie="science")
    creer(client, titre="Sapiens", auteur="Yuval Noah Harari", annee=2011, categorie="histoire")

    assert len(client.get("/livres").json()) == 3
    sciences = client.get("/livres", params={"categorie": "science"}).json()
    assert len(sciences) == 1 and sciences[0]["titre"] == "Cosmos"
    recherche = client.get("/livres", params={"q": "roumain"}).json()
    assert len(recherche) == 1
    page = client.get("/livres", params={"skip": 1, "limit": 1}).json()
    assert len(page) == 1


def test_remplacement_put(client):
    livre_id = creer(client).json()["id"]
    nouveau = {**LIVRE, "titre": "Nouveau titre", "annee": 1950, "categorie": "histoire"}
    reponse = client.put(f"/livres/{livre_id}", json=nouveau)
    assert reponse.status_code == 200
    assert reponse.json()["titre"] == "Nouveau titre"
    assert reponse.json()["categorie"] == "histoire"


def test_modification_partielle_patch(client):
    livre_id = creer(client).json()["id"]
    reponse = client.patch(f"/livres/{livre_id}", json={"disponible": False})
    assert reponse.status_code == 200
    assert reponse.json()["disponible"] is False
    assert reponse.json()["titre"] == "Gouverneurs de la rosée"


def test_suppression(client):
    livre_id = creer(client).json()["id"]
    assert client.delete(f"/livres/{livre_id}").status_code == 204
    assert client.get(f"/livres/{livre_id}").status_code == 404


def test_livre_introuvable_404(client):
    reponse = client.get("/livres/999")
    assert reponse.status_code == 404
    assert reponse.json()["detail"] == "Livre introuvable"


def test_validation_titre_et_annee_422(client):
    assert creer(client, titre="A").status_code == 422
    assert creer(client, annee=1200).status_code == 422
    assert creer(client, categorie="cuisine").status_code == 422
    assert creer(client, isbn="123").status_code == 422


def test_isbn_en_double_409(client):
    assert creer(client, isbn="1234567890").status_code == 201
    reponse = creer(client, titre="Autre livre", isbn="1234567890")
    assert reponse.status_code == 409