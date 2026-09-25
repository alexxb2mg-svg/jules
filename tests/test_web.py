"""Tests de l'application web : acces par code, API eleve et parent."""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

from jules.acces import Acces, empreinte
from jules.config import depuis_dict
from jules.moteur import Tuteur
from jules.web.app import creer_app

PNG_1PX = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xa7\x9a\xa0\xa0\x00\x00\x00\x00IEND\xaeB`\x82"
)


@pytest.fixture
def client_protege(projet, brut_config):
    from jules.llm.factice import Brique as Factice
    from tests.conftest import regle_par_defaut

    brut_config["acces"] = {"code_eleve": empreinte("1234"), "code_parent": empreinte("parent67")}
    llm = Factice()
    llm.regle = regle_par_defaut
    tuteur = Tuteur(depuis_dict(brut_config, projet), llm=llm)
    with TestClient(creer_app(tuteur)) as client:
        yield client
    tuteur.fermer()


def test_jeton_signe_et_falsification(tmp_path):
    acces = Acces({"code_parent": empreinte("x")}, tmp_path / "s.key")
    jeton = acces.jeton("eleve")
    assert acces.lire_jeton(jeton) == "eleve"
    assert acces.lire_jeton(jeton.replace("eleve", "parent", 1)) is None
    assert acces.lire_jeton(acces.jeton("eleve", maintenant=0)) is None  # expire


def test_sans_code_tout_est_bloque(client_protege):
    assert client_protege.get("/api/infos").status_code == 401
    assert client_protege.get("/api/modules/memoire/notes").status_code == 401
    assert client_protege.get("/").status_code == 200  # la page s'affiche (ecran de code)


def test_code_eleve_ne_donne_pas_acces_parent(client_protege):
    assert client_protege.post("/api/session", json={"code": "faux"}).status_code == 401
    assert client_protege.post("/api/session", json={"code": "1234"}).json() == {"role": "eleve"}
    assert client_protege.get("/api/infos").status_code == 200
    assert client_protege.get("/api/modules/memoire/notes").status_code == 401
    assert client_protege.get("/api/parent/evenements/vigilance").status_code == 401


def test_parent_voit_tout(client_protege):
    client_protege.post("/api/session", json={"code": "parent67"})
    assert client_protege.get("/api/infos").status_code == 200
    note = client_protege.post("/api/modules/memoire/notes", json={"texte": "Contrôle vendredi"}).json()
    assert client_protege.get("/api/modules/memoire/notes").json()[0]["texte"] == "Contrôle vendredi"
    assert client_protege.delete(f"/api/modules/memoire/notes/{note['id']}").json() == {"ok": True}
    assert client_protege.get("/api/modules/rapport/jour").status_code == 200


def test_trop_d_essais(client_protege):
    for _ in range(8):
        client_protege.post("/api/session", json={"code": "faux"})
    assert client_protege.post("/api/session", json={"code": "1234"}).status_code == 429


def test_conversation_avec_photo(client_protege):
    client_protege.post("/api/session", json={"code": "1234"})
    conv = client_protege.post("/api/conversations", json={"mode": "aide-devoirs"}).json()
    r = client_protege.post(
        f"/api/conversations/{conv['id']}/messages",
        data={"texte": "Voilà mon exo"},
        files=[("photos", ("exo.png", io.BytesIO(PNG_1PX), "image/png"))],
    )
    assert r.status_code == 200, r.text
    assert r.json()["reponse"] == "Qu'est-ce que tu as déjà essayé ?"
    lue = client_protege.get(f"/api/conversations/{conv['id']}").json()
    nom = lue["messages"][0]["images"][0]
    assert client_protege.get(f"/api/images/{nom}").content == PNG_1PX
    assert client_protege.get("/api/images/..%2Fjules.db").status_code == 404


def test_refus_fichier_non_image(client_protege):
    client_protege.post("/api/session", json={"code": "1234"})
    conv = client_protege.post("/api/conversations", json={}).json()
    r = client_protege.post(
        f"/api/conversations/{conv['id']}/messages",
        data={"texte": "x"},
        files=[("photos", ("virus.exe", io.BytesIO(b"MZ"), "application/octet-stream"))],
    )
    assert r.status_code == 400


def test_message_vide_refuse(client_protege):
    client_protege.post("/api/session", json={"code": "1234"})
    conv = client_protege.post("/api/conversations", json={}).json()
    assert client_protege.post(f"/api/conversations/{conv['id']}/messages", data={"texte": "  "}).status_code == 400


def test_entetes_de_securite(client_protege):
    r = client_protege.get("/")
    csp = r.headers["content-security-policy"]
    assert "script-src 'self'" in csp and "frame-ancestors 'none'" in csp
    assert r.headers["x-content-type-options"] == "nosniff"
    assert client_protege.get("/api/infos").headers["cache-control"] == "no-store"


def test_pages_sans_style_ni_script_en_ligne():
    """La politique de securite interdit le code en ligne : aucune page ne doit en contenir."""
    import re
    from pathlib import Path

    statique = Path(__file__).resolve().parents[1] / "jules" / "web" / "static"
    for page in statique.glob("*.html"):
        html = page.read_text(encoding="utf-8")
        assert not re.search(r"<script(?![^>]*\bsrc=)", html), page.name
        assert not re.search(r"\son[a-z]+\s*=", html), page.name
        assert "style=" not in html, page.name


def test_faux_png_refuse(client_protege):
    """Le type annonce ne suffit pas : le contenu doit vraiment etre une image."""
    client_protege.post("/api/session", json={"code": "1234"})
    conv = client_protege.post("/api/conversations", json={}).json()
    r = client_protege.post(
        f"/api/conversations/{conv['id']}/messages",
        data={"texte": "x"},
        files=[("photos", ("exo.png", io.BytesIO(b"<script>alert(1)</script>"), "image/png"))],
    )
    assert r.status_code == 400


def test_icones_servies_sans_code(client_protege):
    """Icone d'onglet, d'ecran d'accueil et manifeste : publics (le navigateur les charge avant le code)."""
    for chemin, debut in [
        ("/static/favicon.ico", b"\x00\x00\x01\x00"),
        ("/static/icone-192.png", b"\x89PNG"),
        ("/static/icone-512.png", b"\x89PNG"),
        ("/static/apple-touch-icon.png", b"\x89PNG"),
    ]:
        r = client_protege.get(chemin)
        assert r.status_code == 200, chemin
        assert r.content.startswith(debut), chemin
    manifeste = client_protege.get("/static/manifest.webmanifest").json()
    assert manifeste["short_name"] == "Jules"
    assert {i["sizes"] for i in manifeste["icons"]} == {"192x192", "512x512"}
    page = client_protege.get("/").text
    assert 'rel="manifest"' in page
    assert 'rel="apple-touch-icon"' in page


def test_avatar_de_la_persona_est_un_png_carre(client_protege):
    r = client_protege.get("/api/persona/avatar")
    assert r.status_code == 200
    assert r.content.startswith(b"\x89PNG")
    largeur = int.from_bytes(r.content[16:20], "big")
    hauteur = int.from_bytes(r.content[20:24], "big")
    assert largeur == hauteur >= 256


def test_page_cours_renvoie_la_page(client_protege):
    """La page eleve de cours (lot D) doit repondre 200 et servir du HTML."""
    r = client_protege.get("/cours")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "cours.js" in r.text
    assert "cours.css" in r.text


def test_page_studio_renvoie_la_page(client_protege):
    """La page eleve du studio doit etre servie par l'application, comme /cours."""
    r = client_protege.get("/studio")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "studio.js" in r.text
    assert "studio.css" in r.text


def test_cours_html_couvert_par_verification_style_script():
    """cours.html doit bien exister et etre balaye par test_pages_sans_style_ni_script_en_ligne (glob *.html)."""
    from pathlib import Path

    statique = Path(__file__).resolve().parents[1] / "jules" / "web" / "static"
    pages = {p.name for p in statique.glob("*.html")}
    assert "cours.html" in pages


# --- studio (lot C) : fichiers statiques uniquement, le module serveur (lot B) n'existe pas -----
# encore dans ce worktree. Les tests ci-dessous portent sur ce qui EST servi (statique/, /) et sur
# la conformite des fichiers au contrat (docs/STUDIO-CONTRAT.md paragraphe 3 et 6), jamais sur une
# route serveur /api/eleve/studio/... qui n'existe pas encore.


def test_studio_html_couvert_par_verification_style_script():
    """studio.html doit exister et etre balaye par test_pages_sans_style_ni_script_en_ligne (glob *.html)."""
    from pathlib import Path

    statique = Path(__file__).resolve().parents[1] / "jules" / "web" / "static"
    pages = {p.name for p in statique.glob("*.html")}
    assert "studio.html" in pages


def test_studio_fichiers_statiques_servis(client_protege):
    """studio.css et studio.js sont servis publiquement sous /static (comme cours.css/.js)."""
    r_css = client_protege.get("/static/studio.css")
    assert r_css.status_code == 200
    assert "text/css" in r_css.headers["content-type"]
    r_js = client_protege.get("/static/studio.js")
    assert r_js.status_code == 200
    assert "javascript" in r_js.headers["content-type"]


def test_studio_html_reference_ses_scripts_et_styles():
    """studio.html doit charger commun.js, sa propre porte a code et ses propres studio.js/.css."""
    from pathlib import Path

    html = (Path(__file__).resolve().parents[1] / "jules" / "web" / "static" / "studio.html").read_text(
        encoding="utf-8"
    )
    assert "studio.css" in html
    assert "studio.js" in html
    assert "commun.js" in html
    assert 'MS.porte("eleve"' not in html  # la porte est appelee cote JS (studio.js), pas en ligne dans le HTML
    assert 'id="porte"' in html and 'id="porte-form"' in html and 'id="porte-code"' in html


def test_studio_js_utilise_la_porte_eleve_et_les_bons_chemins_api():
    """studio.js doit ouvrir avec MS.porte('eleve', ...) et n'appeler que les chemins du contrat (§3)."""
    import re
    from pathlib import Path

    js = (Path(__file__).resolve().parents[1] / "jules" / "web" / "static" / "studio.js").read_text(encoding="utf-8")
    assert 'MS.porte("eleve"' in js

    chemins_attendus = {
        "/api/eleve/studio/notions",
        "/api/eleve/studio/notions/${encodeURIComponent(notionId)}/creer",
        "/api/eleve/studio/supports/${encodeURIComponent(etat.support.id)}",
        "/api/eleve/studio/supports/${encodeURIComponent(etat.support.id)}/ecrire",
        "/api/eleve/studio/supports/${encodeURIComponent(etat.support.id)}/relire",
        "/api/eleve/studio/supports/${encodeURIComponent(etat.support.id)}/valider",
        "/api/eleve/studio/supports/${encodeURIComponent(etat.support.id)}/devalider",
        "/api/eleve/studio/revisions",
        "/api/eleve/studio/revisions/${encodeURIComponent(carte.support)}/${encodeURIComponent(carte.carte_id)}/reponse",
        "/api/eleve/studio/supports/${encodeURIComponent(carte.support)}",
    }
    trouves = set(re.findall(r"/api/eleve/studio/[^\s`\"')]*", js))
    # chaque chemin trouve doit commencer par un prefixe du contrat (notions, supports, revisions)
    prefixes_valides = (
        "/api/eleve/studio/notions",
        "/api/eleve/studio/supports/",
        "/api/eleve/studio/revisions",
    )
    for chemin in trouves:
        chemin_nettoye = chemin.rstrip("`")
        assert chemin_nettoye.startswith(prefixes_valides), chemin_nettoye
    # et les appels attendus du contrat doivent tous etre presents
    for attendu in chemins_attendus:
        assert attendu in js, attendu


