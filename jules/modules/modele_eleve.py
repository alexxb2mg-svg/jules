"""Module 'modele_eleve' : le modele chiffre de l'eleve, branche sur Jules (docs/MODELE-ELEVE.md).

Le calcul vit dans jules/apprentissage/ (pur, teste sans IA). Cette brique fait le lien :
  - apres_echange, conversation normale : extraction des faits par le modele 'principal' (§2),
    observations, estimateur, etat de seance (politique) ; le verdict du module suivi sur le meme
    echange devient le capteur jugement_ia ;
  - apres_echange, epreuve terminee (evenement 'epreuve' ecrit par le module epreuve) : prediction,
    lecture du resultat, perte, carnet (surprise -> lecon candidate, evaluation, elagage), calibration ;
  - contribution : reglage de comportement pour le message suivant (§6.4) et lecons (§8.4), jamais
    de chiffre ;
  - routes parent : ce que Jules croit, avec quelle confiance, s'il juge bien, et son carnet (§11).

Stockage (§11), espace 'modele_eleve' :
  notions                  -> {notion: EtatNotion.vers_dict()}
  seance:<conversation>    -> EtatSeance.vers_dict()
  calibration              -> ResultatCalibration.vers_dict() (absent tant qu'elle n'a pas tourne)
  carnet                   -> [Lecon.vers_dict()]
  epreuves_lues            -> [id de conversation d'epreuve deja traitee]
Evenements : 'observation' (une par Observation), 'prediction' (une par notion d'epreuve, avec le
resultat et la perte), 'resultat_epreuve' (ResultatEpreuve). Les etats des notions se reconstruisent a
partir des evenements (reconstruire) : changer un reglage, puis rejouer, redonne un etat coherent.
"""

from __future__ import annotations

import logging
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, HTTPException

from jules.apprentissage import calibration, carnet, estimateurs, mesures, observations, parametres, politique
from jules.apprentissage.etat import EtatNotion, EtatSeance, Lecon, Observation, Prediction, Reglage, ResultatEpreuve
from jules.apprentissage.parametres import Parametres
from jules.llm.base import Tour
from jules.modules.base import Module, extraire_json
from jules.stockage import Conversation, Message, maintenant
from jules.texte import remplir

journal = logging.getLogger("jules.modele_eleve")

ESPACE = "modele_eleve"
MODE_EPREUVE = "epreuve"
FICHIER_POLITIQUE = Path(__file__).resolve().parents[2] / "consignes" / "politique.yaml"
MESSAGES_EXTRAIT = 6
EVENEMENTS_MAX = 100_000


def charger_textes_politique(chemin: Path = FICHIER_POLITIQUE) -> dict[str, dict[str, Any]]:
    """consignes/politique.yaml : un texte par etat, plus les phrases des curseurs (§6.3)."""
    brut = yaml.safe_load(chemin.read_text(encoding="utf-8")) or {}
    return {str(k): dict(v or {}) for k, v in brut.items()}


def texte_reglage(reglage: Reglage, textes: dict[str, dict[str, Any]]) -> str:
    """Assemble la consigne injectee : texte de l'etat + une phrase par curseur non vide (§6.4)."""
    etat = textes.get("etats", {}).get(reglage.etat, {})
    curseurs = textes.get("curseurs", {})
    lignes = [str(etat.get("texte") or "").strip()]
    for nom, valeur in (
        ("etayage", reglage.etayage),
        ("difficulte", reglage.difficulte),
        ("exiger_explication", reglage.exiger_explication),
        ("proposer_pause", reglage.proposer_pause),
    ):
        phrase = str((curseurs.get(nom) or {}).get(valeur) or "").strip()
        if phrase:
            lignes.append(phrase)
    return "\n".join(ligne for ligne in lignes if ligne)


def extrait(conv: Conversation, nb: int = MESSAGES_EXTRAIT) -> str:
    lignes = []
    for m in conv.messages[-nb:]:
        qui = "ÉLÈVE" if m.role == "eleve" else "TUTEUR"
        photo = " [+ photo]" if m.images else ""
        lignes.append(f"{qui}{photo} : {m.texte[:1500]}")
    return "\n".join(lignes)


