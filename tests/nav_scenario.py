"""Banc de test navigateur par scenario (docs/spec/NAVIGATION.md, section 6).

Un vrai serveur Jules (uvicorn, 127.0.0.1) sert les pages de production ; une enveloppe ASGI, qui
n'existe qu'ici, ajoute trois choses **uniquement en test** :

- la route `/_test/scenario-nav.js` : la bibliotheque de scenario (objet `S`) suivie des etapes du test ;
- dans chaque page HTML servie, la balise `<script src="/_test/scenario-nav.js">` juste apres `<head>`,
  pour que l'enveloppe de `fetch` soit posee avant les scripts de la page ;
- des reponses d'API simulees (`/api/session`, jeu de notions genere par le test...) : chemin exact -> JSON.

Le HTML de production n'est pas modifie sur disque. Chromium headless tourne en `--dump-dom` avec une taille
de fenetre reglable ; le scenario ecrit son resultat en JSON dans `<pre id="resultat-scenario">`, relu ici.

Aucune dependance nouvelle : ni Playwright, ni axe-core, ni client websocket.

`JULES_CHROMIUM_OBLIGATOIRE=1` : l'absence de Chromium fait echouer le test au lieu de le sauter.

Dans les etapes (corps d'une fonction `async (S) => { ... }` qui renvoie une valeur serialisable en JSON) :

- `S.el(sel)` : l'element (erreur nommee s'il manque) ; `await S.attendre(sel_ou_fonction, ms)` ;
- actions : `S.clic(sel)` (`element.click()`), `S.echap(sel?)` (`keydown` Echap), `S.focus(sel)` ;
- lectures : `S.titre()`, `S.aria(sel)`, `S.style(sel, proprietes)`, `S.rect(sel)`, `S.actif()`,
  `S.stockage()` (`localStorage`), `S.api()` (chemins `/api/...` appeles par `fetch`, dans l'ordre),
  `S.appels()` (idem avec la methode), `S.requetes()` (chemin + parametres), `S.erreurs()` (console.error,
  exceptions et promesses rejetees de la page) ;
- `await S.pause(ms)` : laisse tourner le temps (virtuel) de la page.
"""

from __future__ import annotations

import contextlib
import html
import json
import os
import re
import signal
import socket
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

from jules.chantier_visuel import _chromium

VARIABLE_OBLIGATOIRE = "JULES_CHROMIUM_OBLIGATOIRE"
CHEMIN_SCENARIO = "/_test/scenario-nav.js"
BALISE_SCENARIO = f'<script src="{CHEMIN_SCENARIO}"></script>'
RESULTAT = re.compile(r'<pre id="resultat-scenario"[^>]*>(.*?)</pre>', re.S)
# Delai reel d'un scenario = DELAI_FIXE_S + budget virtuel. Un scenario rendu prend 1 a 10 s ; au-dela, le
# navigateur est bloque et le test echoue avec un message lisible (au lieu de 120 s par test).
DELAI_FIXE_S = 45

