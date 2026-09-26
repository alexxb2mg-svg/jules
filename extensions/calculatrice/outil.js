"use strict";
// Calculatrice : fait les operations (+ - x /), ne resout aucune equation. Calcul sequentiel
// (comme une calculatrice de poche), sans code genere dynamiquement (voir docs/OUTILS-CONTRAT.md).
(function () {
  var app = document.getElementById("app");
  var ACTIONS = ["afficher"];
  var EVENEMENTS = ["calcul_effectue"];

  function envoyer(evenement, donnees) {
    if (EVENEMENTS.indexOf(evenement) === -1) return;
    window.parent.postMessage({ type: "evenement", evenement: evenement, donnees: donnees || {} }, "*");
  }

  var etatCalcul = { affichage: "0", valeur: null, operateur: null, nouveauNombre: true };

  function calculer(a, b, operateur) {
    if (operateur === "+") return a + b;
    if (operateur === "-") return a - b;
    if (operateur === "×") return a * b;
    if (operateur === "÷") return b === 0 ? NaN : a / b;
    return b;
  }

  function formater(nombre) {
    if (Number.isNaN(nombre)) return "Erreur";
    var arrondi = Math.round(nombre * 1e10) / 1e10;
    return String(arrondi);
  }

  var ecran;

  function rafraichir() {
    ecran.textContent = etatCalcul.affichage;
  }

  function saisirChiffre(chiffre) {
    if (etatCalcul.nouveauNombre || etatCalcul.affichage === "0") {
      etatCalcul.affichage = chiffre;
      etatCalcul.nouveauNombre = false;
    } else if (etatCalcul.affichage.length < 14) {
      etatCalcul.affichage += chiffre;
    }
    rafraichir();
  }

  function saisirVirgule() {
    if (etatCalcul.nouveauNombre) {
      etatCalcul.affichage = "0,";
      etatCalcul.nouveauNombre = false;
    } else if (etatCalcul.affichage.indexOf(",") === -1) {
      etatCalcul.affichage += ",";
    }
    rafraichir();
  }

  function nombreAffiche() {
    return parseFloat(etatCalcul.affichage.replace(",", "."));
  }

  function saisirOperateur(operateur) {
    var courant = nombreAffiche();
    if (etatCalcul.valeur !== null && !etatCalcul.nouveauNombre) {
      courant = calculer(etatCalcul.valeur, courant, etatCalcul.operateur);
      etatCalcul.affichage = formater(courant);
    }
    etatCalcul.valeur = courant;
    etatCalcul.operateur = operateur;
    etatCalcul.nouveauNombre = true;
    rafraichir();
  }

  function egal() {
    if (etatCalcul.operateur === null) return;
    var a = etatCalcul.valeur;
    var b = nombreAffiche();
    var resultat = calculer(a, b, etatCalcul.operateur);
    etatCalcul.affichage = formater(resultat);
    envoyer("calcul_effectue", { a: a, b: b, operateur: etatCalcul.operateur, resultat: resultat });
    etatCalcul.valeur = null;
    etatCalcul.operateur = null;
    etatCalcul.nouveauNombre = true;
    rafraichir();
  }

  function effacer() {
    etatCalcul = { affichage: "0", valeur: null, operateur: null, nouveauNombre: true };
    rafraichir();
  }

  var TOUCHES = [
    ["7", "8", "9", "÷"],
    ["4", "5", "6", "×"],
    ["1", "2", "3", "-"],
    ["0", ",", "=", "+"],
    ["C"]
  ];

  function construire() {
    ecran = document.createElement("div");
    ecran.id = "ecran";
    ecran.setAttribute("aria-live", "polite");
    app.appendChild(ecran);

    var pave = document.createElement("div");
    pave.id = "pave";
    TOUCHES.forEach(function (ligne) {
      ligne.forEach(function (touche) {
        var bouton = document.createElement("button");
        bouton.type = "button";
        bouton.textContent = touche;
        if (touche === "=") bouton.className = "egal";
        else if (touche === "C") bouton.className = "efface";
        else if (["+", "-", "×", "÷"].indexOf(touche) !== -1) bouton.className = "operateur";
        bouton.addEventListener("click", function () {
          if (touche === "C") effacer();
          else if (touche === "=") egal();
          else if (touche === ",") saisirVirgule();
          else if (["+", "-", "×", "÷"].indexOf(touche) !== -1) saisirOperateur(touche);
          else saisirChiffre(touche);
        });
        pave.appendChild(bouton);
      });
    });
    app.appendChild(pave);
    rafraichir();
  }

  function recu(event) {
    if (event.source !== window.parent) return;
    var message = event.data;
    if (!message || typeof message !== "object") return;
    if (message.type !== "action") return;
    if (ACTIONS.indexOf(message.action) === -1) return;
    if (message.action === "afficher") effacer();
  }

  window.addEventListener("message", recu);
  construire();
})();
