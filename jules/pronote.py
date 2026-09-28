# -*- coding: utf-8 -*-
"""Pont Pronote : récupère EDT, devoirs, contenu de cours et notes via pronotepy.

Toute information personnelle (identifiants, URL, noms) est lue depuis
config.local.yaml qui n'est JAMAIS publié (.gitignore).

Section attendue dans config.local.yaml :

    pronote:
      url: "https://XXXXX.index-education.net/pronote/parent.html"
      username: "identifiant_educonnect"
      password: "mot_de_passe"
      ent: "nom_de_votre_ent"          # optionnel, null = accès direct
      child_index: 0                   # si plusieurs enfants sur le compte parent

Usage interne uniquement — pas d'export, pas de publication de données.
"""

from __future__ import annotations

import datetime
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pronotepy
import pronotepy.ent as ent_functions

log = logging.getLogger("jules.pronote")

# ---------------------------------------------------------------------------
#  Types de retour légers (dicts sérialisables JSON)
# ---------------------------------------------------------------------------


def _ser_dt(d: datetime.datetime | datetime.date | None) -> str | None:
    return d.isoformat() if d else None


def _lesson_dict(l: pronotepy.Lesson) -> dict[str, Any]:
    return {
        "id": str(l.id) if hasattr(l, "id") else None,
        "subject": l.subject.name if l.subject else None,
        "teacher": l.teacher_name if hasattr(l, "teacher_name") else None,
        "room": l.classroom if hasattr(l, "classroom") else None,
        "start": _ser_dt(l.start),
        "end": _ser_dt(l.end),
        "canceled": l.canceled if hasattr(l, "canceled") else False,
        "status": l.status if hasattr(l, "status") else None,
        "memo": l.memo if hasattr(l, "memo") else None,
    }


def _homework_dict(h: pronotepy.Homework) -> dict[str, Any]:
    return {
        "id": str(h.id) if hasattr(h, "id") else None,
        "subject": h.subject.name if h.subject else None,
        "description": h.description if hasattr(h, "description") else None,
        "done": h.done if hasattr(h, "done") else False,
        "date": _ser_dt(h.date) if hasattr(h, "date") else None,
    }


def _grade_dict(g: Any) -> dict[str, Any]:
    return {
        "subject": g.subject.name if hasattr(g, "subject") and g.subject else None,
        "grade": str(g.grade) if hasattr(g, "grade") else None,
        "out_of": str(g.out_of) if hasattr(g, "out_of") else None,
        "average": str(g.average) if hasattr(g, "average") else None,
        "date": _ser_dt(g.date) if hasattr(g, "date") else None,
        "comment": g.comment if hasattr(g, "comment") else None,
    }


# ---------------------------------------------------------------------------
#  Client wrapper
# ---------------------------------------------------------------------------