def libelle_epreuve(cle: str) -> str:
    """« Matiere : notion » (libelle du module epreuve) -> cle du modele, identique par construction."""
    return cle


class Brique(Module):
    id = "modele_eleve"
    titre = "Où en est l'élève, et comment l'accompagner maintenant"

    def __init__(self, tuteur: Any, reglages: dict[str, Any]) -> None:
        super().__init__(tuteur, reglages)
        self.base = parametres.depuis_reglages(reglages)  # refuse une configuration absurde
        self.nom_estimateur = str(reglages.get("estimateur", "bkt"))
        self.modele_analyse = str(reglages.get("modele_analyse", "principal"))
        self.textes = charger_textes_politique()
        self._verrou = threading.RLock()
        self.parametres = self._parametres_effectifs()
        self.estimateur = estimateurs.creer(self.nom_estimateur, self.parametres)

    # --- etat -----------------------------------------------------------------
    @property
    def stockage(self) -> Any:
        return self.tuteur.stockage

    def _parametres_effectifs(self) -> Parametres:
        brut = self.stockage.lire_etat(ESPACE, "calibration", None)
        if not brut or not self.base.calibration_active:
            return self.base
        return calibration.ResultatCalibration.depuis_dict(brut).appliquer(self.base)

    def notions(self) -> dict[str, EtatNotion]:
        brut = self.stockage.lire_etat(ESPACE, "notions", {}) or {}
        return {k: EtatNotion.depuis_dict(v) for k, v in brut.items()}

    def _ecrire_notions(self, etats: dict[str, EtatNotion]) -> None:
        self.stockage.ecrire_etat(ESPACE, "notions", {k: e.vers_dict() for k, e in etats.items()})

    def seance(self, conv_id: str) -> EtatSeance | None:
        brut = self.stockage.lire_etat(ESPACE, f"seance:{conv_id}", None)
        return EtatSeance.depuis_dict(brut) if brut else None

    def lecons(self) -> list[Lecon]:
        return [Lecon.depuis_dict(d) for d in self.stockage.lire_etat(ESPACE, "carnet", []) or []]

    def _ecrire_lecons(self, lecons: list[Lecon]) -> None:
        self.stockage.ecrire_etat(ESPACE, "carnet", [lecon.vers_dict() for lecon in lecons])

    def _observations(self) -> list[Observation]:
        evenements = reversed(self.stockage.evenements("observation", limite=EVENEMENTS_MAX))
        return [Observation.depuis_dict(ev["donnees"]) for ev in evenements]

    def _resultats(self) -> list[ResultatEpreuve]:
        evenements = reversed(self.stockage.evenements("resultat_epreuve", limite=EVENEMENTS_MAX))
        return [ResultatEpreuve.depuis_dict(ev["donnees"]) for ev in evenements]

    def _predictions(self) -> list[dict[str, Any]]:
        return [ev["donnees"] for ev in reversed(self.stockage.evenements("prediction", limite=EVENEMENTS_MAX))]

    def reconstruire(self) -> dict[str, EtatNotion]:
        """Rejoue tous les evenements 'observation' et 'resultat_epreuve' depuis zero (§11), avec les
        parametres effectifs (calibration comprise). Le carnet et les seances ne sont pas touches."""
        with self._verrou:
            self.parametres = self._parametres_effectifs()
            self.estimateur = estimateurs.creer(self.nom_estimateur, self.parametres)
            evenements: list[tuple[str, int, Observation | ResultatEpreuve]] = [
                (o.horodatage, 0, o) for o in self._observations()
            ]
            evenements += [(r.horodatage, 1, r) for r in self._resultats()]
            evenements.sort(key=lambda x: (x[0], x[1]))
            etats: dict[str, EtatNotion] = {}
            for _, _, ev in evenements:
                if isinstance(ev, Observation):
                    etats[ev.notion] = self.estimateur.observer(etats.get(ev.notion), ev, etats)
                elif ev.notion in etats:
                    etats[ev.notion] = self.estimateur.lire_epreuve(etats[ev.notion], ev.tenu, ev.horodatage)
            self._ecrire_notions(etats)
            return etats

    # --- contrat de module ----------------------------------------------------
    def contribution(self, conv: Conversation) -> str | None:
        """§6.4 et §8.4 : jamais de chiffre dans le prompt. Rien en mode epreuve (elle a ses regles)."""
        if conv.mode == MODE_EPREUVE:
            return None
        profil = self.tuteur.profil()
        variables, genre = profil.variables(), profil.genre
        seance = self.seance(conv.id)
        blocs: list[str] = []
        notion = seance.notion if seance else None
        if seance is not None:
            blocs.append(remplir(texte_reglage(politique.reglage(seance), self.textes), variables, genre))
        matiere = estimateurs.matiere_de(notion) if notion else None
        choisies = carnet.pour_le_prompt(self.lecons(), matiere, notion, self.base.lecons_prompt)
        if choisies:
            titre = remplir("Ce que tu as appris de tes erreurs avec {prenom} :", variables, genre)
            blocs.append(titre + "\n" + "\n".join(f"- {lecon.texte}" for lecon in choisies))
        return "\n\n".join(blocs) or None

    def apres_echange(self, conv: Conversation, eleve: Message, bot: Message) -> None:
        """Toute erreur est journalisee par le moteur et n'interrompt jamais la conversation."""
        with self._verrou:
            if conv.mode == MODE_EPREUVE:
                self._traiter_epreuve(conv)
            else:
                self._traiter_echange(conv, eleve)

    # --- echange normal -------------------------------------------------------
    def _notions_connues(self, maximum: int = 40) -> list[str]:
        return sorted(self.notions(), key=lambda k: k)[:maximum]

    def _extraire(self, conv: Conversation) -> list[dict[str, Any]]:
        consigne = observations.CONSIGNE
        connues = self._notions_connues()
        if connues:
            consigne += "\n\nNotions déjà suivies (libellés à reprendre exactement) :\n" + "\n".join(
                f"- {n}" for n in connues
            )
        tours = [Tour(role="user", texte=f"Mode : {conv.mode}\n\n{extrait(conv)}")]
        brut = self.tuteur.llm.repondre(consigne, tours, self.modele_analyse)
        tentatives = observations.lire_extraction(brut)
        if not tentatives and extraire_json(brut) is None:
            journal.warning("Extraction illisible : %s", brut[:200])
        return tentatives

    def _jugement_ia(self, conv: Conversation, horodatage: str) -> Observation | None:
        """Le verdict du module suivi sur CET echange (s'il a tourne avant nous et parle de cette seance)."""
        for ev in self.stockage.evenements("suivi", limite=5):
            if ev.get("conversation") != conv.id:
                continue
            return observations.depuis_statut_suivi(ev["donnees"], conv.id, horodatage)
        return None

    def _traiter_echange(self, conv: Conversation, eleve: Message) -> None:
        horodatage = eleve.horodatage or maintenant()
        nouvelles: list[Observation] = []
        for tentative in self._extraire(conv):
            nouvelles += observations.vers_observations(tentative, conv.id, horodatage, self.parametres)
        jugement = self._jugement_ia(conv, horodatage)
        if jugement is not None:
            nouvelles.append(jugement)
        if not nouvelles:
            return
        etats = self.notions()
        seance = self.seance(conv.id) or EtatSeance(seance=conv.id)
        for obs in nouvelles:
            self.stockage.ajouter_evenement("observation", obs.vers_dict(), conv.id)
            etats[obs.notion] = self.estimateur.observer(etats.get(obs.notion), obs, etats)
            seance = politique.avancer(seance, obs, etats[obs.notion], self.parametres.politique, horodatage)
        self._ecrire_notions(etats)
        self.stockage.ecrire_etat(ESPACE, f"seance:{conv.id}", seance.vers_dict())

    # --- epreuve ----------------------------------------------------------------
    def _traiter_epreuve(self, conv: Conversation) -> None:
        lues = list(self.stockage.lire_etat(ESPACE, "epreuves_lues", []) or [])
        if conv.id in lues:
            return
        bilan = next(
            (ev for ev in self.stockage.evenements("epreuve", limite=50) if ev["conversation"] == conv.id), None
        )
        if bilan is None:
            return  # epreuve en cours : rien a lire
        horodatage = bilan["horodatage"]
        resultats = [(cle, True) for cle in bilan["donnees"].get("tenues", [])]
        resultats += [(cle, False) for cle in bilan["donnees"].get("pas_tenues", [])]
        etats = self.notions()
        lecons = self.lecons()
        for cle, tenu in resultats:
            notion = libelle_epreuve(cle)
            if notion not in etats:
                continue  # notion jamais observee par le modele (epreuve anterieure a son activation)
            prediction = self.estimateur.predire_epreuve(etats[notion], horodatage, conv.id)
            perte = mesures.perte_log(prediction.pi, int(tenu))
            self.stockage.ajouter_evenement(
                "prediction", {**prediction.vers_dict(), "tenu": tenu, "perte": perte}, conv.id
            )
            resultat = ResultatEpreuve(notion, horodatage, tenu, conv.id)
            self.stockage.ajouter_evenement("resultat_epreuve", resultat.vers_dict(), conv.id)
            etats[notion] = self.estimateur.lire_epreuve(etats[notion], tenu, horodatage)
            lecons = carnet.enregistrer_epreuve(lecons, notion, perte, horodatage)
            if self.base.carnet_actif and perte >= self.base.seuil_surprise:
                lecon = self._proposer_lecon(prediction, tenu, perte, lecons)
                if lecon is not None:
                    lecons.append(lecon)
        self._ecrire_notions(etats)
        instant = datetime.fromisoformat(horodatage)
        lecons = [carnet.evaluer(lecon, instant, expiration_jours=self.base.expiration_jours) for lecon in lecons]
        self._ecrire_lecons(carnet.elaguer(lecons, self.base.max_lecons))
        self.stockage.ecrire_etat(ESPACE, "epreuves_lues", [*lues, conv.id][-500:])
        self._recalibrer()

    def _recalibrer(self) -> None:
        """§7 : recale les capteurs sur toutes les donnees, puis reconstruit les etats avec eux."""
        resultats = self._resultats()
        if not self.base.calibration_active or len(resultats) < self.base.epreuves_min:
            return
        resultat = calibration.calibrer(self._observations(), resultats, self.base)
        if resultat is None:
            return
        self.stockage.ecrire_etat(ESPACE, "calibration", resultat.vers_dict())
        self.reconstruire()

    # --- carnet -----------------------------------------------------------------
    def _seance_du_jugement(self, notion: str) -> Conversation | None:
        for ev in self.stockage.evenements("observation", limite=2000):
            if ev["donnees"].get("notion") == notion and ev.get("conversation"):
                return self.stockage.conversation(ev["conversation"])
        return None

    def _pertes_avant(self, lecon: Lecon) -> list[float]:
        return [
            float(p["perte"])
            for p in self._predictions()
            if "perte" in p and carnet.dans_la_portee(lecon, str(p["notion"])) and str(p["horodatage"]) <= lecon.creee
        ]

    def _proposer_lecon(self, prediction: Prediction, tenu: bool, perte: float, lecons: list[Lecon]) -> Lecon | None:
        """§8.1 : une surprise -> le modele 'principal' relit la seance et propose (ou non) UNE lecon.
        Elle ne passe que si le filtre du §8.2 l'accepte ; sinon le refus est journalise."""
        sens = "surestimation" if not tenu else "sous_estimation"
        sens_phrase = "était comprise" if not tenu else "n'était pas encore comprise"
        conv = self._seance_du_jugement(prediction.notion)
        seance_texte = extrait(conv, 30) if conv is not None else "(séance introuvable)"
        tours = [
            Tour(
                role="user",
                texte=(
                    f"Notion : {prediction.notion}\nRésultat de l'épreuve : {'a tenu' if tenu else 'n a pas tenu'}"
                    f"\n\nSéance où tu avais porté ton jugement :\n{seance_texte}"
                ),
            )
        ]
        brut = self.tuteur.llm.repondre(carnet.CONSIGNE_LECON.format(sens_phrase=sens_phrase), tours, "principal")
        objet = extraire_json(brut) or {}
        proposee = objet.get("lecon")
        if not isinstance(proposee, dict):
            return None  # « rien a retenir » est une reponse legitime
        portee = str(proposee.get("portee") or "notion")
        cle = {"notion": prediction.notion, "matiere": estimateurs.matiere_de(prediction.notion), "global": ""}.get(
            portee, ""
        )
        lecon = Lecon(
            id=uuid.uuid4().hex[:8],
            portee=portee,  # type: ignore[arg-type]  # verifiee par motif_refus
            cle=cle,
            sens=sens,  # type: ignore[arg-type]
            texte=str(proposee.get("texte") or "").strip(),
            creee=prediction.horodatage,
        )
        motif = carnet.motif_refus(lecon, lecons)
        if motif is not None:
            journal.info("Lecon refusee (%s) : %s", motif, lecon.texte[:200])
            return None
        lecon.pertes_avant = self._pertes_avant(lecon) or [perte]
        return lecon

    # --- pour le module epreuve --------------------------------------------------
    def notions_a_reviser(self, maximum: int) -> list[dict[str, str]]:
        """§5.4 : notions dont la retention predite est passee sous la cible, au format du module epreuve."""
        etats = [e for e in self.notions().values() if estimateurs.p_de(e) >= 0.5]
        sortie = []
        for e in estimateurs.a_reviser(etats, maintenant(), self.parametres.retention_cible, maximum):
            matiere, _, nom = e.notion.partition(" : ")
            sortie.append({"matiere": matiere, "notion": nom, "jour": (e.derniere_revision or "")[:10]})
        return sortie

    # --- page parent --------------------------------------------------------------
    def vue_notions(self) -> list[dict[str, Any]]:
        instant = maintenant()
        sortie = []
        for e in self.notions().values():
            p = estimateurs.p_de(e)
            bas, haut = estimateurs.intervalle_wilson(p, e.n_eff)
            sortie.append(
                {
                    "notion": e.notion,
                    "p": round(p, 3),
                    "fourchette": [round(bas, 3), round(haut, 3)],
                    "preuves": round(e.n_eff, 1),
                    "retention": round(estimateurs.retention_actuelle(e, instant), 3),
                    "stabilite_jours": None if e.stabilite is None else round(e.stabilite, 1),
                }
            )
        return sorted(sortie, key=lambda n: n["notion"])

    def vue_fiabilite(self) -> dict[str, Any]:
        predictions = [p for p in self._predictions() if "tenu" in p][-self.base.fenetre_mesure :]
        pis = [float(p["pi"]) for p in predictions]
        ys = [int(bool(p["tenu"])) for p in predictions]
        calib = self.stockage.lire_etat(ESPACE, "calibration", None)
        return {
            "epreuves": len(ys),
            "brier": mesures.brier(pis, ys) if ys else None,
            "brier_reference": mesures.brier_climatologie(ys) if ys else None,
            "ece": mesures.ece(pis, ys) if ys else None,
            "table": [c.__dict__ for c in mesures.table_fiabilite(pis, ys)] if ys else [],
            "calibration": calib,
            "avertissement": "Estimations sur peu d'épreuves : ce sont des repères, pas des mesures.",
        }

    def routes(self) -> APIRouter:
        routeur = APIRouter()

        @routeur.get("/notions")
        def notions() -> list[dict[str, Any]]:
            return self.vue_notions()

        @routeur.get("/fiabilite")
        def fiabilite() -> dict[str, Any]:
            return self.vue_fiabilite()

        @routeur.get("/lecons")
        def lecons() -> list[dict[str, Any]]:
            return [lecon.vers_dict() for lecon in self.lecons()]

        @routeur.delete("/lecons/{lecon_id}")
        def retirer(lecon_id: str) -> dict[str, bool]:
            with self._verrou:
                toutes = self.lecons()
                if not any(lecon.id == lecon_id for lecon in toutes):
                    raise HTTPException(404, "Leçon inconnue")
                for lecon in toutes:
                    if lecon.id == lecon_id:
                        lecon.statut, lecon.motif_retrait = "retiree", "retiree par le parent"
                self._ecrire_lecons(toutes)
            return {"ok": True}

        @routeur.post("/reinitialiser")
        def reinitialiser() -> dict[str, int]:
            return {"notions": len(self.reconstruire())}

        return routeur
