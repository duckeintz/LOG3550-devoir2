# LOG3550 – Devoir 2 : Backend FastAPI (API Bibliothèque)

Auteur : [ANTOINE Heintz-Duckenson]
Dépôt Git : [lien de votre dépôt]

API REST (FastAPI + SQLModel + SQLite) qui gère les livres de la bibliothèque du devoir 1.

## Installation
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Lancer l'API
```
uvicorn app.main:app --reload
```
- API : http://127.0.0.1:8000
- Documentation Swagger : http://127.0.0.1:8000/docs
- Au premier démarrage, la base `bibliotheque.db` est créée et 8 livres de départ sont chargés.

## Lancer les tests
```
pytest -v
```
Les tests utilisent une base SQLite en mémoire, séparée de la vraie base.

## Lancer le frontend
Dans un autre terminal :
```
python -m http.server 5500 --directory frontend
```
Puis ouvrir http://127.0.0.1:5500 (seule origine autorisée par le CORS). L'API doit être démarrée.

## Points d'accès
| Méthode | Route | Rôle |
|---|---|---|
| GET | /sante | État de l'API |
| GET | /livres | Liste (filtres q, categorie, disponible ; pagination skip, limit ≤ 100) |
| GET | /livres/{id} | Lire un livre (404 si absent) |
| POST | /livres | Créer (201 + en-tête Location, 409 si ISBN en double) |
| PUT | /livres/{id} | Remplacement complet |
| PATCH | /livres/{id} | Modification partielle |
| DELETE | /livres/{id} | Suppression (204) |

## Réponses aux questions

### FastAPI, Uvicorn, Pydantic et séparation modèle / schémas
- **FastAPI** est le framework Python qui définit les routes, lit les requêtes et génère la documentation `/docs`.
- **Uvicorn** est le serveur qui reçoit les requêtes HTTP et les transmet à FastAPI.
- **Pydantic** valide et convertit les données (types, longueurs, énumérations) et produit les erreurs 422.
- Le **modèle de base** (`Livre`) décrit le stockage : id, unicité de l'ISBN.
- Les **schémas** décrivent ce que l'API reçoit et renvoie : le client ne fournit jamais l'`id`, et tous les champs sont facultatifs en modification. On sépare les deux pour ne pas exposer ni laisser modifier des champs internes.

### Format d'une erreur 422
La réponse est un JSON `{"detail": [ ... ]}` : une liste d'erreurs. Chaque erreur contient `loc` (où : `["body", "titre"]`), `msg` (message), `type` (règle violée, par exemple `string_too_short`), `input` (valeur reçue) et `ctx` (contrainte, par exemple `min_length: 2`). Le code 422 signifie que la requête est bien formée mais que les données sont invalides.

### PUT et PATCH, idempotence
- **PUT** remplace le livre en entier : il faut envoyer tous les champs.
- **PATCH** ne modifie que les champs envoyés.
- **PUT et DELETE sont idempotents** : répéter la même requête laisse le serveur dans le même état (le même livre, ou le livre déjà supprimé).
- **POST ne l'est pas** : chaque appel crée une nouvelle ressource, donc deux POST identiques créent deux livres (ou donnent un 409 si l'ISBN est unique).

## Captures d'écran
1. `01_swagger.png` : page /docs avec tous les points d'accès
2. `02_erreur_422_a.png` et `03_erreur_422_b.png` : deux erreurs 422
3. `04_pytest.png` : `pytest -v`, tous les tests au vert
4. `05_catalogue_api.png` : catalogue alimenté par l'API
5. `06_reseau_post.png` : requête POST dans l'onglet Réseau

## Sources et outils d'assistance
J'ai utilisé l'assistant Claude (Anthropic) pour être guidé pas à pas dans la réalisation du devoir, ainsi que la documentation officielle de FastAPI et de SQLModel.