"""Acces par code : empreintes scrypt dans config.local.yaml, session par cookie signe (HMAC).

Deux roles : 'eleve' (le chat) et 'parent' (suivi, notes, rapports ; le parent a aussi acces au chat).
Un code vide = acces libre pour ce role, ce qui n'est admis que si le serveur n'ecoute que
sur l'ordinateur lui-meme (127.0.0.1) : voir `verifier_exposition`.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from itertools import pairwise
from pathlib import Path

DUREE_S = 30 * 24 * 3600
COOKIE = "jules_session"
ROLES = ("eleve", "parent")
LONGUEUR_MIN = {"eleve": 6, "parent": 8}
HOTES_LOCAUX = {"127.0.0.1", "localhost", "::1"}

# Codes trop devines : mots de passe courants et claviers (les suites comme "123456" ou "abcdef"
# sont detectees a part par `_suite_triviale`, pas besoin de toutes les lister ici).
CODES_EVIDENTS = {
    "azerty",
    "azertyui",
    "azertyuiop",
    "qwerty",
    "qwertyui",
    "qwertyuiop",
    "password",
    "passw0rd",
    "letmein",
    "motdepasse",
    "monmotdepasse",
    "changeme",
    "soleil",
    "bonjour",
    "bonjour1",
    "football",
    "marseille",
    "11111111",
    "00000000",
    "121212",
    "123123",
    "12341234",
}

# scrypt (bibliotheque standard) : lent a calculer, donc une empreinte volee ne se casse pas en
# essayant tous les codes. Parametres recommandes par la documentation Python / RFC 7914.
_N, _R, _P = 2**14, 8, 1


class ErreurAcces(RuntimeError):
    pass


def empreinte(code: str, sel: bytes | None = None) -> str:
    sel = sel or secrets.token_bytes(16)
    derive = hashlib.scrypt(code.strip().encode("utf-8"), salt=sel, n=_N, r=_R, p=_P, dklen=32)
    return f"scrypt${sel.hex()}${derive.hex()}"


def code_correct(code: str, attendu: str) -> bool:
    try:
        methode, sel_hex, derive_hex = attendu.split("$")
        sel = bytes.fromhex(sel_hex)
    except ValueError:
        return False
    if methode != "scrypt" or not derive_hex:
        return False
    return hmac.compare_digest(empreinte(code, sel), attendu)


def _suite_triviale(code: str) -> bool:
    """Detecte une suite de caracteres consecutifs, croissante ou decroissante (123456, fedcba...)."""
    if len(code) < 3:
        return False
    ecarts = {ord(suivant) - ord(precedent) for precedent, suivant in pairwise(code)}
    return ecarts in ({1}, {-1})


def code_evident(code: str) -> bool:
    """Repere un code trop facile a deviner : un seul caractere repete, une suite, ou un mot de passe courant.

    Ne remplace pas la longueur minimale (`LONGUEUR_MIN`) : les deux controles sont complementaires.
    """
    nettoye = code.strip().lower()
    if not nettoye:
        return False
    if len(set(nettoye)) == 1:
        return True
    if _suite_triviale(nettoye):
        return True
    return nettoye in CODES_EVIDENTS


def verifier_exposition(hote: str, empreintes: dict[str, str]) -> None:
    """Refuse de demarrer un serveur visible sur le reseau sans codes d'acces."""
    if hote in HOTES_LOCAUX:
        return
    manquants = [role for role in ROLES if not empreintes.get(f"code_{role}")]
    if manquants:
        raise ErreurAcces(
            f"Le serveur ecoute sur {hote} (visible sur le reseau) mais aucun code n'est defini pour : "
            f"{', '.join(manquants)}. Lance `python lancer.py code eleve` et `python lancer.py code parent`, "
            "ou remets serveur.hote a 127.0.0.1."
        )


class Acces:
    def __init__(self, empreintes: dict[str, str], fichier_secret: Path) -> None:
        self.empreintes = {role: str(empreintes.get(f"code_{role}", "") or "") for role in ROLES}
        self.secret = self._secret(fichier_secret)

    @staticmethod
    def _secret(fichier: Path) -> bytes:
        if not fichier.is_file():
            fichier.parent.mkdir(parents=True, exist_ok=True)
            fichier.write_text(secrets.token_hex(32), encoding="ascii")
        return fichier.read_text(encoding="ascii").strip().encode("ascii")

    def libre(self, role: str) -> bool:
        return not self.empreintes.get(role)

    def verifier_code(self, code: str) -> str | None:
        """Renvoie le role le plus eleve correspondant au code, ou None."""
        for role in ("parent", "eleve"):
            attendu = self.empreintes.get(role)
            if attendu and code_correct(code, attendu):
                return role
        return None

    def jeton(self, role: str, maintenant: float | None = None) -> str:
        instant = time.time() if maintenant is None else maintenant
        expire = int(instant + DUREE_S)
        charge = f"{role}.{expire}"
        return f"{charge}.{self._signer(charge)}"

    def lire_jeton(self, jeton: str | None, maintenant: float | None = None) -> str | None:
        if not jeton or jeton.count(".") != 2:
            return None
        role, expire, signature = jeton.split(".")
        if role not in ROLES or not expire.isdigit():
            return None
        if not hmac.compare_digest(signature, self._signer(f"{role}.{expire}")):
            return None
        if int(expire) < (time.time() if maintenant is None else maintenant):
            return None
        return role

    def _signer(self, charge: str) -> str:
        return hmac.new(self.secret, charge.encode("utf-8"), hashlib.sha256).hexdigest()[:32]

    def autorise(self, role_session: str | None, role_requis: str) -> bool:
        if role_requis == "eleve":
            return role_session in ("eleve", "parent") or self.libre("eleve")
        return role_session == "parent" or self.libre("parent")