def test_studio_js_appelle_bien_les_methodes_du_contrat():
    """creer, relire, valider, devalider en POST ; ecrire en POST ; DELETE sur un support."""
    from pathlib import Path

    js = (Path(__file__).resolve().parents[1] / "jules" / "web" / "static" / "studio.js").read_text(encoding="utf-8")
    assert "/creer`, MS.json({ type })" in js
    assert "/ecrire`, MS.json({ chemin, valeur })" in js
    assert '/relire`, { method: "POST" }' in js
    assert '/valider`, { method: "POST" }' in js
    assert '/devalider`, { method: "POST" }' in js
    assert 'method: "DELETE"' in js
    import re

    assert re.search(r"/reponse`,\s*MS\.json\(\{\s*reponse\s*\}\)", js)


def test_studio_js_confirme_avant_devalidation_de_cartes_memoire():
    """Dévalider des cartes_memoire doit demander une confirmation explicite (programmation des
    révisions perdue), pas les autres types de support (contrat §6)."""
    from pathlib import Path

    js = (Path(__file__).resolve().parents[1] / "jules" / "web" / "static" / "studio.js").read_text(encoding="utf-8")
    assert "confirmation-devalidation" in js
    assert "cartes_memoire" in js
    # la fonction qui gere le clic sur "Devalider" doit distinguer le type cartes_memoire
    assert "surClicDevalider" in js
    fonction = js[js.index("function surClicDevalider") : js.index("function surClicDevalider") + 400]
    assert "cartes_memoire" in fonction
    assert "confirmation-devalidation" in fonction


