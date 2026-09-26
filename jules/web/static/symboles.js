// Jules - nom des symboles. Un symbole (<, ≤, ×, √, π, Ω, °C...) montre son nom dans une petite
// bulle au survol de la souris, au toucher (tablette) ou au clavier (Tab). Module commun a toutes
// les pages : il observe la page et annote tout texte affiche, y compris ajoute plus tard (fiches,
// bulles et reponses de Jules, exercices). Aucune donnee ne sort de la page.
//   - completer la liste : ajouter une entree dans NOMS (le symbole le plus long gagne : « °C » avant « ° ») ;
//   - exclure une zone : attribut data-sans-symboles sur l'element ;
//   - annoter a la demande (contenu hors de la page, par exemple) : Symboles.annoter(element).
// Jamais d'innerHTML : le texte est decoupe en noeuds texte et en <abbr> crees un par un.
"use strict";

const Symboles = (() => {
  const NOMS = {
    "<": "inférieur à (plus petit que)",
    ">": "supérieur à (plus grand que)",
    "≤": "inférieur ou égal à",
    "⩽": "inférieur ou égal à",
    "≥": "supérieur ou égal à",
    "⩾": "supérieur ou égal à",
    "≠": "différent de",
    "≈": "environ égal à (valeur approchée)",
    "×": "multiplié par (fois)",
    "÷": "divisé par",
    "±": "plus ou moins",
    "√": "racine carrée",
    "∝": "proportionnel à",
    "∞": "infini",
    "π": "pi : environ 3,14",
    "°C": "degré Celsius",
    "°": "degré",
    "‰": "pour mille",
    "²": "au carré (exposant 2)",
    "³": "au cube (exposant 3)",
    "½": "un demi",
    "¼": "un quart",
    "¾": "trois quarts",
    "→": "flèche : « donne », « devient »",
    "⇒": "donc (implique)",
    "⇔": "équivaut à",
    "∥": "est parallèle à",
    "⊥": "est perpendiculaire à",
    "∠": "angle",
    "∈": "appartient à",
    "∉": "n'appartient pas à",
    "∅": "ensemble vide",
    "∩": "inter (les deux à la fois)",
    "∪": "union (l'un ou l'autre)",
    "∑": "somme",
    "Δ": "delta : une variation, une différence",
    "α": "alpha (lettre grecque)",
    "β": "bêta (lettre grecque)",
    "γ": "gamma (lettre grecque)",
    "θ": "thêta (lettre grecque) : souvent un angle",
    "λ": "lambda (lettre grecque) : souvent une longueur d'onde",
    "µ": "micro : un millionième",
    "μ": "micro : un millionième",
    "ρ": "rhô (lettre grecque) : souvent une masse volumique",
    "Ω": "ohm, unité de résistance (lettre grecque oméga)",
  };
  const SVG = "http://www.w3.org/2000/svg";
  const EXCLUS = new Set(["SCRIPT", "STYLE", "TEXTAREA", "INPUT", "SELECT", "OPTION", "CODE", "PRE", "KBD", "SAMP", "TITLE", "NOSCRIPT"]);
  const echapper = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const motif = new RegExp(
    Object.keys(NOMS).sort((a, b) => b.length - a.length).map(echapper).join("|"),
    "g",
  );

  function exclu(el) {
    for (let e = el; e && e.nodeType === 1; e = e.parentNode) {
      if (EXCLUS.has(e.tagName) || e.namespaceURI === SVG || e.isContentEditable) return true;
      if (e.classList.contains("symbole") || e.hasAttribute("data-sans-symboles")) return true;
    }
    return false;
  }

  function annoterTexte(noeud) {
    const texte = noeud.nodeValue;
    motif.lastIndex = 0;
    if (!noeud.parentNode || !motif.test(texte)) return;
    motif.lastIndex = 0;
    const morceaux = document.createDocumentFragment();
    let pos = 0;
    for (let m = motif.exec(texte); m; m = motif.exec(texte)) {
      if (m.index > pos) morceaux.appendChild(document.createTextNode(texte.slice(pos, m.index)));
      const abbr = document.createElement("abbr");
      abbr.className = "symbole";
      abbr.textContent = m[0];
      abbr.dataset.nom = NOMS[m[0]];
      abbr.setAttribute("aria-label", NOMS[m[0]]);
      abbr.tabIndex = 0;
      morceaux.appendChild(abbr);
      pos = m.index + m[0].length;
    }
    if (pos < texte.length) morceaux.appendChild(document.createTextNode(texte.slice(pos)));
    noeud.parentNode.replaceChild(morceaux, noeud);
  }

  function annoter(racine) {
    if (!racine) return;
    if (racine.nodeType === 3) {
      if (!exclu(racine.parentNode)) annoterTexte(racine);
      return;
    }
    if (racine.nodeType !== 1 || exclu(racine)) return;
    const marcheur = document.createTreeWalker(racine, NodeFilter.SHOW_TEXT, {
      acceptNode: (n) => (exclu(n.parentNode) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT),
    });
    const noeuds = [];
    while (marcheur.nextNode()) noeuds.push(marcheur.currentNode);
    noeuds.forEach(annoterTexte);
  }

  function demarrer() {
    annoter(document.body);
    new MutationObserver((changements) => {
      for (const c of changements) {
        if (c.type === "characterData") annoter(c.target);
        else c.addedNodes.forEach(annoter);
      }
    }).observe(document.body, { childList: true, subtree: true, characterData: true });
  }

  if (document.body) demarrer();
  else addEventListener("DOMContentLoaded", demarrer);
  return { NOMS, annoter };
})();
