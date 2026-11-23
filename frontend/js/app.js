"use strict";

const API_URL = "http://127.0.0.1:8000";
const ANNEE_MIN = 1450;
const ANNEE_COURANTE = new Date().getFullYear();

const dom = {
  recherche: document.getElementById("recherche"),
  categorie: document.getElementById("filtre-categorie"),
  disponibles: document.getElementById("filtre-disponibles"),
  tri: document.getElementById("tri"),
  compteur: document.getElementById("compteur"),
  vide: document.getElementById("message-vide"),
  liste: document.getElementById("liste-livres"),
  modele: document.getElementById("modele-carte"),
  reinit: document.getElementById("btn-reinitialiser"),
  form: document.getElementById("form-ajout"),
  confirmation: document.getElementById("message-ajout")
};

let livres = [];

/* ---------- Message d'état (chargement / erreur) ---------- */

const statut = document.createElement("p");
statut.setAttribute("role", "status");
statut.setAttribute("aria-live", "polite");
statut.style.fontWeight = "bold";
statut.hidden = true;
dom.liste.before(statut);

function afficherStatut(message, estErreur = false) {
  statut.textContent = message;
  statut.style.color = estErreur ? "#b00020" : "inherit";
  statut.hidden = message === "";
}

/* ---------- Appels à l'API ---------- */

async function appelApi(chemin, options = {}) {
  const entetes = options.body ? { "Content-Type": "application/json" } : {};
  let reponse;
  try {
    reponse = await fetch(`${API_URL}${chemin}`, { ...options, headers: entetes });
  } catch (erreur) {
    throw new Error("Impossible de joindre l'API. Vérifiez qu'elle est démarrée (uvicorn).");
  }

  if (!reponse.ok) {
    let message = `Erreur ${reponse.status}`;
    try {
      const corps = await reponse.json();
      if (typeof corps.detail === "string") {
        message = corps.detail;
      } else if (Array.isArray(corps.detail)) {
        message = corps.detail.map(e => e.msg).join(" ; ");
      }
    } catch (erreur) {
      // corps non JSON : on garde le message par défaut
    }
    throw new Error(message);
  }
  return reponse.status === 204 ? null : reponse.json();
}

async function chargerLivres() {
  afficherStatut("Chargement des livres…");
  try {
    livres = await appelApi("/livres?limit=100");
    afficherStatut("");
  } catch (erreur) {
    livres = [];
    afficherStatut(erreur.message, true);
  }
  afficher();
}

/* ---------- Recherche, filtres, tri ---------- */

// Minuscules et sans accents : « Éloquent » et « eloquent » deviennent identiques
function normaliser(texte) {
  return texte.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();
}

function filtrer(liste) {
  const requete = normaliser(dom.recherche.value);
  const categorie = normaliser(dom.categorie.value);
  const seulementDispo = dom.disponibles.checked;

  return liste.filter(livre =>
    (!requete || normaliser(livre.titre).includes(requete) || normaliser(livre.auteur).includes(requete)) &&
    (!categorie || normaliser(livre.categorie) === categorie) &&
    (!seulementDispo || livre.disponible)
  );
}

function trier(liste) {
  const [champ, sens] = dom.tri.value.split("-");
  const facteur = sens === "desc" ? -1 : 1;
  return [...liste].sort((a, b) =>
    champ === "annee"
      ? (a.annee - b.annee) * facteur
      : a.titre.localeCompare(b.titre, "fr", { sensitivity: "base" }) * facteur
  );
}

/* ---------- Affichage ---------- */

function creerCarte(livre) {
  const carte = dom.modele.content.firstElementChild.cloneNode(true);
  const etiquette = carte.querySelector(".etiquette");

  carte.querySelector(".carte__titre").textContent = livre.titre;
  carte.querySelector(".carte__auteur").textContent = livre.auteur;
  carte.querySelector(".carte__meta").textContent = `${livre.annee} · ${livre.categorie}`;

  etiquette.textContent = livre.disponible ? "Disponible" : "Emprunté";
  etiquette.classList.add(livre.disponible ? "etiquette--dispo" : "etiquette--emprunte");

  carte.querySelector('[data-action="emprunter"]').disabled = !livre.disponible;
  carte.querySelector('[data-action="rendre"]').disabled = livre.disponible;
  carte.querySelectorAll("button").forEach(bouton => { bouton.dataset.id = livre.id; });
  return carte;
}

