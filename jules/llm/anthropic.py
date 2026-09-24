"""Moteur 'anthropic' : API Messages d'Anthropic (modeles Claude), par simple requete HTTP.

Reglages (section `llm` de la configuration) :
    backend: anthropic
    cle_env: ANTHROPIC_API_KEY        # nom de la variable qui contient la cle (.env)
    modeles: {principal: ..., rapide: ...}
    url: https://api.anthropic.com   # optionnel
"""

from __future__ import annotations

from typing import Any

import httpx

from jules.llm.base import TEXTE_PHOTO_SEULE, ErreurLLM, Tour, cle_api, image_base64, nettoyer, nom_modele, type_media

URL_DEFAUT = "https://api.anthropic.com"
VERSION_API = "2023-06-01"


def blocs_tour(tour: Tour) -> list[dict[str, Any]]:
    blocs: list[dict[str, Any]] = [
        {"type": "image", "source": {"type": "base64", "media_type": type_media(img), "data": image_base64(img)}}
        for img in tour.images
    ]
    blocs.append({"type": "text", "text": tour.texte or TEXTE_PHOTO_SEULE})
    return blocs


def corps_requete(systeme: str, tours: list[Tour], modele: str, max_tokens: int) -> dict[str, Any]:
    return {
        "model": modele,
        "max_tokens": max_tokens,
        "system": systeme,
        "messages": [{"role": t.role, "content": blocs_tour(t)} for t in tours],
    }


def lire_reponse(donnees: dict[str, Any]) -> str:
    return "".join(b.get("text", "") for b in donnees.get("content") or [] if b.get("type") == "text")


class Brique:
    def __init__(self, reglages: dict[str, Any], client: httpx.Client | None = None) -> None:
        self.reglages = reglages
        self.cle = cle_api(reglages)
        nom_modele(reglages, "principal")  # echoue tout de suite si la config est incomplete
        self.url = str(reglages.get("url") or URL_DEFAUT).rstrip("/") + "/v1/messages"
        self.max_tokens = int(reglages.get("max_tokens", 2000))
        self.client = client or httpx.Client(timeout=float(reglages.get("delai_s", 120)))

    def repondre(self, systeme: str, tours: list[Tour], modele: str = "principal") -> str:
        corps = corps_requete(systeme, tours, nom_modele(self.reglages, modele), self.max_tokens)
        entetes = {"x-api-key": self.cle, "anthropic-version": VERSION_API, "content-type": "application/json"}
        try:
            reponse = self.client.post(self.url, json=corps, headers=entetes)
        except httpx.HTTPError as err:
            raise ErreurLLM(f"Anthropic injoignable : {err}") from err
        if reponse.status_code != 200:
            raise ErreurLLM(f"Anthropic : erreur {reponse.status_code} : {reponse.text[:300]}")
        return nettoyer(lire_reponse(reponse.json()))
