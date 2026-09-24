"""Assistant d'installation : `python lancer.py installer`.

Pose quelques questions simples et ecrit trois fichiers, tous exclus de git :
  - profils/<prenom>.yaml  : le profil de l'enfant ;
  - config.local.yaml      : le choix du profil et du moteur d'IA ;
  - .env                   : l'emplacement de la cle API (a coller soi-meme, jamais affichee).
Les fonctions de construction sont pures (testables) ; seule `lancer` pose des questions.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from jules.texte import GENRE_DEFAUT, GENRES, normaliser_genre


@dataclass(frozen=True)
class Moteur:
    id: str
    libelle: str
    llm: dict[str, Any]
    cle_env: str = ""
    aide: str = ""


MOTEURS = (
    Moteur("demo", "Démo (sans IA, pour découvrir l'interface)", {"backend": "demo"}),
    Moteur(
        "ollama",
        "Ollama : modèle gratuit sur cet ordinateur, rien ne sort de la maison",
        {
            "backend": "openai_compatible",
            "url": "http://127.0.0.1:11434/v1",
            "modeles": {"principal": "qwen3-vl:8b", "rapide": "qwen3-vl:8b"},
            "parametres": {"reasoning_effort": "none"},
        },
        aide="Installer Ollama (https://ollama.com) puis lancer : ollama pull qwen3-vl:8b",
    ),
    Moteur(
        "anthropic",
        "Anthropic (Claude), clé API payante",
        {
            "backend": "anthropic",
            "cle_env": "ANTHROPIC_API_KEY",
            "modeles": {"principal": "claude-sonnet-5", "rapide": "claude-haiku-4-5"},
        },
        cle_env="ANTHROPIC_API_KEY",
        aide="Clé sur https://console.anthropic.com ; fixer un plafond de dépense mensuel.",
    ),
    Moteur(
        "mistral",
        "Mistral AI (entreprise française), clé API",
        {
            "backend": "openai_compatible",
            "url": "https://api.mistral.ai/v1",
            "cle_env": "MISTRAL_API_KEY",
            "modeles": {"principal": "mistral-medium-latest", "rapide": "mistral-small-latest"},
        },
        cle_env="MISTRAL_API_KEY",
        aide="Clé sur https://console.mistral.ai",
    ),
    Moteur(
        "openai",
        "OpenAI, clé API payante",
        {
            "backend": "openai_compatible",
            "url": "https://api.openai.com/v1",
            "cle_env": "OPENAI_API_KEY",
            "modeles": {"principal": "gpt-5-mini", "rapide": "gpt-5-nano"},
        },
        cle_env="OPENAI_API_KEY",
        aide="Clé sur https://platform.openai.com ; fixer un plafond de dépense mensuel.",
    ),
)


def identifiant(prenom: str) -> str:
    """'Élise-Marie' -> 'elise-marie' : nom de fichier sans accent ni espace."""
    sans_accent = unicodedata.normalize("NFKD", prenom).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", sans_accent.lower()).strip("-") or "eleve"


def profil_yaml(prenom: str, genre: str, classe: str, parent: str) -> str:
    if genre not in GENRES:
        raise ValueError(f"Genre inconnu : {genre}")
    donnees = {
        "prenom": prenom,
        "genre": genre,
        "parent": parent,
        "classe": classe,
        "centres_interet": [],
        "points_a_travailler": [],
        "remarques": "",
    }
    return "# Profil cree par l'assistant d'installation. Jamais publie.\n" + yaml.safe_dump(
        donnees, allow_unicode=True, sort_keys=False
    )


def config_locale(existante: dict[str, Any], profil: str, moteur: Moteur) -> dict[str, Any]:
    """Nouvelle config locale : garde les reglages existants (codes...), remplace profil et moteur."""
    resultat = dict(existante)
    resultat["profil"] = profil
    resultat["llm"] = dict(moteur.llm)
    return resultat


def ligne_env(texte_env: str, nom: str) -> str:
    """Ajoute `NOM=` au .env si la variable n'y est pas encore (valeur a coller par l'adulte)."""
    if not nom or re.search(rf"^\s*{re.escape(nom)}\s*=", texte_env, re.MULTILINE):
        return texte_env
    prefixe = texte_env if not texte_env or texte_env.endswith("\n") else texte_env + "\n"
    return prefixe + f"{nom}=\n"


def lancer(racine: Path, demander: Callable[[str], str] = input, afficher: Callable[[str], None] = print) -> None:
    afficher("Installation de Jules. Entrée = valeur proposée entre crochets.\n")
    prenom = demander("Prénom de l'enfant : ").strip() or "Camille"
    choix_genre = demander("Genre, pour accorder les phrases (fille / garcon / neutre) [neutre] : ").strip().lower()
    try:
        genre = normaliser_genre(choix_genre)
    except ValueError:
        genre = GENRE_DEFAUT
    classe = demander("Classe (6e, 5e, 4e, 3e) [laisser vide si inconnue] : ").strip()
    parent = demander("Comment Jules doit nommer l'adulte à prévenir [ses parents] : ").strip() or "ses parents"

    afficher("\nMoteur d'intelligence artificielle :")
    for numero, moteur in enumerate(MOTEURS, start=1):
        afficher(f"  {numero}. {moteur.libelle}")
    saisie = demander("Choix [1] : ").strip() or "1"
    moteur = MOTEURS[int(saisie) - 1] if saisie.isdigit() and 1 <= int(saisie) <= len(MOTEURS) else MOTEURS[0]

    id_profil = identifiant(prenom)
    fichier_profil = racine / "profils" / f"{id_profil}.yaml"
    if fichier_profil.exists() and demander(f"{fichier_profil.name} existe déjà. Le remplacer ? (o/N) ").lower() != "o":
        afficher("Profil existant conservé.")
    else:
        fichier_profil.write_text(profil_yaml(prenom, genre, classe, parent), encoding="utf-8")

    fichier_local = racine / "config.local.yaml"
    existante = yaml.safe_load(fichier_local.read_text(encoding="utf-8")) if fichier_local.is_file() else None
    contenu = config_locale(existante or {}, id_profil, moteur)
    entete = "# Reglages propres a cette famille. Fusionne par-dessus config.yaml. Jamais publie.\n"
    fichier_local.write_text(entete + yaml.safe_dump(contenu, allow_unicode=True, sort_keys=False), encoding="utf-8")

    if moteur.cle_env:
        fichier_env = racine / ".env"
        texte = fichier_env.read_text(encoding="utf-8") if fichier_env.is_file() else ""
        fichier_env.write_text(ligne_env(texte, moteur.cle_env), encoding="utf-8")
        afficher(f"\nOuvre le fichier .env et colle ta clé après {moteur.cle_env}= (elle ne sera jamais publiée).")
    if moteur.aide:
        afficher(moteur.aide)
    afficher(
        "\nC'est prêt. Étapes suivantes :\n"
        "  jules code parent   (code de l'espace parent)\n"
        "  jules code eleve    (code de l'enfant)\n"
        "  jules               (démarre Jules sur http://127.0.0.1:8795)\n"
        "Sans installation par pip, remplacer « jules » par « python lancer.py »."
    )
