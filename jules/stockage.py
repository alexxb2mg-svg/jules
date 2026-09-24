"""Stockage SQLite : conversations, messages, evenements des modules, etat cle/valeur.

Seule brique qui touche a la base. Les modules passent par elle.
Le parent peut tout relire (tout_lire) et tout effacer (effacer_conversation, effacer_tout) :
voir jules/dossier.py.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    debut TEXT NOT NULL,
    mode TEXT NOT NULL,
    titre TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation TEXT NOT NULL REFERENCES conversations(id),
    role TEXT NOT NULL CHECK (role IN ('eleve', 'bot')),
    texte TEXT NOT NULL,
    images TEXT NOT NULL DEFAULT '[]',
    horodatage TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS evenements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    conversation TEXT,
    horodatage TEXT NOT NULL,
    donnees TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS etat (
    espace TEXT NOT NULL,
    cle TEXT NOT NULL,
    valeur TEXT NOT NULL,
    PRIMARY KEY (espace, cle)
);
CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation);
CREATE INDEX IF NOT EXISTS idx_evenements_type ON evenements(type, horodatage);
"""


def maintenant() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


@dataclass
class Message:
    role: str  # 'eleve' ou 'bot'
    texte: str
    images: list[str] = field(default_factory=list)  # noms de fichiers dans donnees/images
    horodatage: str = ""


@dataclass
class Conversation:
    id: str
    debut: str
    mode: str
    titre: str
    messages: list[Message] = field(default_factory=list)


