"use strict";
// Calculatrice scientifique : operations de base + fonctions scientifiques pour maths et physique.
// Calcul sequentiel + fonctions immediates, sans code genere dynamiquement (docs/OUTILS-CONTRAT.md).
(function () {
  var app = document.getElementById("app");
  var ACTIONS = ["afficher"];
  var EVENEMENTS = ["calcul_effectue", "fermer"];

  function envoyer(evenement, donnees) {
    if (EVENEMENTS.indexOf(evenement) === -1) return;
    window.parent.postMessage({ type: "evenement", evenement: evenement, donnees: donnees || {} }, "*");
  }

  // --- Etat ---
  var etatCalcul = { affichage: "0", valeur: null, operateur: null, nouveauNombre: true, degres: true };

  // --- Calculs de base ---
  function calculer(a, b, operateur) {
    if (operateur === "+") return a + b;
    if (operateur === "-") return a - b;
    if (operateur === "×") return a * b;
    if (operateur === "÷") return b === 0 ? NaN : a / b;
    if (operateur === "^") return Math.pow(a, b);
    return b;
  }

  function formater(nombre) {
    if (Number.isNaN(nombre) || !Number.isFinite(nombre)) return "Erreur";
    var arrondi = Math.round(nombre * 1e10) / 1e10;
    var texte = String(arrondi);
    if (texte.length > 14) texte = nombre.toPrecision(10);
    return texte;
  }

  var ecran;
  var indicateurMode;
  var reperesRang = false; // levier reperes-rang-chiffres (voir LEVIERS plus bas)
  var RANGS = ["rang-unites", "rang-dizaines", "rang-centaines"];

  function rafraichir() {
    if (indicateurMode) indicateurMode.textContent = etatCalcul.degres ? "DEG" : "RAD";
    var texte = etatCalcul.affichage;
    if (!reperesRang || !/^-?\d+(,\d*)?$/.test(texte)) {
      ecran.textContent = texte;
      return;
    }
    // Chiffres de la partie entiere colores par rang, en partant de la virgule (ou de la fin).
    ecran.textContent = "";
    var finEntier = texte.indexOf(",") === -1 ? texte.length : texte.indexOf(",");
    for (var i = 0; i < texte.length; i++) {
      var rang = finEntier - 1 - i;
      if (i < finEntier && rang < RANGS.length && /\d/.test(texte[i])) {
        var chiffre = document.createElement("span");
        chiffre.className = RANGS[rang];
        chiffre.textContent = texte[i];
        ecran.appendChild(chiffre);
      } else {
        ecran.appendChild(document.createTextNode(texte[i]));
      }
    }
  }

  function nombreAffiche() {
    return parseFloat(etatCalcul.affichage.replace(",", "."));
  }

  // --- Saisie ---
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
    etatCalcul = { affichage: "0", valeur: null, operateur: null, nouveauNombre: true, degres: etatCalcul.degres };
    rafraichir();
  }

  function retour() {
    if (etatCalcul.affichage.length > 1) {
      etatCalcul.affichage = etatCalcul.affichage.slice(0, -1);
    } else {
      etatCalcul.affichage = "0";
    }
    rafraichir();
  }

  function plusMinus() {
    if (etatCalcul.affichage !== "0" && etatCalcul.affichage !== "Erreur") {
      if (etatCalcul.affichage.charAt(0) === "-") {
        etatCalcul.affichage = etatCalcul.affichage.slice(1);
      } else {
        etatCalcul.affichage = "-" + etatCalcul.affichage;
      }
    }
    rafraichir();
  }

  // --- Fonctions scientifiques (appliquees immediatement sur l'affichage) ---
  function versRad(x) { return etatCalcul.degres ? x * Math.PI / 180 : x; }
  function depuisRad(x) { return etatCalcul.degres ? x * 180 / Math.PI : x; }

  function appliquer(fn) {
    var x = nombreAffiche();
    var r = fn(x);
    etatCalcul.affichage = formater(r);
    etatCalcul.nouveauNombre = true;
    rafraichir();
  }

  function basculerMode() {
    etatCalcul.degres = !etatCalcul.degres;
    rafraichir();
  }

  // --- Construction de l'interface ---
  // Ligne 1 : fonctions scientifiques
  // Ligne 2 : fonctions scientifiques suite
  // Ligne 3-6 : chiffres + operateurs (comme avant, elargi)
  // Ligne 7 : C, ←, =
  var LIGNES = [
    // Fonctions scientifiques
    [
      { t: "sin",  c: "sci", fn: function () { appliquer(function (x) { return Math.sin(versRad(x)); }); } },
      { t: "cos",  c: "sci", fn: function () { appliquer(function (x) { return Math.cos(versRad(x)); }); } },
      { t: "tan",  c: "sci", fn: function () { appliquer(function (x) { return Math.tan(versRad(x)); }); } },
      { t: "π",    c: "sci", fn: function () { etatCalcul.affichage = formater(Math.PI); etatCalcul.nouveauNombre = true; rafraichir(); } },
    ],
    [
      { t: "√",    c: "sci", fn: function () { appliquer(Math.sqrt); } },
      { t: "x²",   c: "sci", fn: function () { appliquer(function (x) { return x * x; }); } },
      { t: "xⁿ",   c: "operateur", fn: function () { saisirOperateur("^"); } },
      { t: "e",    c: "sci", fn: function () { etatCalcul.affichage = formater(Math.E); etatCalcul.nouveauNombre = true; rafraichir(); } },
    ],
    [
      { t: "log",  c: "sci", fn: function () { appliquer(Math.log10); } },
      { t: "ln",   c: "sci", fn: function () { appliquer(Math.log); } },
      { t: "n!",   c: "sci", fn: function () { appliquer(function (x) { if (x < 0 || x !== Math.floor(x) || x > 170) return NaN; var r = 1; for (var i = 2; i <= x; i++) r *= i; return r; }); } },
      { t: "%",    c: "sci", fn: function () { appliquer(function (x) { return x / 100; }); } },
    ],
    // Chiffres + operateurs
    [
      { t: "7", c: "num" }, { t: "8", c: "num" }, { t: "9", c: "num" }, { t: "÷", c: "operateur" },
    ],
    [
      { t: "4", c: "num" }, { t: "5", c: "num" }, { t: "6", c: "num" }, { t: "×", c: "operateur" },
    ],
    [
      { t: "1", c: "num" }, { t: "2", c: "num" }, { t: "3", c: "num" }, { t: "-", c: "operateur" },
    ],
    [
      { t: "0", c: "num" }, { t: ",", c: "num" }, { t: "±", c: "num" }, { t: "+", c: "operateur" },
    ],
    [
      { t: "C", c: "efface" }, { t: "←", c: "efface" }, { t: "DEG", c: "mode" }, { t: "=", c: "egal" },
    ],
  ];

  function gererClic(touche) {
    if (touche.fn) { touche.fn(); return; }
    var t = touche.t;
    if (t === "C") effacer();
    else if (t === "=") egal();
    else if (t === ",") saisirVirgule();
    else if (t === "±") plusMinus();
    else if (t === "←") retour();
    else if (t === "DEG") basculerMode();
    else if (["+", "-", "×", "÷"].indexOf(t) !== -1) saisirOperateur(t);
    else saisirChiffre(t);
  }

  function construire() {
    // Indicateur de mode
    indicateurMode = document.createElement("div");
    indicateurMode.id = "mode-indicateur";
    app.appendChild(indicateurMode);

    // Ecran
    ecran = document.createElement("div");
    ecran.id = "ecran";
    ecran.setAttribute("aria-live", "polite");
    app.appendChild(ecran);

    // Pave
    var pave = document.createElement("div");
    pave.id = "pave";
    LIGNES.forEach(function (ligne) {
      ligne.forEach(function (touche) {
        var bouton = document.createElement("button");
        bouton.type = "button";
        bouton.textContent = touche.t;
        if (touche.c) bouton.className = touche.c;
        bouton.addEventListener("click", function () { gererClic(touche); });
        pave.appendChild(bouton);
      });
    });
    app.appendChild(pave);
    rafraichir();
  }

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
    "fond": choix("fond", "--adapt-fond", { creme: "#FBF5E6", "bleu-pale": "#EEF4FB" }),
    // Libelle PAP : « colonne des unites en rouge, des dizaines en bleu et des centaines en vert ».
    "reperes-rang-chiffres": function (valeur) {
      if (valeur !== true) return;
      reperesRang = true;
      corps.setAttribute("data-adapt-reperes-rang-chiffres", "1");
      rafraichir();
    }
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
    if (message.action === "afficher") effacer();
  }

  window.addEventListener("message", recu);
  // Echap dans l'outil (le focus y est des qu'on a touche une touche) : la page hote ne voit pas ce clavier
  // (origine opaque), l'outil lui demande donc la fermeture par l'evenement reserve « fermer »
  // (docs/OUTILS-CONTRAT.md, §2). Aucune autre touche n'est relayee.
  document.addEventListener("keydown", function (ev) {
    if (ev.key === "Escape") envoyer("fermer", {});
  });
  construire();
  poigneeDeMain();
})();
