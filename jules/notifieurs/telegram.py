"""Notifieur 'telegram' : message au parent via un bot Telegram (API HTTP officielle).

Jeton et identifiant de conversation lus dans des variables d'environnement
(noms reglables dans config.yaml), jamais ecrits dans la config.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from jules.config import Config

LIMITE = 4000  # Telegram refuse au-dela de 4096 caracteres


class Brique:
    def __init__(self, config: Config, reglages: dict[str, Any]) -> None:
        nom_jeton = str(reglages.get("token_env", "JULES_TELEGRAM_TOKEN"))
        nom_chat = str(reglages.get("chat_id_env", "JULES_TELEGRAM_CHAT_ID"))
        self.jeton = os.environ.get(nom_jeton, "")
        self.chat_id = os.environ.get(nom_chat, "")
        if not self.jeton or not self.chat_id:
            raise RuntimeError(f"Notifieur telegram : variables {nom_jeton} / {nom_chat} absentes")

    def envoyer(self, sujet: str, texte: str, urgent: bool = False) -> None:
        prefixe = "URGENT - " if urgent else ""
        corps = f"{prefixe}{sujet}\n\n{texte}"[:LIMITE]
        reponse = httpx.post(
            f"https://api.telegram.org/bot{self.jeton}/sendMessage",
            json={"chat_id": self.chat_id, "text": corps, "disable_notification": not urgent},
            timeout=20,
        )
        reponse.raise_for_status()
