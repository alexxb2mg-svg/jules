"""Lecteur YAML rapide (jules/yaml_rapide.py) : il doit rendre EXACTEMENT les memes donnees que yaml.safe_load.
Verifie sur toutes les fiches et lecons du depot (docs/PERFORMANCES.md §1)."""

from __future__ import annotations

import yaml

from jules import yaml_rapide
from tests.conftest import RACINE


def test_memes_donnees_que_safe_load_sur_tout_le_depot():
    fichiers = sorted((RACINE / "bibliotheque").rglob("*.yaml"))
    assert len(fichiers) > 100
    for f in fichiers:
        texte = f.read_text(encoding="utf-8")
        assert yaml_rapide.charger(texte) == yaml.safe_load(texte), f


def test_lecteur_sur_et_types_de_base():
    texte = "a: 1\nb: [x, 2.5, true, null]\nc: '2026-09-28'\nd: 2026-09-28\n"
    assert yaml_rapide.charger(texte) == yaml.safe_load(texte)
    # aucune construction d'objet Python arbitraire
    try:
        yaml_rapide.charger("!!python/object/apply:os.system ['echo x']")
    except yaml.YAMLError:
        pass
    else:  # pragma: no cover
        raise AssertionError("le lecteur doit refuser les balises python/*")


def test_lecteur_c_utilise_quand_disponible():
    assert yaml_rapide.RAPIDE == hasattr(yaml, "CSafeLoader")