function afficher() {
  const visibles = trier(filtrer(livres));
  dom.liste.replaceChildren(...visibles.map(creerCarte));
  dom.vide.hidden = visibles.length > 0;
  dom.compteur.textContent = visibles.length === 0
    ? "Aucun résultat"
    : `${visibles.length} livre${visibles.length > 1 ? "s" : ""} sur ${livres.length}`;
}

/* ---------- Actions sur les livres (via l'API) ---------- */

async function changerDisponibilite(id, disponible) {
  try {
    const misAJour = await appelApi(`/livres/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ disponible })
    });
    livres = livres.map(l => (l.id === id ? misAJour : l));
    afficherStatut("");
    afficher();
  } catch (erreur) {
    afficherStatut(erreur.message, true);
  }
}

async function supprimer(id) {
  const livre = livres.find(l => l.id === id);
  if (!livre || !confirm(`Supprimer « ${livre.titre} » du catalogue ?`)) return;
  try {
    await appelApi(`/livres/${id}`, { method: "DELETE" });
    livres = livres.filter(l => l.id !== id);
    afficherStatut("");
    afficher();
  } catch (erreur) {
    afficherStatut(erreur.message, true);
  }
}

// Un seul écouteur sur la liste pour tous les boutons des cartes (délégation d'événements)
function gererClicCarte(evenement) {
  const bouton = evenement.target.closest("button[data-action]");
  if (!bouton) return;
  const id = Number(bouton.dataset.id);
  const actions = {
    emprunter: () => changerDisponibilite(id, false),
    rendre: () => changerDisponibilite(id, true),
    supprimer: () => supprimer(id)
  };
  actions[bouton.dataset.action]();
}

/* ---------- Formulaire : validation et ajout ---------- */

const REGLES = {
  titre: v => v.trim().length >= 2 ? "" : "Saisissez un titre d'au moins 2 caractères.",
  auteur: v => v.trim().length >= 2 ? "" : "Saisissez un auteur d'au moins 2 caractères.",
  annee: v => {
    const n = Number(v);
    const valide = v !== "" && Number.isInteger(n) && n >= ANNEE_MIN && n <= ANNEE_COURANTE;
    return valide ? "" : `Saisissez une année entre ${ANNEE_MIN} et ${ANNEE_COURANTE}.`;
  },
  categorie: v => v ? "" : "Choisissez une catégorie."
};

// Affiche (ou efface) l'erreur sous le champ ; aria-describedby + aria-live la font annoncer
function validerChamp(nom) {
  const champ = dom.form.elements[nom];
  const message = REGLES[nom](champ.value);
  document.getElementById(`erreur-${nom}`).textContent = message;
  champ.setAttribute("aria-invalid", message ? "true" : "false");
  return message === "";
}

function effacerErreurs() {
  Object.keys(REGLES).forEach(nom => {
    document.getElementById(`erreur-${nom}`).textContent = "";
    dom.form.elements[nom].removeAttribute("aria-invalid");
  });
}

async function ajouterLivre(evenement) {
  evenement.preventDefault();
  dom.confirmation.textContent = "";

  const resultats = Object.keys(REGLES).map(validerChamp); // valide tous les champs d'un coup
  if (resultats.includes(false)) {
    dom.form.querySelector('[aria-invalid="true"]').focus();
    return;
  }

  const f = dom.form.elements;
  const nouveauLivre = {
    titre: f.titre.value.trim(),
    auteur: f.auteur.value.trim(),
    annee: Number(f.annee.value),
    categorie: f.categorie.value.toLowerCase(),
    disponible: f.disponible.checked
  };

  try {
    const cree = await appelApi("/livres", {
      method: "POST",
      body: JSON.stringify(nouveauLivre)
    });
    livres.push(cree);
    afficherStatut("");
    afficher();
    dom.form.reset();
    effacerErreurs();
    dom.confirmation.textContent = "Livre ajouté au catalogue.";
  } catch (erreur) {
    afficherStatut(erreur.message, true);
  }
}

/* ---------- Démarrage ---------- */

function init() {
  dom.form.elements.annee.max = ANNEE_COURANTE;
  dom.form.elements.annee.min = ANNEE_MIN;

  // Les données viennent maintenant de l'API : plus de réinitialisation locale
  dom.reinit.style.display = "none";

  [dom.recherche, dom.categorie, dom.disponibles, dom.tri]
    .forEach(element => element.addEventListener("input", afficher));
  dom.liste.addEventListener("click", gererClicCarte);
  dom.form.addEventListener("submit", ajouterLivre);
  Object.keys(REGLES).forEach(nom =>
    dom.form.elements[nom].addEventListener("blur", () => validerChamp(nom))
  );

  chargerLivres();
}

init();