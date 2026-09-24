"""Moteur 'openai_compatible' : tout service qui parle le format « chat completions ».

Un seul moteur pour de nombreux fournisseurs, il suffit de changer l'adresse :
    Ollama (local, gratuit)   url: http://localhost:11434/v1     cle_env: (vide)
    Mistral AI                url: https://api.mistral.ai/v1     cle_env: MISTRAL_API_KEY
    OpenAI                    url: https://api.openai.com/v1     cle_env: OPENAI_API_KEY
    LM Studio, vLLM, llama.cpp, OpenRouter... : meme principe.

Reglages (section `llm` de la configuration) :
    backend: openai_compatible
    url: ...
    cle_env: ...                      # vide pour un modele local sans cle
    modeles: {principal: ..., rapide: ...}
    images: true                      # false si le modele ne lit pas les photos
    parametres: {}                    # champs ajoutes tels quels a la requete (ex. reasoning_effort: none)
"""

from __future__ import annotations

from typing import Any

import httpx

from jules.llm.base import TEXTE_PHOTO_SEULE, ErreurLLM, Tour, cle_api, image_base64, nettoyer, nom_modele, type_media

NOTE_SANS_IMAGES = (
    "(une photo a été envoyée, mais ce modèle ne sait pas lire les images : demande de recopier l'énoncé)"
)


def contenu_tour(tour: Tour, images: bool) -> str | list[dict[str, Any]]:
    if not tour.images:
        return tour.texte or TEXTE_PHOTO_SEULE
    if not images:
        return f"{tour.texte}\n{NOTE_SANS_IMAGES}".strip()
    parties: list[dict[str, Any]] = [
        {"type": "image_url", "image_url": {"url": f"data:{type_media(img)};base64,{image_base64(img)}"}}
        for img in tour.images
    ]
    parties.append({"type": "text", "text": tour.texte or TEXTE_PHOTO_SEULE})
    return parties


def corps_requete(
    systeme: str,
    tours: list[Tour],
    modele: str,
    max_tokens: int,
    images: bool,
    parametres: dict[str, Any] | None = None,
) -> dict[str, Any]:
    messages: list[dict[str, Any]] = [{"role": "system", "content": systeme}]
    messages += [{"role": t.role, "content": contenu_tour(t, images)} for t in tours]
    corps: dict[str, Any] = dict(parametres or {})
    corps.update({"model": modele, "messages": messages, "max_tokens": max_tokens})
    return corps


def lire_reponse(donnees: dict[str, Any]) -> str:
    choix = donnees.get("choices") or []
    if not choix:
        raise ErreurLLM(f"Reponse sans contenu : {str(donnees)[:300]}")
    return str((choix[0].get("message") or {}).get("content") or "")


class Brique:
    def __init__(self, reglages: dict[str, Any], client: httpx.Client | None = None) -> None:
        self.reglages = reglages
        url = str(reglages.get("url") or "").rstrip("/")
        if not url:
            raise ErreurLLM("llm.url manquant (ex. http://localhost:11434/v1 pour Ollama)")
        self.url = url + "/chat/completions"
        self.cle = cle_api(reglages, obligatoire=bool(reglages.get("cle_env")))
        nom_modele(reglages, "principal")
        self.images = bool(reglages.get("images", True))
        self.max_tokens = int(reglages.get("max_tokens", 2000))
        self.parametres = dict(reglages.get("parametres") or {})
        self.client = client or httpx.Client(timeout=float(reglages.get("delai_s", 180)))

    def repondre(self, systeme: str, tours: list[Tour], modele: str = "principal") -> str:
        nom = nom_modele(self.reglages, modele)
        corps = corps_requete(systeme, tours, nom, self.max_tokens, self.images, self.parametres)
        entetes = {"content-type": "application/json"}
        if self.cle:
            entetes["authorization"] = f"Bearer {self.cle}"
        try:
            reponse = self.client.post(self.url, json=corps, headers=entetes)
        except httpx.HTTPError as err:
            raise ErreurLLM(f"Service IA injoignable ({self.url}) : {err}") from err
        if reponse.status_code != 200:
            raise ErreurLLM(f"Service IA : erreur {reponse.status_code} : {reponse.text[:300]}")
        return nettoyer(lire_reponse(reponse.json()))
