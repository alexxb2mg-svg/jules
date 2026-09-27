"""Limite d'essais du code d'acces : compteur par IP et compteur global (jules/web/limite.py)."""

from __future__ import annotations

from jules.web.limite import LimiteEssais


def test_plafond_par_ip():
    limite = LimiteEssais(essais_max_ip=8, essais_max_global=30)
    for _ in range(8):
        assert limite.autorise("1.2.3.4")
        limite.enregistrer_echec("1.2.3.4")
    assert not limite.autorise("1.2.3.4")
    assert limite.autorise("5.6.7.8")  # une autre IP n'est pas affectee


def test_plafond_global_meme_si_chaque_ip_reste_sous_son_plafond():
    """Plusieurs appareils d'un meme LAN, chacun sous le plafond par IP, ne doivent pas pouvoir
    multiplier les essais indefiniment : le compteur global (toutes IP confondues) doit aussi
    fermer la porte."""
    limite = LimiteEssais(essais_max_ip=8, essais_max_global=30)
    ips = [f"10.0.0.{i}" for i in range(6)]
    for i in range(30):
        adresse = ips[i % len(ips)]
        assert limite.autorise(adresse)
        limite.enregistrer_echec(adresse)
    for adresse in ips:
        assert not limite.autorise(adresse)  # chacune est bien sous 8 essais, mais le total atteint 30


def test_fenetre_expire():
    limite = LimiteEssais(essais_max_ip=1, essais_max_global=30, fenetre_s=600)
    debut = 1_000_000.0
    limite.enregistrer_echec("1.2.3.4", maintenant=debut)
    assert not limite.autorise("1.2.3.4", maintenant=debut + 1)
    assert limite.autorise("1.2.3.4", maintenant=debut + 601)  # fenetre expiree
