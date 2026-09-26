// Jules - bulles de rappel au survol. Deux sortes de rappels, montres dans une petite bulle au survol
// de la souris, au toucher (tablette) ou au clavier (Tab) :
//   - les SYMBOLES peu evidents (<, ≤, ≈, √, π, Ω, °C...) : liste NOMS ci-dessous, valable partout ;
//   - les LETTRES d'une formule (v, d, t, Ec, ρ...) : leur sens depend de la notion, il vient de la
//     fiche visuelle de la notion (champ `variables` et legendes de ses formules, voir
//     bibliotheque/SCHEMA-FICHE-VISUELLE.md). Une lettre n'est annotee que dans une formule (a cote
//     de =, ×, ÷, +, −, /, <, >...) ou dans un element [data-formule] : jamais le « a » du verbe avoir.
// Module commun a toutes les pages : il observe la page et annote tout texte affiche, y compris ajoute
// plus tard (fiches, bulles et reponses de Jules, exercices). API :
//   - Symboles.notion(element, notionId) : rappelle les lettres de cette notion dans element (null : aucune) ;
//   - Symboles.variables(element, {v: "la vitesse, en m/s"}) : idem, avec un dictionnaire deja connu ;
//   - Symboles.annoter(element) : annoter a la demande ; attribut data-sans-symboles : zone exclue.
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
    "→": "flèche : « donne », « devient »",
    "⇒": "donc (implique)",
    "⇔": "équivaut à",
    "↔": "dans les deux sens : l'un est l'inverse de l'autre",
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
  const OPERATEURS = "=×÷/+−-*<>≤≥≈≠()²³^·½¼¾";
  const LETTRE = /[\p{L}\p{N}₀-₉'’_]/u;
  const echapper = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const motifDe = (cles) => new RegExp(cles.sort((a, b) => b.length - a.length).map(echapper).join("|"), "gu");
  const motifSymboles = motifDe(Object.keys(NOMS));
  const contextes = new WeakMap(); // element -> { variables, motif }

  function exclu(el) {
    for (let e = el; e && e.nodeType === 1; e = e.parentNode) {
      if (EXCLUS.has(e.tagName) || e.namespaceURI === SVG || e.isContentEditable) return true;
      if (e.classList.contains("symbole") || e.hasAttribute("data-sans-symboles")) return true;
    }
    return false;
  }

  function contexteDe(el) {
    for (let e = el; e && e.nodeType === 1; e = e.parentNode) if (contextes.has(e)) return contextes.get(e);
    return null;
  }

  const dansFormule = (el) => Boolean(el.closest && el.closest(".formule-expression, [data-formule]"));

  // Une lettre de formule : isolee (pas au milieu d'un mot, pas « d' ») et voisine d'un operateur.
  function lettreDeFormule(texte, debut, fin, formule) {
    if (debut > 0 && LETTRE.test(texte[debut - 1])) return false;
    if (fin < texte.length && LETTRE.test(texte[fin])) return false;
    if (formule) return true;
    let i = debut - 1;
    while (i >= 0 && texte[i] === " ") i--;
    let j = fin;
    while (j < texte.length && texte[j] === " ") j++;
    return (i >= 0 && OPERATEURS.includes(texte[i])) || (j < texte.length && OPERATEURS.includes(texte[j]));
  }

  function bulle(texte, nom, classe) {
    const abbr = document.createElement("abbr");
    abbr.className = classe;
    abbr.textContent = texte;
    abbr.dataset.nom = nom;
    abbr.setAttribute("aria-label", nom);
    abbr.tabIndex = 0;
    return abbr;
  }

  function annoterTexte(noeud) {
    const parent = noeud.parentNode;
    if (!parent) return;
    const texte = noeud.nodeValue;
    const ctx = contexteDe(parent);
    const trouves = [];
    motifSymboles.lastIndex = 0;
    for (let m = motifSymboles.exec(texte); m; m = motifSymboles.exec(texte)) {
      trouves.push({ debut: m.index, fin: m.index + m[0].length, el: () => bulle(m[0], NOMS[m[0]], "symbole") });
    }
    if (ctx) {
      const formule = dansFormule(parent);
      ctx.motif.lastIndex = 0;
      for (let m = ctx.motif.exec(texte); m; m = ctx.motif.exec(texte)) {
        const debut = m.index, fin = debut + m[0].length, lettre = m[0];
        if (trouves.some((t) => t.debut < fin && debut < t.fin)) continue;
        if (!lettreDeFormule(texte, debut, fin, formule)) continue;
        trouves.push({ debut, fin, el: () => bulle(lettre, `${lettre} : ${ctx.variables[lettre]}`, "symbole variable") });
      }
    }
    if (!trouves.length) return;
    trouves.sort((a, b) => a.debut - b.debut);
    const morceaux = document.createDocumentFragment();
    let pos = 0;
    for (const t of trouves) {
      if (t.debut > pos) morceaux.appendChild(document.createTextNode(texte.slice(pos, t.debut)));
      morceaux.appendChild(t.el());
      pos = t.fin;
    }
    if (pos < texte.length) morceaux.appendChild(document.createTextNode(texte.slice(pos)));
    parent.replaceChild(morceaux, noeud);
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

  // Rappel des lettres d'une notion dans une zone : les anciens rappels de lettres sont retires, puis
  // la zone est relue avec le nouveau dictionnaire (vide : plus aucune lettre rappelee).
  function variables(racine, dictionnaire) {
    if (!racine) return;
    for (const a of racine.querySelectorAll("abbr.variable")) a.replaceWith(document.createTextNode(a.textContent));
    racine.normalize();
    const cles = Object.keys(dictionnaire || {}).filter((k) => k && dictionnaire[k]);
    if (cles.length) contextes.set(racine, { variables: dictionnaire, motif: motifDe(cles) });
    else contextes.delete(racine);
    annoter(racine);
  }

  let demandeNotion = 0;
  async function notion(racine, notionId) {
    const demande = ++demandeNotion;
    let dictionnaire = {};
    if (notionId) {
      try {
        const r = await fetch(`/api/eleve/fiches_visuelles/notions/${encodeURIComponent(notionId)}/variables`, { credentials: "same-origin" });
        if (r.ok) dictionnaire = (await r.json()).variables || {};
      } catch (_) { /* sans fiche visuelle, rien a rappeler */ }
    }
    if (demande === demandeNotion) variables(racine, dictionnaire);
  }

  // Une seule bulle pour toute la page, placee au-dessus du symbole (en dessous s'il n'y a pas la
  // place) et toujours gardee dans l'ecran, meme pour un symbole colle au bord.
  let bulleAffichee = null, abbrCourant = null;
  function montrer(abbr) {
    abbrCourant = abbr;
    if (!bulleAffichee) {
      bulleAffichee = document.createElement("div");
      bulleAffichee.className = "symboles-bulle";
      bulleAffichee.setAttribute("role", "tooltip");
      bulleAffichee.setAttribute("data-sans-symboles", "");
      document.body.appendChild(bulleAffichee);
    }
    bulleAffichee.textContent = abbr.dataset.nom;
    bulleAffichee.classList.add("visible");
    const r = abbr.getBoundingClientRect(), b = bulleAffichee.getBoundingClientRect(), marge = 8;
    const gauche = Math.min(Math.max(marge, r.left + r.width / 2 - b.width / 2), innerWidth - b.width - marge);
    const dessus = r.top - b.height - 10 >= marge;
    bulleAffichee.style.left = `${gauche + scrollX}px`;
    bulleAffichee.style.top = `${(dessus ? r.top - b.height - 10 : r.bottom + 10) + scrollY}px`;
  }
  function cacher() {
    abbrCourant = null;
    if (bulleAffichee) bulleAffichee.classList.remove("visible");
  }
  // La page defile : la bulle suit son symbole (ou disparait s'il n'est plus affiche).
  function suivre() {
    if (!abbrCourant) return;
    if (abbrCourant.isConnected) montrer(abbrCourant);
    else cacher();
  }
  const cible = (e) => (e.target.closest ? e.target.closest("abbr.symbole") : null);

  function demarrer() {
    document.addEventListener("mouseover", (e) => { const a = cible(e); if (a) montrer(a); });
    document.addEventListener("mouseout", (e) => { if (cible(e)) cacher(); });
    document.addEventListener("focusin", (e) => { const a = cible(e); if (a) montrer(a); else cacher(); });
    document.addEventListener("focusout", (e) => { if (cible(e)) cacher(); });
    addEventListener("scroll", suivre, true);
    addEventListener("resize", suivre);
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
  return { NOMS, annoter, variables, notion };
})();