BIBLIOTHEQUE_JS = r""""use strict";
// Banc de scenario (tests/nav_scenario.py) : injecte seulement en test, avant les scripts de la page.
(function () {
  var appels = [];
  var fetchOrigine = window.fetch.bind(window);
  window.fetch = function (entree, options) {
    try {
      var brut = typeof entree === "string" ? entree : (entree && entree.url) || String(entree);
      var url = new URL(brut, location.href);
      if (url.origin === location.origin && url.pathname.indexOf("/api/") === 0) {
        var methode = (options && options.method) || (entree && entree.method) || "GET";
        appels.push({ methode: String(methode).toUpperCase(), chemin: url.pathname, requete: url.search });
      }
    } catch (e) { /* une adresse illisible n'empeche pas l'appel */ }
    return fetchOrigine(entree, options);
  };

  // Erreurs de la page : console.error, exceptions non rattrapees, promesses rejetees sans gestionnaire.
  var erreurs = [];
  var consoleErreur = console.error.bind(console);
  console.error = function () {
    erreurs.push(Array.prototype.map.call(arguments, String).join(" "));
    return consoleErreur.apply(null, arguments);
  };
  window.addEventListener("error", function (ev) { erreurs.push("error: " + (ev.message || String(ev.error))); });
  window.addEventListener("unhandledrejection", function (ev) {
    erreurs.push("unhandledrejection: " + String(ev.reason && (ev.reason.stack || ev.reason)));
  });

  function el(sel) {
    if (typeof sel !== "string") return sel;
    var e = document.querySelector(sel);
    if (!e) throw new Error("element introuvable : " + sel);
    return e;
  }
  function pause(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }

  var S = {
    el: el,
    pause: pause,
    attendre: async function (condition, ms) {
      var limite = performance.now() + (ms || 3000);
      var essai = typeof condition === "string"
        ? function () { return document.querySelector(condition); }
        : condition;
      for (;;) {
        var v = essai();
        if (v) return v;
        if (performance.now() > limite) throw new Error("attente depassee : " + String(condition));
        await pause(20);
      }
    },
    clic: function (sel) { el(sel).click(); },
    echap: function (sel) {
      var cible = sel ? el(sel) : (document.activeElement || document.body);
      var options = { key: "Escape", code: "Escape", bubbles: true, cancelable: true };
      cible.dispatchEvent(new KeyboardEvent("keydown", options));
    },
    focus: function (sel) { el(sel).focus(); },
    titre: function () { return document.title; },
    aria: function (sel) {
      var e = el(sel), r = {};
      for (var i = 0; i < e.attributes.length; i++) {
        var a = e.attributes[i];
        if (a.name.indexOf("aria-") === 0 || a.name === "role") r[a.name] = a.value;
      }
      return r;
    },
    style: function (sel, proprietes) {
      var s = getComputedStyle(el(sel)), r = {};
      (proprietes || []).forEach(function (p) { r[p] = s.getPropertyValue(p); });
      return r;
    },
    rect: function (sel) {
      var b = el(sel).getBoundingClientRect();
      return {
        x: b.x, y: b.y, largeur: b.width, hauteur: b.height,
        haut: b.top, bas: b.bottom, gauche: b.left, droite: b.right
      };
    },
    actif: function () {
      var a = document.activeElement;
      if (!a) return null;
      return {
        balise: a.tagName.toLowerCase(), id: a.id || null, classes: a.className || null,
        texte: (a.textContent || "").trim().slice(0, 80)
      };
    },
    stockage: function () {
      var r = {};
      for (var i = 0; i < localStorage.length; i++) { var k = localStorage.key(i); r[k] = localStorage.getItem(k); }
      return r;
    },
    api: function () { return appels.map(function (a) { return a.chemin; }); },
    appels: function () { return appels.map(function (a) { return { methode: a.methode, chemin: a.chemin }; }); },
    requetes: function () { return appels.map(function (a) { return a.chemin + a.requete; }); },
    erreurs: function () { return erreurs.slice(); },
  };

  function ecrire(objet) {
    var pre = document.createElement("pre");
    pre.id = "resultat-scenario";
    pre.hidden = true;
    objet.fenetre = [innerWidth, innerHeight];
    pre.textContent = JSON.stringify(objet);
    document.body.appendChild(pre);
  }

  window.__scenarioNav = {
    S: S,
    lancer: function (etapes) {
      window.addEventListener("load", function () {
        Promise.resolve()
          .then(function () { return etapes(S); })
          .then(function (valeur) { ecrire({ ok: true, valeur: valeur === undefined ? null : valeur }); },
                function (err) { ecrire({ ok: false, erreur: String((err && err.stack) || err) }); });
      });
    },
  };
})();
"""


class ErreurScenario(AssertionError):
    """Le scenario n'a pas abouti : exception JS, attente depassee ou resultat absent du DOM."""


def _tuer_groupe(pid: int) -> None:
    """POSIX : tue tout le groupe de processus cree par `start_new_session=True` (zygote, rendu, GPU)."""
    if sys.platform != "win32":
        with contextlib.suppress(ProcessLookupError):
            os.killpg(pid, signal.SIGKILL)


def _tuer_arbre(processus: subprocess.Popen[str]) -> None:
    """Tue le navigateur ET ses enfants : `Popen.kill` seul laisse des orphelins."""
    if sys.platform == "win32":
        taskkill = Path(os.environ.get("SYSTEMROOT", "C:/Windows")) / "System32" / "taskkill.exe"
        subprocess.run(  # noqa: S603 - pid de notre propre enfant, executable systeme en chemin complet
            [str(taskkill), "/PID", str(processus.pid), "/T", "/F"], capture_output=True, check=False
        )
    _tuer_groupe(processus.pid)
    processus.kill()


