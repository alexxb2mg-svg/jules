"""Moteurs d'IA : format des requetes, sans aucun appel reseau reel (transport simule)."""

from __future__ import annotations

import json

import httpx
import pytest

from jules.llm import anthropic, demo, openai_compatible
from jules.llm.base import ErreurLLM, Tour, nettoyer

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 20


def client_simule(reponse: dict, statut: int = 200):
    requetes: list[httpx.Request] = []

    def gerer(requete: httpx.Request) -> httpx.Response:
        requetes.append(requete)
        return httpx.Response(statut, json=reponse)

    return httpx.Client(transport=httpx.MockTransport(gerer)), requetes


def test_anthropic_requete_et_reponse(monkeypatch, tmp_path):
    monkeypatch.setenv("CLE_TEST", "sk-test")
    image = tmp_path / "exo.png"
    image.write_bytes(PNG)
    client, requetes = client_simule({"content": [{"type": "text", "text": "Bonjour !"}]})
    moteur = anthropic.Brique({"cle_env": "CLE_TEST", "modeles": {"principal": "m-p", "rapide": "m-r"}}, client)
    assert moteur.repondre("sys", [Tour("user", "", [image])], "rapide") == "Bonjour !"
    envoye = json.loads(requetes[0].content)
    assert requetes[0].headers["x-api-key"] == "sk-test"
    assert envoye["model"] == "m-r" and envoye["system"] == "sys"
    assert envoye["messages"][0]["content"][0]["source"]["media_type"] == "image/png"


def test_openai_compatible_ollama_sans_cle(tmp_path):
    client, requetes = client_simule({"choices": [{"message": {"content": "<think>hmm</think>Salut"}}]})
    moteur = openai_compatible.Brique({"url": "http://127.0.0.1:11434/v1/", "modeles": {"principal": "qwen"}}, client)
    assert moteur.repondre("sys", [Tour("user", "Bonjour")]) == "Salut"
    assert str(requetes[0].url) == "http://127.0.0.1:11434/v1/chat/completions"
    assert "authorization" not in requetes[0].headers
    assert json.loads(requetes[0].content)["messages"][0] == {"role": "system", "content": "sys"}


def test_openai_compatible_modele_sans_vision(tmp_path):
    image = tmp_path / "exo.png"
    image.write_bytes(PNG)
    client, requetes = client_simule({"choices": [{"message": {"content": "ok"}}]})
    moteur = openai_compatible.Brique({"url": "http://x/v1", "modeles": {"principal": "m"}, "images": False}, client)
    moteur.repondre("sys", [Tour("user", "voilà", [image])])
    assert "ne sait pas lire les images" in json.loads(requetes[0].content)["messages"][1]["content"]


def test_erreur_http_remontee_proprement(monkeypatch):
    monkeypatch.setenv("CLE_TEST", "sk-test")
    client, _ = client_simule({"error": "quota"}, statut=429)
    moteur = anthropic.Brique({"cle_env": "CLE_TEST", "modeles": {"principal": "m"}}, client)
    with pytest.raises(ErreurLLM, match="429"):
        moteur.repondre("sys", [Tour("user", "x")])


def test_cle_absente_message_clair(monkeypatch):
    monkeypatch.delenv("CLE_ABSENTE", raising=False)
    with pytest.raises(ErreurLLM, match="CLE_ABSENTE"):
        anthropic.Brique({"cle_env": "CLE_ABSENTE", "modeles": {"principal": "m"}})


def test_modele_manquant_refuse(monkeypatch):
    monkeypatch.setenv("CLE_TEST", "sk-test")
    with pytest.raises(ErreurLLM, match="principal"):
        anthropic.Brique({"cle_env": "CLE_TEST"})


def test_demo_fonctionne_sans_rien():
    moteur = demo.Brique({})
    assert "mode démo" in moteur.repondre("sys", [Tour("user", "x")])
    assert json.loads(moteur.repondre("Réponds en JSON", [], "rapide"))["niveau"] == "aucun"


def test_nettoyer_blocs_de_reflexion():
    assert nettoyer("<think>\nplan\n</think>\n Réponse ") == "Réponse"


def test_parametres_supplementaires_sans_ecraser_l_essentiel():
    corps = openai_compatible.corps_requete(
        "sys", [Tour("user", "x")], "m", 100, True, {"reasoning_effort": "none", "model": "autre"}
    )
    assert corps["reasoning_effort"] == "none"
    assert corps["model"] == "m"
