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

  // --- adaptations : poignee de main avec la page hote (docs/OUTILS-CONTRAT.md, §2) --------
  // Le contenu reste masque (<body hidden>) jusqu'a ce que les leviers de l'eleve soient
  // appliques. Sans reponse de la page apres DELAI_ADAPTATIONS ms, l'outil s'affiche avec les
  // valeurs neutres et le signale ; une reponse tardive valide est quand meme appliquee.
  // Code volontairement duplique dans chaque outil (un outil reste un dossier autonome).
  // Leviers d'affichage (docs/spec/ADAPTATIONS-LOT2.md, §2, EX-105). Les valeurs viennent de la page,
  // mais l'outil les revalide contre les plages et listes fermees du §2 (recopiees ici, comme la
  // poignee de main) : une valeur hors plage ou d'un mauvais type est ignoree, comme un levier inconnu.
  // Les regles CSS correspondantes sont dans outil.css (actives seulement avec l'attribut data-adapt-*).
  var corps = document.body;
  function poser(levier, variable, valeurCss) {
    corps.style.setProperty(variable, valeurCss);
    corps.setAttribute("data-adapt-" + levier, "1");
  }
  function nombre(levier, min, max, appliquer) {
    return function (valeur) {
      if (typeof valeur !== "number" || !isFinite(valeur) || valeur < min || valeur > max) return;
      appliquer(valeur);
      corps.setAttribute("data-adapt-" + levier, String(valeur));
    };
  }
  function choix(levier, variable, table) {
    return function (valeur) {
      if (typeof valeur !== "string" || !Object.prototype.hasOwnProperty.call(table, valeur)) return;
      poser(levier, variable, table[valeur]);
    };
  }
  var LEVIERS = { // levier connu -> function (valeur) ; les autres sont ignores
    "espacement-lettres": nombre("espacement-lettres", 0, 0.18, function (v) {
      corps.style.setProperty("--adapt-espacement-lettres", v + "em");
    }),
    "espacement-mots": nombre("espacement-mots", 0, 0.5, function (v) {
      corps.style.setProperty("--adapt-espacement-mots", v + "em");
    }),
    "interligne": nombre("interligne", 1.55, 2, function (v) {
      corps.style.setProperty("--adapt-interligne", String(v));
    }),
    "longueur-ligne": nombre("longueur-ligne", 1e-9, 80, function (v) {
      corps.style.setProperty("--adapt-longueur-ligne", v + "ch");
    }),
    // L'outil est un document a part : la taille se regle a sa racine (tailles en rem), dans le
    // rapport a la valeur neutre de la page (1,125rem).
    "taille-texte": nombre("taille-texte", 1.125, 1.6875, function (v) {
      document.documentElement.style.fontSize = Math.round(v / 1.125 * 1e6) / 1e4 + "%";
    }),
    "police": choix("police", "--adapt-police", {
      arial: "Arial, \"Liberation Sans\", sans-serif",
      verdana: "Verdana, \"DejaVu Sans\", sans-serif"
    }),
    "fond": choix("fond", "--adapt-fond", { creme: "#FBF5E6", "bleu-pale": "#EEF4FB" })
  };
  var DELAI_ADAPTATIONS = 500;
  var attenteAdaptations = null;

  function afficherContenu(etatAdaptations) {
    document.documentElement.setAttribute("data-adaptations", etatAdaptations);
    document.body.hidden = false;
  }

  function appliquerAdaptations(leviers) {
    if (!leviers || typeof leviers !== "object" || Array.isArray(leviers)) return;
    if (attenteAdaptations !== null) {
      clearTimeout(attenteAdaptations);
      attenteAdaptations = null;
    }
    Object.keys(leviers).forEach(function (nom) {
      if (Object.prototype.hasOwnProperty.call(LEVIERS, nom)) LEVIERS[nom](leviers[nom]);
    });
    afficherContenu("appliquees");
  }

  function poigneeDeMain() {
    attenteAdaptations = setTimeout(function () {
      attenteAdaptations = null;
      afficherContenu("neutres");
      window.parent.postMessage({ type: "adaptations-absentes" }, "*");
    }, DELAI_ADAPTATIONS);
    window.parent.postMessage({ type: "pret" }, "*");
  }

  function recu(event) {
    // Iframe sandbox sans allow-same-origin : event.source est le seul repère fiable
    // (event.origin vaut toujours "null" ici, voir docs/OUTILS-CONTRAT.md).
    if (event.source !== window.parent) return;
    var message = event.data;
    if (!message || typeof message !== "object") return;
    if (message.type === "adaptations") {
      appliquerAdaptations(message.leviers);
      return;
    }
    if (message.type !== "action") return;
    if (ACTIONS.indexOf(message.action) === -1) return;
    var gestionnaire = GESTIONNAIRES[message.action];
    if (!gestionnaire) return;
    var donnees = message.donnees && typeof message.donnees === "object" ? message.donnees : {};
    gestionnaire(donnees);
  }

  window.addEventListener("message", recu);
  poigneeDeMain();
})();
