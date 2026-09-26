// Jules - bulles de rappel au survol, sur toutes les pages : tout ce qui est abrege ou symbolique
// dans un texte affiche a l'eleve montre ce qu'il veut dire dans une petite bulle (souris, toucher,
// clavier). Ce fichier est le COEUR : il parcourt la page, affiche les bulles, tient le contexte de
// la notion (matiere, lettres des formules, abreviations de sa fiche visuelle) et ne connait que les
// symboles communs a tout le programme (≤, ≈, →...). Les regles d'une matiere (unites et chimie en
// sciences, siecles en histoire, grammaire en francais...) viennent des EXTENSIONS de la famille
// `rappels` (docs/EXTENSIONS.md), servies par /rappels.js apres ce fichier. Une extension enregistre :
//   Symboles.dictionnaire({id, matieres, entrees: {URSS: "Union des républiques..."}})  // donnees seules
//   Symboles.enregistrer({
//     id: "unites", matieres: ["physique-chimie", ...] (absent : toutes), rang: 3 (petit = prioritaire),
//     trouver(texte, ctx, outils) -> [{debut, fin, sens, classe?}]   // une bulle par passage reconnu
//     // ou bien, pour une mise en forme (formules en gras) :
//     mettreEnForme(texte, ctx, outils) -> [{debut, fin, classe}], formule: true|false
//   });
// `ctx` : {matiere, variables, abreviations, formule (dans une formule ?), zone (l'element formule)}.
// `outils` : aides partagees (avant, apres, isole, motAvant, motDevantParenthese, designe, motifDe...).
// Quand la matiere est inconnue (discussion libre), toutes les regles s'appliquent.
// API des pages : Symboles.notion(element, notionId) ; Symboles.contexte(element, {matiere,
// variables, abreviations}) ; Symboles.annoter(element) ; attribut data-sans-symboles : zone exclue.
// Jamais d'innerHTML : le texte est decoupe en noeuds texte et en elements crees un par un.
"use strict";

