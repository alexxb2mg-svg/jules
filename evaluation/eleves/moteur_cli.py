"""Moteur d'IA du banc d'essai : le CLI Claude Code, isole, et un journal de chaque appel.

Pourquoi le CLI : il permet de faire tourner le banc sur un abonnement, sans cle API. Il est lance
en mode neutre (--safe-mode : ni CLAUDE.md, ni MCP, ni skills ; aucun outil ; aucune session gardee ;
repertoire de travail vide) et SANS reflexion etendue (MAX_THINKING_TOKENS=0), pour se rapprocher du
moteur `anthropic` de Jules, qui n'en demande pas.

Chaque appel est journalise : role (jules, suivi, vigilance, detection, rapport, eleve simule, juge),
modele reel, jetons, duree. Le CLI ajoute son propre socle de jetons a chaque appel : il est mesure
une fois par modele (`socle()`) et retire dans l'analyse, pour estimer le cout au tarif de l'API.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from jules.llm.base import ErreurLLM, Tour

DOSSIER_NEUTRE = Path(tempfile.gettempdir()) / "jules_banc_neutre"
MOTS_LIMITE = ("usage limit", "rate limit", "rate_limit", "overloaded", "429", "529", "limit reached")


class LimiteAtteinte(ErreurLLM):
    """Limite de debit de l'abonnement : le banc s'arrete proprement et reprendra plus tard."""


def role_appel(systeme: str, logique: str) -> str:
    """Role d'un appel fait par Jules, d'apres le debut de sa consigne systeme."""
    if logique == "principal":
        return "jules"
    debut = systeme[:120]
    for marque, role in (
        ("Tu analyses un échange", "suivi"),
        ("Tu protèges un élève", "vigilance"),
        ("Tu rattaches le travail", "detection"),
        ("Tu écris à l'adulte", "rapport"),
        ("Tu lis le bilan final", "bilan_epreuve"),
    ):
        if debut.startswith(marque):
            return role
    return "rapide_autre"


def transcription(tours: list[Tour]) -> str:
    """Meme mise en forme que le moteur claude_cli de l'installation familiale."""
    if not tours or tours[-1].role != "user":
        raise ErreurLLM("Le dernier tour doit venir de l'eleve")
    dernier = tours[-1].texte or "(photo envoyée sans texte)"
    if len(tours) == 1:
        return dernier
    lignes = [f"[{'ÉLÈVE' if t.role == 'user' else 'TOI'}]\n{t.texte}" for t in tours[:-1]]
    return (
        "<historique>\n" + "\n\n".join(lignes) + "\n</historique>\n"
        "Continue la conversation. Réponds uniquement au dernier message de l'élève, sans préfixe ni étiquette.\n\n"
        + dernier
    )


class Journal:
    """Appels d'un scenario, gardes en memoire puis ecrits avec le resultat."""

    def __init__(self) -> None:
        self.appels: list[dict[str, Any]] = []
        self._verrou = threading.Lock()

    def ajouter(self, appel: dict[str, Any]) -> None:
        with self._verrou:
            self.appels.append(appel)


class MoteurCLI:
    """Respecte le contrat MoteurLLM de Jules (repondre) et sert aussi l'eleve simule et le juge (appeler)."""

    def __init__(self, modeles: dict[str, str], journal: Journal | None = None, delai_s: int = 300) -> None:
        executable = shutil.which("claude")
        if executable is None:
            raise ErreurLLM("Commande 'claude' introuvable dans le PATH")
        self.executable = executable
        self.modeles = modeles
        self.journal = journal or Journal()
        self.delai = delai_s
        DOSSIER_NEUTRE.mkdir(exist_ok=True)

    # --- contrat MoteurLLM ------------------------------------------------------
    def repondre(self, systeme: str, tours: list[Tour], modele: str = "principal") -> str:
        alias = self.modeles.get(modele) or self.modeles["principal"]
        return self.appeler(systeme, transcription(tours), alias, role_appel(systeme, modele), logique=modele)

    # --- appel brut ---------------------------------------------------------------
    def appeler(self, systeme: str, message: str, alias: str, role: str, logique: str = "") -> str:
        attentes = (20, 60, 180)
        for essai in range(len(attentes) + 1):
            try:
                return self._appel(systeme, message, alias, role, logique)
            except LimiteAtteinte:
                if essai == len(attentes):
                    raise
                time.sleep(attentes[essai])
            except ErreurLLM:
                if essai >= 1:
                    raise
                time.sleep(5)
        raise ErreurLLM("inatteignable")

    def _appel(self, systeme: str, message: str, alias: str, role: str, logique: str) -> str:
        fichier = DOSSIER_NEUTRE / f"systeme_{uuid.uuid4().hex}.txt"
        fichier.write_text(systeme, encoding="utf-8")
        commande = [
            self.executable, "-p", "--safe-mode", "--no-session-persistence",
            "--tools", "", "--exclude-dynamic-system-prompt-sections",
            "--model", alias, "--output-format", "json",
            "--system-prompt-file", str(fichier),
        ]  # fmt: skip
        env = {**os.environ, "MAX_THINKING_TOKENS": "0"}
        debut = time.perf_counter()
        try:
            fini = subprocess.run(  # noqa: S603 (commande construite ici, sans entree de l'eleve)
                commande,
                input=message,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.delai,
                cwd=DOSSIER_NEUTRE,
                env=env,
                check=False,
            )
        except subprocess.TimeoutExpired as err:
            raise ErreurLLM(f"pas de reponse en {self.delai} s") from err
        finally:
            fichier.unlink(missing_ok=True)
        duree = time.perf_counter() - debut
        try:
            sortie = json.loads(fini.stdout.strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError) as err:
            brut = (fini.stdout + fini.stderr)[-400:]
            if any(m in brut.casefold() for m in MOTS_LIMITE):
                raise LimiteAtteinte(brut) from err
            raise ErreurLLM(f"sortie illisible : {brut}") from err
        texte = str(sortie.get("result") or "")
        if sortie.get("is_error"):
            if any(m in texte.casefold() for m in MOTS_LIMITE):
                raise LimiteAtteinte(texte[:300])
            raise ErreurLLM(texte[:300] or str(sortie.get("subtype")))
        usage = sortie.get("usage") or {}
        reel = next(iter(sortie.get("modelUsage") or {}), alias)
        self.journal.ajouter(
            {
                "role": role,
                "logique": logique,
                "alias": alias,
                "modele": reel,
                "entree": int(usage.get("input_tokens", 0))
                + int(usage.get("cache_creation_input_tokens", 0))
                + int(usage.get("cache_read_input_tokens", 0)),
                "sortie": int(usage.get("output_tokens", 0)),
                "reflexion": int((usage.get("output_tokens_details") or {}).get("thinking_tokens", 0)),
                "duree_s": round(duree, 2),
                "duree_api_s": round(float(sortie.get("duration_api_ms", 0)) / 1000, 2),
                "car_systeme": len(systeme),
                "car_message": len(message),
            }
        )
        return texte.strip()


def socle(alias: str) -> int:
    """Jetons d'entree ajoutes par le CLI lui-meme (systeme et message d'un seul caractere)."""
    journal = Journal()
    MoteurCLI({"principal": alias}, journal).appeler("x", "x", alias, "socle")
    return max(0, journal.appels[-1]["entree"] - 2)
