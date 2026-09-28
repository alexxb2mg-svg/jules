"""Pilote minimal de Chromium headless par le protocole de debogage (CDP), bibliotheque standard seulement.

Sert aux tests qui ont besoin d'une VRAIE entree utilisateur (clic souris, touche clavier) : un `element.click()`
ou un `dispatchEvent` de script ne deplace pas le focus dans une iframe et n'atteint pas le document d'une iframe
a origine opaque. `Input.dispatchMouseEvent` / `Input.dispatchKeyEvent` passent par le navigateur, comme un
eleve : le focus entre reellement dans l'iframe, et Echap part vers le document qui a le focus.

Aucune dependance nouvelle (pas de client websocket installe) : poignee de main HTTP et trames RFC 6455 ecrites
ici, texte seulement, ce qui suffit au CDP. Le navigateur est lance en headless uniquement (aucune fenetre).
"""

from __future__ import annotations

import base64
import contextlib
import json
import os
import socket
import struct
import subprocess
import time
import urllib.request
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


class ErreurCdp(AssertionError):
    """Le navigateur n'a pas repondu comme attendu (demarrage, commande en erreur, delai depasse)."""


class _WebSocket:
    def __init__(self, url: str, delai: float = 30.0) -> None:
        u = urlparse(url)
        self.sock = socket.create_connection((u.hostname or "127.0.0.1", u.port or 80), timeout=delai)
        cle = base64.b64encode(os.urandom(16)).decode()
        requete = (
            f"GET {u.path} HTTP/1.1\r\nHost: {u.hostname}:{u.port}\r\nUpgrade: websocket\r\n"
            f"Connection: Upgrade\r\nSec-WebSocket-Key: {cle}\r\nSec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(requete.encode())
        reponse = b""
        while b"\r\n\r\n" not in reponse:
            morceau = self.sock.recv(4096)
            if not morceau:
                raise ErreurCdp("poignee de main websocket interrompue")
            reponse += morceau
        entete, _, self._tampon = reponse.partition(b"\r\n\r\n")
        if b" 101 " not in entete.split(b"\r\n", 1)[0]:
            raise ErreurCdp(f"poignee de main websocket refusee : {entete[:200]!r}")

    def _lire(self, n: int) -> bytes:
        while len(self._tampon) < n:
            morceau = self.sock.recv(65536)
            if not morceau:
                raise ErreurCdp("websocket fermee par le navigateur")
            self._tampon += morceau
        donnees, self._tampon = self._tampon[:n], self._tampon[n:]
        return donnees

    def envoyer(self, texte: str) -> None:
        charge = texte.encode("utf-8")
        n = len(charge)
        if n < 126:
            entete = struct.pack("!BB", 0x81, 0x80 | n)
        elif n < 65536:
            entete = struct.pack("!BBH", 0x81, 0x80 | 126, n)
        else:
            entete = struct.pack("!BBQ", 0x81, 0x80 | 127, n)
        masque = os.urandom(4)
        masquee = bytes(b ^ masque[i % 4] for i, b in enumerate(charge))
        self.sock.sendall(entete + masque + masquee)

    def recevoir(self) -> str:
        morceaux: list[bytes] = []
        while True:
            b0, b1 = self._lire(2)
            code, fin = b0 & 0x0F, b0 & 0x80
            n = b1 & 0x7F
            if n == 126:
                (n,) = struct.unpack("!H", self._lire(2))
            elif n == 127:
                (n,) = struct.unpack("!Q", self._lire(8))
            charge = self._lire(n)
            if code == 0x8:
                raise ErreurCdp("websocket fermee par le navigateur")
            if code in (0x9, 0xA):  # ping / pong : le navigateur n'en envoie pas au client, ignores
                continue
            morceaux.append(charge)
            if fin:
                return b"".join(morceaux).decode("utf-8")

    def fermer(self) -> None:
        with contextlib.suppress(OSError):
            self.sock.close()


class Page:
    """Une page du navigateur, pilotee par CDP (sessions « flatten » pour les iframes hors processus)."""

    def __init__(self, ws: _WebSocket, session: str) -> None:
        self.ws = ws
        self.session = session
        self._id = 0
        self.evenements: list[dict[str, Any]] = []

    def commande(self, methode: str, session: str | None = None, **params: Any) -> dict[str, Any]:
        self._id += 1
        attendu = self._id
        message: dict[str, Any] = {"id": attendu, "method": methode, "params": params}
        message["sessionId"] = session or self.session
        self.ws.envoyer(json.dumps(message))
        while True:
            recu = json.loads(self.ws.recevoir())
            if recu.get("id") == attendu:
                if "error" in recu:
                    raise ErreurCdp(f"{methode} : {recu['error']}")
                return dict(recu.get("result", {}))
            if "method" in recu:
                self.evenements.append(recu)

    def evaluer(self, expression: str, session: str | None = None, contexte: int | None = None) -> Any:
        params: dict[str, Any] = {"expression": expression, "awaitPromise": True, "returnByValue": True}
        if contexte is not None:
            params["contextId"] = contexte
        r = self.commande("Runtime.evaluate", session=session, **params)
        if "exceptionDetails" in r:
            raise ErreurCdp(f"exception JS : {r['exceptionDetails']}")
        return r["result"].get("value")

    def attendre(self, expression: str, delai: float = 8.0, session: str | None = None) -> Any:
        limite = time.monotonic() + delai
        while True:
            v = self.evaluer(expression, session=session)
            if v:
                return v
            if time.monotonic() > limite:
                raise ErreurCdp(f"attente depassee : {expression}")
            time.sleep(0.05)

    def cliquer(self, x: float, y: float) -> None:
        """Vrai clic souris (appui + relachement) au point (x, y) de la fenetre."""
        for type_ in ("mousePressed", "mouseReleased"):
            self.commande("Input.dispatchMouseEvent", type=type_, x=x, y=y, button="left", clickCount=1)

    def touche(self, cle: str, code: str, touche_windows: int) -> None:
        """Vraie touche clavier, envoyee a l'element qui a le focus (iframe comprise)."""
        commun = {"key": cle, "code": code, "windowsVirtualKeyCode": touche_windows}
        self.commande("Input.dispatchKeyEvent", type="rawKeyDown", **commun)
        self.commande("Input.dispatchKeyEvent", type="keyUp", **commun)

    def sessions_iframes(self) -> list[str]:
        """Sessions des iframes hors processus attachees (Target.setAutoAttach, flatten)."""
        return [
            e["params"]["sessionId"]
            for e in self.evenements
            if e.get("method") == "Target.attachedToTarget" and e["params"]["targetInfo"].get("type") == "iframe"
        ]

    def contextes(self) -> list[dict[str, Any]]:
        """Contextes d'execution vus sur la session de la page (iframes dans le meme processus comprises)."""
        return [
            e["params"]["context"]
            for e in self.evenements
            if e.get("method") == "Runtime.executionContextCreated" and e.get("sessionId") == self.session
        ]


def _port(profil: Path, delai: float = 20.0) -> int:
    fichier = profil / "DevToolsActivePort"
    limite = time.monotonic() + delai
    while time.monotonic() < limite:
        try:
            lignes = fichier.read_text(encoding="utf-8").split() if fichier.is_file() else []
        except PermissionError:  # Windows : Chrome ecrit le fichier au meme instant, on reessaie
            lignes = []
        if lignes:
            return int(lignes[0])
        time.sleep(0.05)
    raise ErreurCdp("le navigateur n'a pas publie son port de debogage")


@contextmanager
def navigateur_cdp(chromium: str, profil: Path, taille: tuple[int, int]) -> Iterator[Page]:
    """Lance Chromium headless (port de debogage choisi par le navigateur) et rend une page vierge pilotee."""
    profil.mkdir(parents=True, exist_ok=True)
    options = [
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--hide-scrollbars",
        "--no-first-run",
        "--no-default-browser-check",
        "--remote-debugging-port=0",
        f"--user-data-dir={profil}",
        f"--window-size={taille[0]},{taille[1]}",
        "about:blank",
    ]
    processus = subprocess.Popen(  # noqa: S603 - navigateur local, arguments fixes
        [chromium, *options], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    ws: _WebSocket | None = None
    try:
        port = _port(profil)
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=10) as r:
            url_ws = json.loads(r.read())["webSocketDebuggerUrl"]
        ws = _WebSocket(url_ws)
        navigateur = Page(ws, "")
        cible = navigateur.commande("Target.createTarget", session=None, url="about:blank")["targetId"]
        session = navigateur.commande("Target.attachToTarget", targetId=cible, flatten=True)["sessionId"]
        page = Page(ws, session)
        page._id = navigateur._id
        page.commande(
            "Emulation.setDeviceMetricsOverride", width=taille[0], height=taille[1], deviceScaleFactor=1, mobile=False
        )
        page.commande("Runtime.enable")
        page.commande("Page.enable")
        page.commande("Target.setAutoAttach", autoAttach=True, waitForDebuggerOnStart=False, flatten=True)
        yield page
    finally:
        if ws is not None:
            ws.fermer()
        processus.kill()
        processus.wait(timeout=20)