@dataclass
class PronoteClient:
    """Wrapper autour de pronotepy.ParentClient (ou Client).

    Gère la connexion, la reconnexion automatique, et expose des méthodes
    qui retournent des dicts JSON-sérialisables.
    """

    url: str = ""
    username: str = ""
    password: str = ""
    ent_name: str | None = None
    ent_url: str | None = None  # URL CAS personnalisée (si celle par défaut est périmée)
    child_index: int = 0

    _client: Any = field(default=None, init=False, repr=False)

    # -- connexion -----------------------------------------------------------

    def connect(self) -> bool:
        """Connexion au serveur Pronote. Retourne True si ok."""
        ent_func = None
        if self.ent_name:
            ent_func = getattr(ent_functions, self.ent_name, None)
            if ent_func is None:
                log.error("Fonction ENT '%s' introuvable dans pronotepy.ent", self.ent_name)
                return False
            # Si une URL CAS personnalisée est fournie, on surcharge l'URL par défaut
            if self.ent_url:
                from functools import partial as _partial
                base_func = ent_func.func if hasattr(ent_func, "func") else ent_func
                ent_func = _partial(base_func, url=self.ent_url)

        try:
            is_parent = "parent" in self.url.lower()
            cls = pronotepy.ParentClient if is_parent else pronotepy.Client
            self._client = cls(
                self.url,
                username=self.username,
                password=self.password,
                ent=ent_func,
            )
        except Exception:
            log.exception("Échec de connexion Pronote")
            self._client = None
            return False

        if not self._client.logged_in:
            log.error("Pronote : identifiants refusés")
            self._client = None
            return False

        # Compte parent : sélectionner l'enfant
        if is_parent and hasattr(self._client, "children"):
            children = self._client.children
            if not children:
                log.error("Aucun enfant sur le compte parent")
                return False
            if self.child_index >= len(children):
                log.warning("child_index %d hors limites, on prend le premier", self.child_index)
                self.child_index = 0
            self._client.set_child(children[self.child_index])
            log.info("Enfant sélectionné : %s", children[self.child_index].name)

        log.info("Connecté à Pronote (%s)", "parent" if is_parent else "élève")
        return True

    @property
    def connected(self) -> bool:
        return self._client is not None and self._client.logged_in

    def _ensure(self) -> None:
        """Reconnexion si session expirée."""
        if self._client is None:
            self.connect()
        elif hasattr(self._client, "session_check"):
            self._client.session_check()

    # -- données -------------------------------------------------------------

    def timetable(
        self,
        date: datetime.date | None = None,
        weeks: int = 1,
    ) -> list[dict[str, Any]]:
        """Emploi du temps sur *weeks* semaines à partir de *date*."""
        self._ensure()
        if not self.connected:
            return []
        date = date or datetime.date.today()
        lessons: list[dict] = []
        for w in range(weeks):
            d = date + datetime.timedelta(weeks=w)
            try:
                raw = self._client.lessons(d)
                lessons.extend(_lesson_dict(l) for l in raw)
            except Exception:
                log.exception("Erreur récupération EDT semaine %s", d)
        return lessons

    def homework(
        self,
        date_from: datetime.date | None = None,
    ) -> list[dict[str, Any]]:
        """Devoirs à partir de *date_from* (défaut : aujourd'hui)."""
        self._ensure()
        if not self.connected:
            return []
        date_from = date_from or datetime.date.today()
        try:
            raw = self._client.homework(date_from)
            return [_homework_dict(h) for h in raw]
        except Exception:
            log.exception("Erreur récupération devoirs")
            return []

    def grades(self, period: str | None = None) -> list[dict[str, Any]]:
        """Notes de la période courante (ou nommée)."""
        self._ensure()
        if not self.connected:
            return []
        try:
            p = self._client.current_period
            if period:
                p = next((x for x in self._client.periods if x.name == period), p)
            return [_grade_dict(g) for g in p.grades]
        except Exception:
            log.exception("Erreur récupération notes")
            return []

    def info(self) -> dict[str, Any]:
        """Informations générales (nom de l'élève, établissement)."""
        self._ensure()
        if not self.connected:
            return {"connected": False}
        c = self._client
        # Compte parent : on affiche l'enfant sélectionné, pas le parent
        src = c
        if hasattr(c, "children") and c.children:
            src = c.children[self.child_index] if self.child_index < len(c.children) else c.children[0]
        return {
            "connected": True,
            "name": src.name if hasattr(src, "name") else None,
            "school": src.establishment if hasattr(src, "establishment") else None,
            "class": src.class_name if hasattr(src, "class_name") else None,
        }


# ---------------------------------------------------------------------------
#  Factory depuis la config Jules
# ---------------------------------------------------------------------------


def _dechiffrer_si_enc(valeur: str, donnees: Path | None) -> str:
    """Si la valeur commence par 'ENC:', la déchiffrer avec secret.key. Sinon retour tel quel."""
    if not valeur.startswith("ENC:"):
        return valeur
    if donnees is None:
        log.error("Identifiant chiffré mais pas de chemin vers donnees/secret.key")
        return ""
    cle_path = donnees / "secret.key"
    if not cle_path.is_file():
        log.error("Identifiant chiffré mais secret.key introuvable : %s", cle_path)
        return ""
    from jules.pronote_crypt import dechiffrer
    return dechiffrer(valeur[4:], cle_path)


def from_config(config: dict[str, Any]) -> PronoteClient | None:
    """Crée un PronoteClient à partir de la section `pronote:` de la config.

    Retourne None si la section n'existe pas.
    Les identifiants préfixés par ``ENC:`` sont déchiffrés avec ``donnees/secret.key``.
    """
    section = config.get("pronote")
    if not section:
        return None
    # Chemin vers le dossier données pour le déchiffrement
    donnees_path = Path(config.get("donnees", "donnees"))
    if not donnees_path.is_absolute():
        # Relatif à la racine du projet
        donnees_path = Path(__file__).resolve().parent.parent / donnees_path
    return PronoteClient(
        url=section.get("url", ""),
        username=_dechiffrer_si_enc(str(section.get("username", "")), donnees_path),
        password=_dechiffrer_si_enc(str(section.get("password", "")), donnees_path),
        ent_name=section.get("ent") if section.get("ent") else None,
        ent_url=section.get("ent_url"),
        child_index=section.get("child_index", 0),
    )
