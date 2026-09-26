"use strict";
// Frise chronologique : voir docs/OUTILS-CONTRAT.md pour le protocole de messages.
// Deux actions :
//   - afficher_periode (donnees.evenements AVEC leur annee) : simple affichage, rien a deviner.
//   - exercice_remettre_dans_l_ordre (donnees.evenements SANS annee) : l'outil ne connait pas
//     la reponse, l'eleve range les evenements et propose son ordre (regle de fond : un outil
//     ne fait pas le travail a la place de l'eleve).
(function () {
  var app = document.getElementById("app");
  var etat = document.getElementById("etat");

  var ACTIONS = ["afficher_periode", "exercice_remettre_dans_l_ordre"];
  var EVENEMENTS = ["evenement_consulte", "reponse_proposee"];

  function envoyer(evenement, donnees) {
    if (EVENEMENTS.indexOf(evenement) === -1) return;
    window.parent.postMessage({ type: "evenement", evenement: evenement, donnees: donnees || {} }, "*");
  }

  function texte(valeur) {
    return String(valeur === null || valeur === undefined ? "" : valeur);
  }

  function vider(element) {
    while (element.firstChild) element.removeChild(element.firstChild);
  }

  function afficherPeriode(donnees) {
    vider(app);
    var evenements = Array.isArray(donnees.evenements) ? donnees.evenements.slice() : [];
    evenements.sort(function (a, b) { return Number(a.annee) - Number(b.annee); });
    var liste = document.createElement("ol");
    liste.className = "frise";
    evenements.forEach(function (ev) {
      var item = document.createElement("li");
      var bouton = document.createElement("button");
      bouton.type = "button";
      bouton.textContent = texte(ev.annee) + " — " + texte(ev.titre);
      bouton.addEventListener("click", function () {
        envoyer("evenement_consulte", { id: texte(ev.id) });
      });
      item.appendChild(bouton);
      liste.appendChild(item);
    });
    app.appendChild(liste);
    etat.textContent = "Frise affichée : " + evenements.length + " évènement(s).";
  }

  function exerciceRemettreDansLOrdre(donnees) {
    vider(app);
    var evenements = Array.isArray(donnees.evenements) ? donnees.evenements.slice() : [];
    var ordre = evenements.map(function (ev) { return texte(ev.id); });
    var liste = document.createElement("ol");
    liste.className = "frise frise-exercice";

    function parId(id) {
      for (var i = 0; i < evenements.length; i++) {
        if (texte(evenements[i].id) === id) return evenements[i];
      }
      return null;
    }

    function rendre() {
      vider(liste);
      ordre.forEach(function (id, index) {
        var ev = parId(id);
        var item = document.createElement("li");
        var libelle = document.createElement("span");
        libelle.textContent = ev ? texte(ev.titre) : id;
        var boutons = document.createElement("span");
        var haut = document.createElement("button");
        haut.type = "button";
        haut.textContent = "▲";
        haut.setAttribute("aria-label", "Monter " + libelle.textContent);
        haut.disabled = index === 0;
        haut.addEventListener("click", function () {
          var tmp = ordre[index - 1];
          ordre[index - 1] = ordre[index];
          ordre[index] = tmp;
          rendre();
        });
        var bas = document.createElement("button");
        bas.type = "button";
        bas.textContent = "▼";
        bas.setAttribute("aria-label", "Descendre " + libelle.textContent);
        bas.disabled = index === ordre.length - 1;
        bas.addEventListener("click", function () {
          var tmp = ordre[index + 1];
          ordre[index + 1] = ordre[index];
          ordre[index] = tmp;
          rendre();
        });
        boutons.appendChild(haut);
        boutons.appendChild(bas);
        item.appendChild(libelle);
        item.appendChild(boutons);
        liste.appendChild(item);
      });
    }
    rendre();
    app.appendChild(liste);

    var valider = document.createElement("button");
    valider.type = "button";
    valider.textContent = "Proposer cet ordre";
    valider.addEventListener("click", function () {
      envoyer("reponse_proposee", { ordre: ordre });
    });
    app.appendChild(valider);
    etat.textContent = "Range les évènements dans l'ordre, puis propose ton ordre.";
  }

  var GESTIONNAIRES = {
    afficher_periode: afficherPeriode,
    exercice_remettre_dans_l_ordre: exerciceRemettreDansLOrdre
  };

  function recu(event) {
    // Iframe sandbox sans allow-same-origin : event.source est le seul repère fiable
    // (event.origin vaut toujours "null" ici, voir docs/OUTILS-CONTRAT.md).
    if (event.source !== window.parent) return;
    var message = event.data;
    if (!message || typeof message !== "object") return;
    if (message.type !== "action") return;
    if (ACTIONS.indexOf(message.action) === -1) return;
    var gestionnaire = GESTIONNAIRES[message.action];
    if (!gestionnaire) return;
    var donnees = message.donnees && typeof message.donnees === "object" ? message.donnees : {};
    gestionnaire(donnees);
  }

  window.addEventListener("message", recu);
})();
