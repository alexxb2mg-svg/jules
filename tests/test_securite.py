"""Acces : empreintes des codes, exposition reseau, fichiers de persona."""

from __future__ import annotations

import pytest

from jules.acces import ErreurAcces, code_correct, code_evident, empreinte, verifier_exposition
from jules.persona import ErreurPersona, charger_persona


def test_empreinte_salee_et_verifiable():
    a, b = empreinte("1234"), empreinte("1234")
    assert a != b  # sel different a chaque fois : deux familles avec le meme code n'ont pas la meme empreinte
    assert code_correct("1234", a) and code_correct(" 1234 ", b)
    assert not code_correct("1235", a)


@pytest.mark.parametrize("attendu", ["", "abc", "md5$00$11", "scrypt$zz$11", "scrypt$00$"])
def test_empreinte_invalide_refusee(attendu):
    assert not code_correct("1234", attendu)


@pytest.mark.parametrize(
    "code",
    [
        "aaaaaa",
        "111111",
        "AAAAAAAA",  # caractere unique repete
        "123456",
        "abcdef",
        "654321",
        "fedcba",
        "12345678",  # suites
        "azerty",
        "azertyui",
        "qwerty",
        "password",
        "motdepasse",
        "soleil",
        "marseille",
        "  123456  ",  # espaces autour : nettoye avant comparaison
        "AZERTY",  # casse ignoree
    ],
)
def test_code_evident_refuse(code):
    assert code_evident(code)


@pytest.mark.parametrize("code", ["tr0ub4dor", "chat-violet-19", "PjK4mLwq", "framboise7X"])
def test_code_non_evident_accepte(code):
    assert not code_evident(code)


def test_code_evident_chaine_vide_non_signalee():
    assert not code_evident("")


def test_serveur_local_sans_code_autorise():
    verifier_exposition("127.0.0.1", {})


def test_serveur_expose_sans_code_refuse():
    with pytest.raises(ErreurAcces, match="parent"):
        verifier_exposition("0.0.0.0", {"code_eleve": empreinte("1234")})  # noqa: S104


def test_serveur_expose_avec_codes_autorise():
    verifier_exposition("0.0.0.0", {"code_eleve": empreinte("1234"), "code_parent": empreinte("abcdef")})  # noqa: S104


def test_persona_ne_lit_pas_hors_de_son_dossier(tmp_path):
    dossier = tmp_path / "persona" / "pirate"
    dossier.mkdir(parents=True)
    (tmp_path / "secret.txt").write_text("cle", encoding="utf-8")
    (dossier / "persona.yaml").write_text("nom: P\nconsignes:\n  - fichier: ../../secret.txt\n", encoding="utf-8")
    with pytest.raises(ErreurPersona, match="hors du dossier"):
        charger_persona(dossier)


def test_env_charge_sans_ecraser(tmp_path, monkeypatch):
    from jules.config import charger_env

    monkeypatch.setenv("DEJA_LA", "systeme")
    monkeypatch.delenv("NOUVELLE", raising=False)
    fichier = tmp_path / ".env"
    fichier.write_text('# commentaire\nNOUVELLE="valeur"\nDEJA_LA=fichier\n\nLIGNE_INVALIDE\n', encoding="utf-8")
    assert charger_env(fichier) == ["NOUVELLE"]
    import os

    assert os.environ["NOUVELLE"] == "valeur" and os.environ["DEJA_LA"] == "systeme"
    monkeypatch.delenv("NOUVELLE")
