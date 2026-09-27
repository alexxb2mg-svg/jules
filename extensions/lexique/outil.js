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

  recherche.addEventListener("input", function () {
    rendre(recherche.value);
  });
  window.addEventListener("message", recu);
  poigneeDeMain();
})();