def executer_navigateur(commande: list[str], delai: float) -> subprocess.CompletedProcess[str]:
    """Lance le navigateur dans son propre groupe de processus, avec un delai maximal. Sur depassement (ou
    toute autre exception, y compris Ctrl-C), tout l'arbre est tue avant de relancer l'exception."""
    groupe: dict[str, Any] = {}
    if sys.platform == "win32":
        groupe["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        groupe["start_new_session"] = True
    processus = subprocess.Popen(  # noqa: S603 - navigateur local, arguments fixes
        commande,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        **groupe,
    )
    try:
        sortie, erreurs = processus.communicate(timeout=delai)
    except BaseException:
        _tuer_arbre(processus)
        # Borne aussi la vidange : un petit-enfant rescape qui tiendrait encore le tube ne doit pas bloquer.
        with contextlib.suppress(subprocess.TimeoutExpired):
            processus.communicate(timeout=10)
        raise
    # --dump-dom termine le processus principal ; un enfant encore vivant dans le groupe serait un orphelin.
    _tuer_groupe(processus.pid)
    return subprocess.CompletedProcess(commande, processus.returncode, sortie, erreurs)


def navigateur() -> str:
    """Chemin de Chromium ; sinon `skip`, ou echec si JULES_CHROMIUM_OBLIGATOIRE=1 (un test ignore compte
    comme un echec, spec section 6)."""
    chemin = _chromium()
    if chemin:
        return chemin
    message = "Chromium absent (definir JULES_CHROMIUM)"
    if os.environ.get(VARIABLE_OBLIGATOIRE) == "1":
        pytest.fail(f"{message} et {VARIABLE_OBLIGATOIRE}=1 : le test ne peut pas etre ignore", pytrace=False)
    pytest.skip(message)
    raise AssertionError("inatteignable")  # pytest.skip leve toujours ; pour mypy et ruff


class EnveloppeTest:
    """Application ASGI de test autour de l'app Jules : scenario, injection de la balise, API simulee."""

    def __init__(self, app: Callable[..., Any]) -> None:
        self.app = app
        self.script = ""
        self.simulees: dict[str, Any] = {}
        # Fichiers statiques remplaces pour un seul scenario (tests de mutation) : chemin -> texte JS.
        self.remplaces: dict[str, str] = {}
        # Pannes simulees : chemin d'API exact -> nombre de reponses 500 a renvoyer avant de laisser passer.
        self.pannes: dict[str, int] = {}

    async def __call__(self, scope: dict[str, Any], receive: Callable[..., Any], send: Callable[..., Any]) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        chemin = scope["path"]
        if self.pannes.get(chemin, 0) > 0:
            self.pannes[chemin] -= 1
            await _repondre(send, b'{"detail": "panne simulee"}', "application/json", statut=500)
            return
        if chemin == CHEMIN_SCENARIO:
            await _repondre(send, self.script.encode("utf-8"), "text/javascript; charset=utf-8")
            return
        if chemin in self.remplaces:
            await _repondre(send, self.remplaces[chemin].encode("utf-8"), "text/javascript; charset=utf-8")
            return
        if chemin in self.simulees and scope["method"] == "GET":
            corps = json.dumps(self.simulees[chemin], ensure_ascii=False).encode("utf-8")
            await _repondre(send, corps, "application/json")
            return
        if chemin.startswith(("/api/", "/static/")):
            await self.app(scope, receive, send)
            return

        debut: dict[str, Any] = {}
        morceaux: list[bytes] = []

        async def retenir(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                debut.update(message)
                return
            morceaux.append(message.get("body", b""))
            if message.get("more_body"):
                return
            corps = b"".join(morceaux)
            entetes = [(k, v) for k, v in debut.get("headers", []) if k.lower() != b"content-length"]
            type_ = {k.lower(): v for k, v in entetes}.get(b"content-type", b"")
            if type_.startswith(b"text/html"):
                corps = _injecter(corps.decode("utf-8")).encode("utf-8")
            entetes.append((b"content-length", str(len(corps)).encode()))
            await send({**debut, "headers": entetes})
            await send({"type": "http.response.body", "body": corps})

        await self.app(scope, receive, retenir)


def _injecter(page: str) -> str:
    if "<head>" not in page:
        raise ErreurScenario("page HTML sans <head> : impossible d'injecter le scenario")
    return page.replace("<head>", "<head>\n  " + BALISE_SCENARIO, 1)


async def _repondre(send: Callable[..., Any], corps: bytes, type_: str, statut: int = 200) -> None:
    entetes = [
        (b"content-type", type_.encode()),
        (b"content-length", str(len(corps)).encode()),
        (b"cache-control", b"no-store"),
    ]
    await send({"type": "http.response.start", "status": statut, "headers": entetes})
    await send({"type": "http.response.body", "body": corps})


def _port_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


class Banc:
    """Un serveur Jules de test et un Chromium headless : `jouer()` ouvre une page et rend la valeur du scenario."""

    def __init__(self, enveloppe: EnveloppeTest, url: str, chromium: str, profils: Path) -> None:
        self.enveloppe = enveloppe
        self.url = url
        self.chromium = chromium
        self.profils = profils
        self._n = 0
        self.derniere_sortie = ""
        self.bloque = ""  # raison du premier blocage du navigateur ; les scenarios suivants echouent sans attendre

    def jouer(
        self,
        chemin: str,
        etapes: str,
        *,
        taille: tuple[int, int] = (1280, 800),
        avant: str = "",
        simulees: dict[str, Any] | None = None,
        remplaces: dict[str, str] | None = None,
        pannes: dict[str, int] | None = None,
        budget_ms: int = 5000,
    ) -> Any:
        """Ouvre `chemin` a la taille `taille` (largeur, hauteur) et joue `etapes`, corps JS d'une fonction
        `async (S) => { ... }`. `avant` s'execute avant les scripts de la page (ex. remplir localStorage).
        `simulees` : chemin d'API exact -> JSON renvoye a la place du vrai serveur (GET seulement).
        `remplaces` : chemin d'un script statique -> texte servi a sa place (tests de mutation).
        `pannes` : chemin d'API exact -> nombre de reponses 500 renvoyees avant de laisser passer."""
        self.enveloppe.simulees = dict(simulees or {})
        self.enveloppe.remplaces = dict(remplaces or {})
        self.enveloppe.pannes = dict(pannes or {})
        self.enveloppe.script = (
            BIBLIOTHEQUE_JS
            + f"\n(function () {{\n{avant}\n}})();\n"
            + f"window.__scenarioNav.lancer(async function (S) {{\n{etapes}\n}});\n"
        )
        self._n += 1
        options = [
            "--headless=new",
            "--no-sandbox",
            "--disable-gpu",
            "--hide-scrollbars",
            "--no-first-run",
            "--no-default-browser-check",
            f"--user-data-dir={self.profils / f'profil-{self._n}'}",
            f"--window-size={taille[0]},{taille[1]}",
            f"--virtual-time-budget={budget_ms}",
            "--dump-dom",
        ]
        if self.bloque:
            # Un navigateur qui ne rend pas la page ne la rendra pas mieux au scenario suivant : on echoue
            # tout de suite au lieu d'attendre le delai a chaque test (sinon le job CI finit annule).
            raise ErreurScenario(f"scenario non joue sur {chemin} : {self.bloque}")
        delai = DELAI_FIXE_S + budget_ms / 1000
        try:
            execution = executer_navigateur([self.chromium, *options, self.url + chemin], delai)
        except subprocess.TimeoutExpired:
            self.bloque = (
                f"{self.chromium} n'a rien rendu en {delai:.0f} s sur {chemin} (budget virtuel {budget_ms} ms) ; "
                "sous Linux, /usr/bin/chromium (snapshot) reste bloque en --dump-dom : "
                "definir JULES_CHROMIUM vers chrome-headless-shell"
            )
            raise ErreurScenario(self.bloque) from None
        self.derniere_sortie = execution.stdout
        trouve = RESULTAT.search(execution.stdout)
        if not trouve:
            raise ErreurScenario(
                f"pas de <pre id=resultat-scenario> (code {execution.returncode}) ; stderr : {execution.stderr[-1500:]}"
            )
        resultat = json.loads(html.unescape(trouve.group(1)))
        if resultat.get("fenetre") != list(taille):
            # Chrome « complet » en --headless=new impose une largeur minimale (500 px) et retire la barre
            # d'outils de la hauteur : innerWidth x innerHeight ne vaut pas --window-size. Chrome Headless
            # Shell (ou Chrome for Testing) respecte la taille demandee. Un test de mise en page mesure a une
            # taille fausse ne prouve rien : on echoue plutot que de mesurer a cote.
            raise ErreurScenario(
                f"fenetre obtenue {resultat.get('fenetre')} au lieu de {list(taille)} avec {self.chromium} : "
                "definir JULES_CHROMIUM vers chrome-headless-shell (Chrome for Testing), qui respecte --window-size"
            )
        if not resultat.get("ok"):
            raise ErreurScenario(f"scenario en echec sur {chemin} : {resultat.get('erreur')}")
        return resultat["valeur"]


@contextmanager
def banc_navigation(app: Callable[..., Any], dossier: Path) -> Iterator[Banc]:
    """Demarre l'app (enveloppee) sur 127.0.0.1 et rend un Banc ; tout s'arrete a la sortie."""
    import uvicorn

    chromium = navigateur()
    enveloppe = EnveloppeTest(app)
    port = _port_libre()
    serveur = uvicorn.Server(uvicorn.Config(enveloppe, host="127.0.0.1", port=port, log_level="warning"))
    fil = threading.Thread(target=serveur.run, daemon=True)
    fil.start()
    limite = time.time() + 20
    while not serveur.started and time.time() < limite:
        time.sleep(0.05)
    if not serveur.started:
        raise ErreurScenario("le serveur de test n'a pas demarre")
    try:
        yield Banc(enveloppe, f"http://127.0.0.1:{port}", chromium, dossier)
    finally:
        serveur.should_exit = True
        fil.join(timeout=10)