def test_studio_css_existe_et_ne_definit_pas_de_style_en_ligne_ailleurs():
    """studio.css doit exister (aucun style en ligne autorise, voir test_pages_sans_style_ni_script_en_ligne)."""
    from pathlib import Path

    css = Path(__file__).resolve().parents[1] / "jules" / "web" / "static" / "studio.css"
    assert css.exists()
    assert len(css.read_text(encoding="utf-8")) > 0


def test_studio_js_echappe_tout_texte_serveur_avant_innerhtml():
    """Toute donnee texte du serveur (titre, contenu, retours) passe par MS.echapper ou MS.markdown
    avant d'aller dans innerHTML, comme dans cours.js (aucune concatenation brute de champ serveur)."""
    from pathlib import Path

    js = (Path(__file__).resolve().parents[1] / "jules" / "web" / "static" / "studio.js").read_text(encoding="utf-8")
    # les endroits ou un champ venant du serveur (titre, texte, contenu, message...) est insere
    # dans du HTML doivent passer par MS.echapper(...) ou MS.markdown(...)
    assert "MS.echapper(" in js
    assert "MS.markdown(" in js
    # pas de gabarit qui insere directement une variable de contenu sans passer par MS.*
    import re

    for gabarit in re.findall(r"\.innerHTML\s*=\s*(`[^`]*`)", js, re.S):
        # chaque interpolation ${...} dans un gabarit HTML doit contenir soit MS.echapper, MS.markdown,
        # soit ne pas venir de donnees serveur variables (ex: classes CSS statiques, compteur numerique)
        for interpolation in re.findall(r"\$\{([^}]*)\}", gabarit):
            interpolation = interpolation.strip()
            if interpolation.startswith("MS.echapper(") or interpolation.startswith("MS.markdown("):
                continue
            # autorise : constantes / longueurs / index numeriques, pas de champ texte libre
            assert re.fullmatch(r"(lbl \? .*: \"\")|[\w.]+(\.length)?( ?[+][+]? ?\d*)?", interpolation), interpolation


def test_page_studio_absente_sans_le_module_serveur(client_protege):
    """Le lot B (module serveur) n'existe pas encore dans ce worktree : documenter l'etat reel
    plutot que d'inventer une route. Si /studio finit par repondre 200 un jour (app.py modifie
    par l'integrateur), ce test echouera et devra etre mis a jour a ce moment-la."""
    r = client_protege.get("/studio")
    assert r.status_code == 404
