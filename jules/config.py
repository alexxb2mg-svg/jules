"""Lecture de la configuration (config.yaml + config.local.yaml + .env) en objets simples."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

RACINE = Path(__file__).resolve().parents[1]


@dataclass
class RefBrique:
    """Reference a une brique : son id (= nom du fichier), active ou non, ses reglages."""

    id: str
    actif: bool = True
    reglages: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def depuis(cls, brut: dict[str, Any] | str) -> RefBrique:
        if isinstance(brut, str):
            return cls(id=brut)
        return cls(
            id=str(brut["id"]),
            actif=bool(brut.get("actif", True)),
            reglages=dict(brut.get("reglages") or {}),
        )


@dataclass
class Config:
    racine: Path
    donnees: Path
    hote: str
    port: int
    persona: str
    profil: str
    llm: dict[str, Any]
    acces: dict[str, str]
    modules: list[RefBrique]
    notifieurs: list[RefBrique]

    @property
    def dossier_consignes(self) -> Path:
        return self.racine / "consignes"

    @property
    def dossier_bibliotheques(self) -> Path:
        return self.racine / "bibliotheque"

    @property
    def dossier_persona(self) -> Path:
        return self.racine / "persona" / self.persona

    @property
    def fichier_profil(self) -> Path:
        return self.racine / "profils" / f"{self.profil}.yaml"


def depuis_dict(brut: dict[str, Any], racine: Path) -> Config:
    serveur = brut.get("serveur") or {}
    donnees = Path(brut.get("donnees") or "donnees")
    return Config(
        racine=racine,
        donnees=donnees if donnees.is_absolute() else racine / donnees,
        hote=str(serveur.get("hote", "127.0.0.1")),
        port=int(serveur.get("port", 8795)),
        persona=str(brut["persona"]),
        profil=str(brut["profil"]),
        llm=dict(brut.get("llm") or {}),
        acces=dict(brut.get("acces") or {}),
        modules=[RefBrique.depuis(m) for m in brut.get("modules") or []],
        notifieurs=[RefBrique.depuis(n) for n in brut.get("notifieurs") or []],
    )


def fusionner(base: dict[str, Any], surcharge: dict[str, Any]) -> dict[str, Any]:
    """Fusion recursive : les cles de `surcharge` remplacent celles de `base`."""
    resultat = dict(base)
    for cle, valeur in surcharge.items():
        if isinstance(valeur, dict) and isinstance(resultat.get(cle), dict):
            resultat[cle] = fusionner(resultat[cle], valeur)
        else:
            resultat[cle] = valeur
    return resultat


def charger_env(fichier: Path) -> list[str]:
    """Charge un fichier .env (CLE=valeur) dans l'environnement, sans ecraser l'existant.

    Les cles API vivent ici, dans un fichier jamais publie, et non dans la configuration.
    Renvoie les noms des variables chargees.
    """
    if not fichier.is_file():
        return []
    charges = []
    for ligne in fichier.read_text(encoding="utf-8").splitlines():
        ligne = ligne.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue
        cle, valeur = ligne.removeprefix("export ").split("=", 1)
        cle, valeur = cle.strip(), valeur.strip().strip('"').strip("'")
        if cle and cle not in os.environ:
            os.environ[cle] = valeur
            charges.append(cle)
    return charges


def charger_config(chemin: Path | None = None) -> Config:
    """config.yaml (partage, sans donnee perso) + config.local.yaml s'il existe (propre a la famille,
    jamais publie : profil de l'enfant, codes d'acces, reglages locaux)."""
    chemin = chemin or RACINE / "config.yaml"
    charger_env(chemin.with_name(".env"))
    brut = yaml.safe_load(chemin.read_text(encoding="utf-8")) or {}
    local = chemin.with_name("config.local.yaml")
    if local.is_file():
        brut = fusionner(brut, yaml.safe_load(local.read_text(encoding="utf-8")) or {})
    return depuis_dict(brut, chemin.resolve().parent)
