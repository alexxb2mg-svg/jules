"""Moteur Mistral du banc d'essai : l'API Mistral (format chat completions), journalisee comme MoteurCLI.

Seul Jules passe par ce moteur (reponses et taches de fond) ; l'eleve simule et le juge restent sur
MoteurCLI pour que les comparaisons entre modeles se fassent avec le meme eleve et le meme juge.
Les jetons sont ceux renvoyes par l'API (pas de socle a retirer). Cle : variable MISTRAL_API_KEY.
"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx
from moteur_cli import Journal, role_appel

from jules.llm.base import ErreurLLM, Tour, nettoyer
from jules.llm.openai_compatible import corps_requete, lire_reponse

URL = "https://api.mistral.ai/v1/chat/completions"
# Tarifs publics en $ par million de jetons (entree, sortie), releves le 29/09/2026.
TARIFS_MISTRAL = {
    "ministral-3b": (0.10, 0.10),
    "ministral-8b": (0.15, 0.15),
    "ministral-14b": (0.20, 0.20),
    "mistral-small": (0.15, 0.60),
    "mistral-large": (0.50, 1.50),
    "codestral": (0.30, 0.90),
}


def est_mistral(alias: str) -> bool:
    return alias.startswith(("ministral", "mistral", "codestral", "magistral"))


class MoteurMistral:
    """Contrat MoteurLLM de Jules (repondre), un appel HTTP par demande, jetons journalises."""

    def __init__(self, modeles: dict[str, str], journal: Journal, delai_s: float = 180) -> None:
        cle = os.environ.get("MISTRAL_API_KEY", "").strip()
        if not cle:
            raise ErreurLLM("MISTRAL_API_KEY absente")
        self.entetes = {"authorization": f"Bearer {cle}", "content-type": "application/json"}
        self.modeles = modeles
        self.journal = journal
        self.client = httpx.Client(timeout=delai_s)

    def repondre(self, systeme: str, tours: list[Tour], modele: str = "principal") -> str:
        alias = self.modeles.get(modele) or self.modeles["principal"]
        corps = corps_requete(systeme, tours, alias, 2000, images=False)
        debut = time.perf_counter()
        donnees = self._poster(corps)
        usage = donnees.get("usage") or {}
        self.journal.ajouter(
            {
                "role": role_appel(systeme, modele),
                "logique": modele,
                "alias": alias,
                "modele": str(donnees.get("model") or alias),
                "entree": int(usage.get("prompt_tokens", 0)),
                "entree_cache": int((usage.get("prompt_tokens_details") or {}).get("cached_tokens", 0)),
                "sortie": int(usage.get("completion_tokens", 0)),
                "reflexion": 0,
                "duree_s": round(time.perf_counter() - debut, 2),
                "duree_api_s": 0.0,
                "car_systeme": len(systeme),
                "car_message": sum(len(t.texte or "") for t in tours),
            }
        )
        return nettoyer(lire_reponse(donnees))

    def _poster(self, corps: dict[str, Any]) -> dict[str, Any]:
        attentes = (5, 15, 30, 60, 90)
        for essai in range(len(attentes) + 1):
            try:
                r = self.client.post(URL, json=corps, headers=self.entetes)
            except httpx.HTTPError as err:
                if essai == len(attentes):
                    raise ErreurLLM(f"Mistral injoignable : {err}") from err
                time.sleep(attentes[essai])
                continue
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 500, 502, 503) and essai < len(attentes):
                time.sleep(attentes[essai])
                continue
            raise ErreurLLM(f"Mistral : erreur {r.status_code} : {r.text[:300]}")
        raise ErreurLLM("inatteignable")