const Symboles = (() => {
  // Symboles communs a toutes les matieres. Les operations evidentes (+, ×, ÷, =) n'en ont pas.
  const SYMBOLES = {
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
    "ρ": "rhô (lettre grecque) : souvent une masse volumique",
  };
  const SVG = "http://www.w3.org/2000/svg";
  const EXCLUS = new Set(["SCRIPT", "STYLE", "TEXTAREA", "INPUT", "SELECT", "OPTION", "CODE", "PRE", "KBD", "SAMP", "TITLE", "NOSCRIPT"]);
  const ZONE_FORMULE = ".formule-expression, .rappel-formule, [data-formule]";
  const ZONE_FORME = ".formule-expression, .rappel-forme, [data-formule]";
  const OPERATEURS = "=×÷+−*<>≤≥≈≠()²³^·½¼¾→"; // pas « / » : il appartient aux unites (m/s)
  const COLLE = /[\p{L}\p{N}₀-₉'’_]/u; // un caractere qui colle a un mot
  const LETTRES_MOTS = new Set(["a", "y", "A", "Y", "à", "À", "ô"]); // « il a », « il y a » : formule seulement

  // --- outils partages avec les extensions -------------------------------------------------------
  const echapper = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const alternatives = (cles) => cles.slice().sort((a, b) => b.length - a.length).map(echapper).join("|");
  const motifDe = (cles) => new RegExp(alternatives(cles), "gu");
  const sansAccent = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  const avant = (texte, i) => { while (i >= 0 && texte[i] === " ") i--; return i >= 0 ? texte[i] : ""; };
  const apres = (texte, j) => { while (j < texte.length && texte[j] === " ") j++; return j < texte.length ? texte[j] : ""; };
  const isole = (texte, debut, fin) => !(debut > 0 && COLLE.test(texte[debut - 1])) && !(fin < texte.length && COLLE.test(texte[fin]));
  const motAvant = (texte, i) => texte.slice(0, i).trimEnd().split(/\s+/).pop() || "";
  // « watts (W) » : le mot devant une lettre entre parentheses dit ce qu'elle est.
  function motDevantParenthese(texte, debut, fin) {
    if (texte[debut - 1] !== "(" || texte[fin] !== ")") return "";
    return sansAccent(texte.slice(0, debut - 1).trimEnd().split(/\s+/).pop() || "");
  }
  const designe = (mot, sens) => Boolean(mot) && sansAccent(sens).split(/[\s(,]/)[0].replace(/s$/, "") === mot.replace(/s$/, "");
  function parcourir(motif, texte, faire) {
    motif.lastIndex = 0;
    for (let m = motif.exec(texte); m; m = motif.exec(texte)) faire(m[0], m.index, m);
  }
  const outils = { echapper, alternatives, motifDe, sansAccent, avant, apres, isole, motAvant, motDevantParenthese, designe, parcourir, OPERATEURS, COLLE };

  // --- les regles : celles du coeur, puis celles des extensions -----------------------------------
  const reconnaisseurs = [];
  const formes = [];
  let demarre = false;

  function enregistrer(regle) {
    if (!regle || typeof regle.id !== "string" || (typeof regle.trouver !== "function" && typeof regle.mettreEnForme !== "function")) {
      console.warn("Symboles : regle ignoree (id et trouver() ou mettreEnForme() attendus)", regle);
      return;
    }
    const r = { rang: 5, matieres: null, ...regle };
    (r.mettreEnForme ? formes : reconnaisseurs).push(r);
    if (demarre) annoter(document.body);
  }
  // Raccourci pour une extension faite de donnees seules : { abreviation: sens }, reconnue comme mot
  // entier (« l'ONU » compte : l'apostrophe devant est admise), sensible a la casse.
  function dictionnaire({ id, matieres = null, rang = 4, classe = "abreviation", entrees = {} }) {
    const cles = Object.keys(entrees).filter((k) => k && entrees[k]);
    if (!cles.length) return;
    const motif = motifDe(cles);
    enregistrer({
      id, matieres, rang,
      trouver(texte) {
        const trouves = [];
        parcourir(motif, texte, (mot, i) => {
          const fin = i + mot.length;
          if (i > 0 && /[\p{L}\p{N}_]/u.test(texte[i - 1])) return;
          if (fin < texte.length && /[\p{L}\p{N}_]/u.test(texte[fin])) return;
          trouves.push({ debut: i, fin, sens: `${mot} : ${entrees[mot]}`, classe });
        });
        return trouves;
      },
    });
  }
  const actives = (regles, matiere) => regles.filter((r) => !matiere || !r.matieres || r.matieres.includes(matiere));

  // Lettres des formules de la notion : dans une formule, ou dans une phrase si ce n'est pas un mot.
  enregistrer({
    id: "notion-lettres", rang: 0,
    trouver(texte, ctx) {
      if (!ctx.motifVariables) return [];
      const trouves = [];
      parcourir(ctx.motifVariables, texte, (mot, i) => {
        if (!isole(texte, i, i + mot.length)) return;
        if (/\d/.test(avant(texte, i - 1))) return; // « 5 m/s », « 10 m » : une unite
        if (mot.length === 1 && ["en", "des", "par"].includes(motAvant(texte, i))) return; // « en m »
        const voisin = OPERATEURS.includes(avant(texte, i - 1)) || OPERATEURS.includes(apres(texte, i + mot.length));
        if (ctx.formule || voisin || !LETTRES_MOTS.has(mot)) {
          trouves.push({ debut: i, fin: i + mot.length, sens: `${mot} : ${ctx.variables[mot]}`, classe: "variable" });
        }
      });
      return trouves;
    },
  });
  // Abreviations propres a la notion (champ `abreviations` de sa fiche visuelle).
  enregistrer({
    id: "notion-abreviations", rang: 1,
    trouver(texte, ctx) {
      if (!ctx.motifAbreviations) return [];
      const trouves = [];
      parcourir(ctx.motifAbreviations, texte, (mot, i) => {
        if (isole(texte, i, i + mot.length)) trouves.push({ debut: i, fin: i + mot.length, sens: `${mot} : ${ctx.abreviations[mot]}`, classe: "abreviation" });
      });
      return trouves;
    },
  });
  const motifSymboles = motifDe(Object.keys(SYMBOLES));
  enregistrer({
    id: "symboles", rang: 5,
    trouver(texte) {
      const trouves = [];
      parcourir(motifSymboles, texte, (mot, i) => {
        if (mot === "°" && !/\d/.test(avant(texte, i - 1))) return; // « n° 31 » n'est pas un degre
        trouves.push({ debut: i, fin: i + mot.length, sens: `${mot} : ${SYMBOLES[mot]}` });
      });
      return trouves;
    },
  });

  // --- contexte d'une zone de la page ---------------------------------------------------------------
  const contextes = new WeakMap(); // element -> { matiere, variables, abreviations, motifVariables, motifAbreviations }

  function exclu(el) {
    for (let e = el; e && e.nodeType === 1; e = e.parentNode) {
      if (EXCLUS.has(e.tagName) || e.namespaceURI === SVG || e.isContentEditable) return true;
      if (e.classList.contains("symbole") || e.hasAttribute("data-sans-symboles")) return true;
    }
    return false;
  }

  function contexteDe(parent) {
    let base = {};
    for (let e = parent; e && e.nodeType === 1; e = e.parentNode) if (contextes.has(e)) { base = contextes.get(e); break; }
    const zone = parent.closest ? parent.closest(ZONE_FORMULE) : null;
    return { ...base, formule: Boolean(zone), zone };
  }

  function appliquer(regles, fonction, texte, ctx, rangDefaut) {
    const resultats = [];
    for (const r of actives(regles, ctx.matiere)) {
      let trouves = [];
      try {
        trouves = r[fonction](texte, ctx, outils) || [];
      } catch (err) {
        console.warn(`Symboles : la regle ${r.id} a echoue`, err);
      }
      for (const t of trouves) {
        if (Number.isInteger(t.debut) && Number.isInteger(t.fin) && t.debut >= 0 && t.fin <= texte.length && t.fin > t.debut) {
          resultats.push({ ...t, rang: r.rang ?? rangDefaut, formule: Boolean(r.formule) });
        }
      }
    }
    // Au meme endroit, la lecture la plus longue l'emporte (« m/s » plutot que « m »), puis le rang.
    resultats.sort((a, b) => a.debut - b.debut || b.fin - a.fin || a.rang - b.rang);
    const retenus = [];
    for (const t of resultats) {
      const dernier = retenus[retenus.length - 1];
      if (!dernier || t.debut >= dernier.fin) retenus.push(t);
    }
    return retenus;
  }

  function bulle(texte, t) {
    const abbr = document.createElement("abbr");
    abbr.className = `symbole ${t.classe || ""}`.trim();
    abbr.textContent = texte.slice(t.debut, t.fin);
    abbr.dataset.nom = t.sens;
    abbr.setAttribute("aria-label", t.sens);
    abbr.tabIndex = 0;
    return abbr;
  }

  function decouper(noeud, texte, retenus, fabriquer) {
    const morceaux = [];
    let pos = 0;
    for (const t of retenus) {
      if (t.debut > pos) morceaux.push(document.createTextNode(texte.slice(pos, t.debut)));
      morceaux.push(fabriquer(t));
      pos = t.fin;
    }
    if (pos < texte.length) morceaux.push(document.createTextNode(texte.slice(pos)));
    const fragment = document.createDocumentFragment();
    morceaux.forEach((m) => fragment.appendChild(m));
    noeud.parentNode.replaceChild(fragment, noeud);
    return morceaux;
  }

  function annoterTexte(noeud) {
    const parent = noeud.parentNode;
    if (!parent) return;
    const texte = noeud.nodeValue;
    const ctx = contexteDe(parent);
    // 1. Mises en forme (formules du texte en gras...) ; leur contenu est annote ensuite.
    if (!(parent.closest && parent.closest(ZONE_FORME))) {
      const zones = appliquer(formes, "mettreEnForme", texte, ctx, 5);
      if (zones.length) {
        const morceaux = decouper(noeud, texte, zones, (t) => {
          const span = document.createElement("span");
          span.className = `rappel-forme ${t.formule ? "rappel-formule " : ""}${t.classe || ""}`.trim();
          span.textContent = texte.slice(t.debut, t.fin);
          return span;
        });
        morceaux.forEach((m) => annoter(m));
        return;
      }
    }
    // 2. Les bulles.
    const retenus = appliquer(reconnaisseurs, "trouver", texte, ctx, 5);
    if (retenus.length) decouper(noeud, texte, retenus, (t) => bulle(texte, t));
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

  // Contexte d'une zone (la fiche, la discussion...) : matiere et rappels propres a la notion. Tout
  // est relu : un rappel propre a la notion prime sur un rappel commun (« ua » de la fiche).
  function contexte(racine, { matiere = null, variables = {}, abreviations = {} } = {}) {
    if (!racine) return;
    for (const a of racine.querySelectorAll("abbr.symbole")) a.replaceWith(document.createTextNode(a.textContent));
    for (const s of racine.querySelectorAll(".rappel-forme")) s.replaceWith(document.createTextNode(s.textContent));
    racine.normalize();
    const cles = (d) => Object.keys(d || {}).filter((k) => k && d[k]);
    const cv = cles(variables), ca = cles(abreviations);
    contextes.set(racine, {
      matiere, variables, abreviations,
      motifVariables: cv.length ? motifDe(cv) : null,
      motifAbreviations: ca.length ? motifDe(ca) : null,
    });
    annoter(racine);
  }

  let demandeNotion = 0;
  async function notion(racine, notionId) {
    const demande = ++demandeNotion;
    let rappels = {};
    if (notionId) {
      try {
        const r = await fetch(`/api/eleve/fiches_visuelles/notions/${encodeURIComponent(notionId)}/rappels`, { credentials: "same-origin" });
        if (r.ok) rappels = await r.json();
      } catch (_) { /* sans fiche visuelle, rien de propre a la notion */ }
    }
    if (demande === demandeNotion) contexte(racine, rappels);
  }

  // --- la bulle : une seule pour la page, placee par le script, toujours dans l'ecran --------------
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
  function suivre() {
    if (!abbrCourant) return;
    if (abbrCourant.isConnected) montrer(abbrCourant);
    else cacher();
  }
  const cible = (e) => (e.target.closest ? e.target.closest("abbr.symbole") : null);

  // Demarrage une fois toute la page lue : les extensions (/rappels.js) sont alors enregistrees.
  function demarrer() {
    if (demarre) return;
    demarre = true;
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
  if (document.readyState === "loading") addEventListener("DOMContentLoaded", demarrer);
  else setTimeout(demarrer, 0);

  const variables = (racine, dictionnaire) => contexte(racine, { variables: dictionnaire });
  return { enregistrer, dictionnaire, annoter, contexte, variables, notion, outils };
})();
