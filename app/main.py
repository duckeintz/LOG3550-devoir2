from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import creer_tables, charger_donnees_depart
from app import models  # noqa: F401
from app.routers import livres

ORIGINES_AUTORISEES = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    creer_tables()
    charger_donnees_depart()
    yield


app = FastAPI(title="API Bibliothèque", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINES_AUTORISEES,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(livres.router)


@app.get("/sante")
def sante():
    return {"statut": "ok"}