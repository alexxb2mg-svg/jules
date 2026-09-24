"use strict";
// Lexique : affiche des termes et definitions transmis par la lecon. L'outil n'ajoute ni ne
// devine aucune definition : il montre ce qui lui est donne (voir docs/OUTILS-CONTRAT.md).
(function () {
  var app = document.getElementById("app");
  var etat = document.getElementById("etat");
  var recherche = document.getElementById("recherche");
  var ACTIONS = ["afficher_termes"];
  var EVENEMENTS = ["terme_consulte"];
  var termes = [];

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

  function normaliser(chaine) {
    return chaine
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function rendre(filtre) {
    vider(app);
    var visibles = termes.filter(function (t) {
      if (!filtre) return true;
      return normaliser(texte(t.terme)).indexOf(normaliser(filtre)) !== -1;
    });
    visibles.forEach(function (t) {
      var dt = document.createElement("dt");
      var bouton = document.createElement("button");
      bouton.type = "button";
      bouton.textContent = texte(t.terme);
      bouton.addEventListener("click", function () {
        envoyer("terme_consulte", { id: texte(t.id || t.terme) });
      });
      dt.appendChild(bouton);
      var dd = document.createElement("dd");
      dd.textContent = texte(t.definition);
      app.appendChild(dt);
      app.appendChild(dd);
    });
    etat.textContent = visibles.length + " terme(s) affiché(s).";
  }

  function afficherTermes(donnees) {
    termes = Array.isArray(donnees.termes) ? donnees.termes : [];
    recherche.value = "";
    rendre("");
  }

  var GESTIONNAIRES = { afficher_termes: afficherTermes };

  function recu(event) {
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

  recherche.addEventListener("input", function () {
    rendre(recherche.value);
  });
  window.addEventListener("message", recu);
})();