class Stockage:
    def __init__(self, dossier: Path) -> None:
        self.dossier = dossier
        self.dossier_images = dossier / "images"
        self.dossier_images.mkdir(parents=True, exist_ok=True)
        self._verrou = threading.Lock()
        self._cx = sqlite3.connect(dossier / "jules.db", check_same_thread=False)
        self._cx.row_factory = sqlite3.Row
        self._cx.executescript(SCHEMA)

    # --- conversations -------------------------------------------------
    def creer_conversation(self, mode: str) -> Conversation:
        conv = Conversation(id=uuid.uuid4().hex[:12], debut=maintenant(), mode=mode, titre="")
        with self._verrou, self._cx:
            self._cx.execute(
                "INSERT INTO conversations (id, debut, mode, titre) VALUES (?, ?, ?, ?)",
                (conv.id, conv.debut, conv.mode, conv.titre),
            )
        return conv

    def conversation(self, conv_id: str) -> Conversation | None:
        with self._verrou:
            ligne = self._cx.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,)).fetchone()
            if ligne is None:
                return None
            msgs = self._cx.execute(
                "SELECT role, texte, images, horodatage FROM messages WHERE conversation = ? ORDER BY id",
                (conv_id,),
            ).fetchall()
        conv = Conversation(id=ligne["id"], debut=ligne["debut"], mode=ligne["mode"], titre=ligne["titre"])
        conv.messages = [
            Message(role=m["role"], texte=m["texte"], images=json.loads(m["images"]), horodatage=m["horodatage"])
            for m in msgs
        ]
        return conv

    def lister_conversations(self, jour: str | None = None, limite: int = 50) -> list[dict[str, Any]]:
        requete = (
            "SELECT c.id, c.debut, c.mode, c.titre, COUNT(m.id) AS nb, MAX(m.horodatage) AS dernier "
            "FROM conversations c LEFT JOIN messages m ON m.conversation = c.id "
        )
        params: list[Any] = []
        if jour:
            requete += "WHERE substr(c.debut, 1, 10) = ? "
            params.append(jour)
        requete += "GROUP BY c.id ORDER BY c.debut DESC LIMIT ?"
        params.append(limite)
        with self._verrou:
            return [dict(r) for r in self._cx.execute(requete, params).fetchall()]

    def renommer(self, conv_id: str, titre: str) -> None:
        with self._verrou, self._cx:
            self._cx.execute("UPDATE conversations SET titre = ? WHERE id = ?", (titre[:80], conv_id))

    def ajouter_message(self, conv_id: str, message: Message) -> Message:
        message.horodatage = message.horodatage or maintenant()
        with self._verrou, self._cx:
            self._cx.execute(
                "INSERT INTO messages (conversation, role, texte, images, horodatage) VALUES (?, ?, ?, ?, ?)",
                (conv_id, message.role, message.texte, json.dumps(message.images), message.horodatage),
            )
        return message

    def messages_du_jour(self, jour: str) -> list[dict[str, Any]]:
        with self._verrou:
            lignes = self._cx.execute(
                "SELECT conversation, role, texte, horodatage FROM messages "
                "WHERE substr(horodatage, 1, 10) = ? ORDER BY id",
                (jour,),
            ).fetchall()
        return [dict(r) for r in lignes]

    # --- images ----------------------------------------------------------
    def enregistrer_image(self, contenu: bytes, extension: str) -> str:
        nom = f"{uuid.uuid4().hex}.{extension}"
        (self.dossier_images / nom).write_bytes(contenu)
        return nom

    def chemin_image(self, nom: str) -> Path | None:
        chemin = (self.dossier_images / nom).resolve()
        if chemin.parent != self.dossier_images.resolve() or not chemin.is_file():
            return None
        return chemin

    # --- evenements (journal des modules) --------------------------------
    def ajouter_evenement(self, type_: str, donnees: dict[str, Any], conversation: str | None = None) -> None:
        with self._verrou, self._cx:
            self._cx.execute(
                "INSERT INTO evenements (type, conversation, horodatage, donnees) VALUES (?, ?, ?, ?)",
                (type_, conversation, maintenant(), json.dumps(donnees, ensure_ascii=False)),
            )

    def evenements(self, type_: str, jour: str | None = None, limite: int = 500) -> list[dict[str, Any]]:
        requete = "SELECT type, conversation, horodatage, donnees FROM evenements WHERE type = ? "
        params: list[Any] = [type_]
        if jour:
            requete += "AND substr(horodatage, 1, 10) = ? "
            params.append(jour)
        requete += "ORDER BY id DESC LIMIT ?"
        params.append(limite)
        with self._verrou:
            lignes = self._cx.execute(requete, params).fetchall()
        return [{**dict(r), "donnees": json.loads(r["donnees"])} for r in lignes]

    # --- etat cle/valeur par espace (un espace par module) --------------
    def lire_etat(self, espace: str, cle: str, defaut: Any = None) -> Any:
        with self._verrou:
            ligne = self._cx.execute("SELECT valeur FROM etat WHERE espace = ? AND cle = ?", (espace, cle)).fetchone()
        return json.loads(ligne["valeur"]) if ligne else defaut

    def ecrire_etat(self, espace: str, cle: str, valeur: Any) -> None:
        with self._verrou, self._cx:
            self._cx.execute(
                "INSERT INTO etat (espace, cle, valeur) VALUES (?, ?, ?) "
                "ON CONFLICT(espace, cle) DO UPDATE SET valeur = excluded.valeur",
                (espace, cle, json.dumps(valeur, ensure_ascii=False)),
            )

    # --- dossier complet (export et effacement par le parent) -----------
    def tout_lire(self) -> dict[str, Any]:
        """Tout ce que la base contient, en clair : conversations et messages, evenements, etat."""
        with self._verrou:
            convs = self._cx.execute("SELECT id, debut, mode, titre FROM conversations ORDER BY debut").fetchall()
            msgs = self._cx.execute(
                "SELECT conversation, role, texte, images, horodatage FROM messages ORDER BY id"
            ).fetchall()
            evs = self._cx.execute(
                "SELECT type, conversation, horodatage, donnees FROM evenements ORDER BY id"
            ).fetchall()
            etats = self._cx.execute("SELECT espace, cle, valeur FROM etat ORDER BY espace, cle").fetchall()
        par_conv: dict[str, list[dict[str, Any]]] = {}
        for m in msgs:
            par_conv.setdefault(m["conversation"], []).append(
                {
                    "role": m["role"],
                    "texte": m["texte"],
                    "images": json.loads(m["images"]),
                    "horodatage": m["horodatage"],
                }
            )
        etat: dict[str, dict[str, Any]] = {}
        for e in etats:
            etat.setdefault(e["espace"], {})[e["cle"]] = json.loads(e["valeur"])
        return {
            "conversations": [{**dict(c), "messages": par_conv.get(c["id"], [])} for c in convs],
            "evenements": [{**dict(e), "donnees": json.loads(e["donnees"])} for e in evs],
            "etat": etat,
        }

    def effacer_conversation(self, conv_id: str) -> bool:
        """Efface une conversation, ses messages, ses photos et les analyses qui en viennent."""
        with self._verrou, self._cx:
            if self._cx.execute("SELECT 1 FROM conversations WHERE id = ?", (conv_id,)).fetchone() is None:
                return False
            images = self._cx.execute("SELECT images FROM messages WHERE conversation = ?", (conv_id,)).fetchall()
            self._cx.execute("DELETE FROM messages WHERE conversation = ?", (conv_id,))
            self._cx.execute("DELETE FROM evenements WHERE conversation = ?", (conv_id,))
            self._cx.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
        for ligne in images:
            for nom in json.loads(ligne["images"]):
                chemin = self.chemin_image(nom)
                if chemin is not None:
                    chemin.unlink()
        self._compacter()
        return True

    def effacer_tout(self, garder_espaces: tuple[str, ...] = ()) -> None:
        """Efface conversations, messages, evenements, etat (sauf les espaces techniques gardes) et photos."""
        with self._verrou, self._cx:
            self._cx.execute("DELETE FROM messages")
            self._cx.execute("DELETE FROM evenements")
            self._cx.execute("DELETE FROM conversations")
            self._cx.execute(
                "DELETE FROM etat WHERE espace NOT IN (SELECT value FROM json_each(?))", (json.dumps(garder_espaces),)
            )
        for image in self.dossier_images.iterdir():
            if image.is_file():
                image.unlink()
        self._compacter()

    def _compacter(self) -> None:
        """Reecrit la base : sans cela, SQLite garde les lignes effacees dans ses pages libres."""
        with self._verrou:
            self._cx.execute("VACUUM")

    def fermer(self) -> None:
        self._cx.close()
