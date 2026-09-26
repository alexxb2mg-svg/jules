"""Extension d'exemple : observe `bloc_consulte` et `fin_de_seance`, sans appeler aucun modele d'IA.

Chaque evenement recu est ecrit dans le journal de l'eleve (type "observateur-exemple"). Une vraie
extension (Jules commentateur, rapport de fin de seance...) part de la meme forme : une classe
`Brique(Module)` qui ne surcharge que les points d'accroche dont elle a besoin.
"""

from __future__ import annotations

from jules.modules.base import Module


class Brique(Module):
    id = "exemple_observateur"

    def bloc_consulte(self, conv, adresse, notion=None):
        self.tuteur.stockage.ajouter_evenement(
            "observateur-exemple",
            {"point": "bloc_consulte", "adresse": adresse, "notion": notion},
            conv.id if conv else None,
        )

    def fin_de_seance(self, conv):
        self.tuteur.stockage.ajouter_evenement(
            "observateur-exemple", {"point": "fin_de_seance"}, conv.id if conv else None
        )
