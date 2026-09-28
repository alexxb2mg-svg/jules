# -*- coding: utf-8 -*-
"""Chiffrement réversible des identifiants Pronote avec la clé locale secret.key.

Utilise Fernet (AES-128-CBC + HMAC-SHA256) de la bibliothèque `cryptography`.
La clé Fernet est dérivée de donnees/secret.key via HKDF-SHA256.

Usage :
    # Chiffrer (interactif)
    python -m jules.pronote_crypt

    # Depuis le code
    from jules.pronote_crypt import chiffrer, dechiffrer
    token = chiffrer("mon_mot_de_passe", cle_path)
    mdp = dechiffrer(token, cle_path)
"""

from __future__ import annotations

import base64
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes


def _fernet(cle_path: Path) -> Fernet:
    """Dérive une clé Fernet 32 octets depuis secret.key via HKDF."""
    materiel = cle_path.read_bytes()
    derive = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"jules-pronote-v1",
        info=b"pronote credentials",
    ).derive(materiel)
    return Fernet(base64.urlsafe_b64encode(derive))


def chiffrer(texte: str, cle_path: Path) -> str:
    """Chiffre un texte → token Fernet encodé base64 (stockable dans YAML)."""
    return _fernet(cle_path).encrypt(texte.encode("utf-8")).decode("ascii")


def dechiffrer(token: str, cle_path: Path) -> str:
    """Déchiffre un token Fernet → texte original."""
    return _fernet(cle_path).decrypt(token.encode("ascii")).decode("utf-8")


if __name__ == "__main__":
    import sys
    from jules.config import charger_config

    config = charger_config()
    cle = config.donnees / "secret.key"
    if not cle.is_file():
        print(f"Clé introuvable : {cle}", file=sys.stderr)
        sys.exit(1)

    print("Chiffrement des identifiants Pronote")
    print(f"Clé : {cle}")
    username = input("Identifiant Pronote : ").strip()
    password = input("Mot de passe Pronote : ").strip()

    enc_user = chiffrer(username, cle)
    enc_pass = chiffrer(password, cle)

    print("\nÀ mettre dans config.local.yaml (section pronote:) :")
    print(f'  username: "ENC:{enc_user}"')
    print(f'  password: "ENC:{enc_pass}"')
    print("\nLes valeurs en clair peuvent être supprimées.")
