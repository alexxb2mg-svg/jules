// Jules - bulles de rappel au survol, sur toutes les pages. Tout ce qui est abrege ou symbolique dans
// un texte affiche a l'eleve montre ce qu'il veut dire dans une petite bulle (souris, toucher, clavier) :
//   - les formules ecrites dans le texte (« P = m × g ») ressortent en gras ;
//   - les LETTRES d'une formule (v, d, t, Ec...) : sens donne par la fiche visuelle de la notion
//     (champ `variables`), reconnues seulement dans une formule, jamais le « a » du verbe avoir ;
//   - les ESPECES CHIMIQUES (CO₂, H₂O, Cu²⁺, NaCl...) : nom et composition ;
//   - les ELEMENTS (Fe, Na, O...) ; les UNITES (s, kg, N, km/h...) ; les SYMBOLES (≈, ≤, √, →...) ;
//   - les ABREVIATIONS propres a une notion (champ `abreviations` de sa fiche : ua, URSS...).
// Les dictionnaires communs sont dans rappels.js (des donnees : une ligne ajoutee = une bulle de plus
// partout). Le module observe la page et annote aussi le texte ajoute plus tard (fiches, bulles et
// reponses de Jules, exercices). API :
//   - Symboles.notion(element, notionId) : rappels propres a cette notion dans element (null : aucun) ;
//   - Symboles.contexte(element, {variables, abreviations}) : idem, avec des dictionnaires deja connus ;
//   - Symboles.annoter(element) : annoter a la demande ; attribut data-sans-symboles : zone exclue.
// Jamais d'innerHTML : le texte est decoupe en noeuds texte et en elements crees un par un.
"use strict";

const Symboles = (() => {
  const D = typeof RAPPELS !== "undefined" ? RAPPELS : { symboles: {}, unites: {}, elements: {}, especes: {}, elementsAmbigus: [] };
  const SVG = "http://www.w3.org/2000/svg";
  const EXCLUS = new Set(["SCRIPT", "STYLE", "TEXTAREA", "INPUT", "SELECT", "OPTION", "CODE", "PRE", "KBD", "SAMP", "TITLE", "NOSCRIPT"]);
  const ZONE_FORMULE = ".formule-expression, .formule-texte, [data-formule]";
  const OPERATEURS = "=×÷+−*<>≤≥≈≠()²³^·½¼¾→"; // pas « / » : il appartient aux unites (m/s)
  const COLLE = /[\p{L}\p{N}₀-₉'’_]/u; // un caractere qui colle a un mot
  const AMBIGUS = new Set(D.elementsAmbigus || []);
  const LETTRES_MOTS = new Set(["a", "y", "A", "Y", "à", "À", "ô"]); // « il a », « il y a » : dans une formule seulement
  const INDICES = "₀₁₂₃₄₅₆₇₈₉", EXPOSANTS = "⁰¹²³⁴⁵⁶⁷⁸⁹";
  const echapper = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const alternatives = (cles) => cles.slice().sort((a, b) => b.length - a.length).map(echapper).join("|");
  const motifDe = (cles) => new RegExp(alternatives(cles), "gu");

  const motifSymboles = motifDe(Object.keys(D.symboles));
  const motifUnites = motifDe(Object.keys(D.unites));
  const motifChimie = /\(?(?:[A-Z][a-z]?[₀-₉]*|\((?:[A-Z][a-z]?[₀-₉]*)+\)[₀-₉]*)+[⁰¹²³⁴⁵⁶⁷⁸⁹]*[⁺⁻]?/gu;

  // Une formule ecrite dans le texte : des termes courts relies par des operateurs, avec au moins
  // un « = », « → » ou « ≈ ». Termes : nombre (avec son unite), lettre(s) de grandeur, espece chimique.
  const NOMBRE = String.raw`\d+(?:[  ]\d{3})*(?:,\d+)?(?:[  ]?(?:${alternatives(Object.keys(D.unites))})(?![\p{L}\p{N}]))?`;
  const UNITE_SEULE = String.raw`(?:${alternatives(Object.keys(D.unites).filter((u) => u.length > 1))})(?![\p{L}\p{N}])`;
  const TERME = String.raw`(?:${NOMBRE}|${UNITE_SEULE}|(?:\d+[  ])?(?:[A-Z][a-z]?[₀-₉]*)+[⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻]*(?![\p{L}\p{N}])|[½¼¾]|[\p{L}][\p{L}0-9₀-₉]{0,2}[²³]?(?![\p{L}\p{N}])|\([^()\n]{1,30}\))`;
  const motifFormule = new RegExp(String.raw`(?<![\p{L}\p{N}])${TERME}(?:\s*[=×÷+−→≈≤≥<>]\s*${TERME})+`, "gu");

  const contextes = new WeakMap(); // element -> { variables, abreviations, motifVariables, motifAbreviations }

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

  const dansFormule = (el) => Boolean(el.closest && el.closest(ZONE_FORMULE));
  const avant = (texte, i) => { while (i >= 0 && texte[i] === " ") i--; return i >= 0 ? texte[i] : ""; };
  const apres = (texte, j) => { while (j < texte.length && texte[j] === " ") j++; return j < texte.length ? texte[j] : ""; };
  // « watts (W) » : le mot devant une lettre entre parentheses dit ce qu'elle est.
  const sansAccent = (s) => s.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  function motDevantParenthese(texte, debut, fin) {
    if (texte[debut - 1] !== "(" || texte[fin] !== ")") return "";
    return sansAccent(texte.slice(0, debut - 1).trimEnd().split(/\s+/).pop() || "");
  }
  const designe = (mot, sens) => mot && sansAccent(sens).split(/[\s(,]/)[0].replace(/s$/, "") === mot.replace(/s$/, "");
  const isole = (texte, debut, fin) => !(debut > 0 && COLLE.test(texte[debut - 1])) && !(fin < texte.length && COLLE.test(texte[fin]));

  // --- composition d'une espece chimique -------------------------------------------------------
  const chiffres = (s, table) => Number([...s].map((c) => table.indexOf(c)).join("")) || 1;
  const elision = (nom) => (/^[aeiouyéèêh]/i.test(nom) ? `d'${nom}` : `de ${nom}`);

  function composition(formule) {
    const corps = formule.replace(/[⁰-⁹⁺⁻¹²³]+$/u, "").replace(/[⁺⁻]$/, "");
    const compte = new Map();
    const lire = (morceau, facteur) => {
      for (const m of morceau.matchAll(/\(([^)]+)\)([₀-₉]*)|([A-Z][a-z]?)([₀-₉]*)/gu)) {
        if (m[1]) lire(m[1], facteur * (m[2] ? chiffres(m[2], INDICES) : 1));
        else compte.set(m[3], (compte.get(m[3]) || 0) + facteur * (m[4] ? chiffres(m[4], INDICES) : 1));
      }
    };
    lire(corps, 1);
    if ([...compte.keys()].some((s) => !D.elements[s])) return null;
    return [...compte].map(([s, n]) => `${n} atome${n > 1 ? "s" : ""} ${elision(D.elements[s])}`).join(", ");
  }

  function charge(formule) {
    const m = formule.match(/([⁰¹²³⁴⁵⁶⁷⁸⁹]*)([⁺⁻])$/u);
    if (!m) return "";
    const n = m[1] ? chiffres(m[1], EXPOSANTS) : 1;
    return `${n} charge${n > 1 ? "s" : ""} ${m[2] === "⁺" ? "positive" : "négative"}${n > 1 ? "s" : ""}`;
  }

  function sensChimique(formule) {
    const nom = D.especes[formule];
    const compo = composition(formule);
    if (!compo) return null;
    const parties = compo.split(", ");
    const ion = /[⁺⁻]$/.test(formule);
    // Un seul atome sans charge : c'est un element, traite a part.
    if (!nom && !ion && parties.length === 1 && parties[0].startsWith("1 ")) return null;
    const detail = [compo, ion ? charge(formule) : ""].filter(Boolean).join(" ; ");
    return nom ? `${nom} : ${detail}` : `${ion ? "ion" : "molécule"} : ${detail}`;
  }

  // --- reperage des rappels dans un texte ------------------------------------------------------
  function candidats(texte, parent) {
    const ctx = contexteDe(parent);
    const formule = dansFormule(parent);
    const trouves = [];
    const ajouter = (debut, mot, sens, classe, rang) => trouves.push({ debut, fin: debut + mot.length, mot, sens, classe, rang });
    const parcourir = (motif, faire) => {
      motif.lastIndex = 0;
      for (let m = motif.exec(texte); m; m = motif.exec(texte)) faire(m[0], m.index);
    };

    if (ctx && ctx.motifVariables) {
      parcourir(ctx.motifVariables, (mot, i) => {
        if (!isole(texte, i, i + mot.length)) return;
        if (/\d/.test(avant(texte, i - 1))) return; // « 5 m/s », « 10 m » : une unite, pas une lettre
        const motAvant = texte.slice(0, i).trimEnd().split(/\s+/).pop();
        if (D.unites[mot] && ["en", "des", "par"].includes(motAvant)) return; // « en m » : des metres
        // Dans une phrase aussi (« vérifie que m est en kg »), sauf les lettres qui sont des mots.
        const voisin = OPERATEURS.includes(avant(texte, i - 1)) || OPERATEURS.includes(apres(texte, i + mot.length));
        if (formule || voisin || !LETTRES_MOTS.has(mot)) ajouter(i, mot, `${mot} : ${ctx.variables[mot]}`, "variable", 0);
      });
    }
    if (ctx && ctx.motifAbreviations) {
      parcourir(ctx.motifAbreviations, (mot, i) => {
        if (isole(texte, i, i + mot.length)) ajouter(i, mot, `${mot} : ${ctx.abreviations[mot]}`, "abreviation", 1);
      });
    }
    parcourir(motifChimie, (mot, i) => {
      if (mot.startsWith("(") || !isole(texte, i, i + mot.length)) return;
      const multiple = /[₀-₉⁺⁻]/u.test(mot) || D.especes[mot] || (mot.match(/[A-Z]/g) || []).length > 1 && /[a-z]/.test(mot);
      if (!multiple) return;
      const sens = sensChimique(mot);
      if (sens) ajouter(i, mot, `${mot} : ${sens}`, "chimie", 2);
    });
    parcourir(motifUnites, (mot, i) => {
      const fin = i + mot.length;
      if ((i > 0 && /[\p{L}_'’]/u.test(texte[i - 1])) || (fin < texte.length && COLLE.test(texte[fin]))) return;
      const courte = mot.length === 1 || D.elements[mot]; // « m », « N », « Pa » : il faut un nombre ou « en »
      const precede = avant(texte, i - 1);
      const motAvant = texte.slice(0, i).trimEnd().split(/\s+/).pop();
      const nomme = designe(motDevantParenthese(texte, i, fin), D.unites[mot]); // « watts (W) »
      if (courte && !/\d/.test(precede) && !nomme && !["en", "des", "les", "par"].includes(motAvant)) return;
      // Dans une formule, « mg » fait de lettres de la formule (m × g) n'est pas une unite.
      if (formule && !/\d/.test(precede) && ctx && [...mot].every((c) => ctx.variables[c] || !/\p{L}/u.test(c))) return;
      ajouter(i, mot, `${mot} : ${D.unites[mot]}`, "unite", 3);
    });
    parcourir(/[A-Z][a-z]?/gu, (mot, i) => {
      const nom = D.elements[mot];
      if (!nom || !isole(texte, i, i + mot.length)) return;
      if (mot.length === 1 || AMBIGUS.has(mot)) {
        // « watts (W) » : c'est l'unite, pas le tungstene.
        if (D.unites[mot] && designe(motDevantParenthese(texte, i, i + mot.length), D.unites[mot])) return;
        // Jamais suivi d'un mot : « Au début » et « Si tu » ne sont ni de l'or ni du silicium.
        if (/\p{L}/u.test(apres(texte, i + mot.length))) return;
        const precedent = avant(texte, i - 1);
        const zone = formule && parent.closest(ZONE_FORMULE);
        const equationChimique = Boolean(zone && /[₀-₉→]/u.test(zone.textContent));
        if (mot.length === 1) {
          // Une lettre seule (O, C, N...) : dans une equation chimique, ou dans une liste hors formule.
          if (formule ? !equationChimique : !precedent || !"(,;:/+".includes(precedent)) return;
        } else if (precedent && !"(,;:/+→".includes(precedent)) {
          return;
        }
      }
      ajouter(i, mot, `${mot} : ${nom} (élément chimique)`, "chimie", 4);
    });
    parcourir(motifSymboles, (mot, i) => {
      if (mot === "°" && !/\d/.test(avant(texte, i - 1))) return; // « n° 31 » n'est pas un degre
      ajouter(i, mot, `${mot} : ${D.symboles[mot]}`, "", 5);
    });

    // Au meme endroit, la lecture la plus longue l'emporte (« m/s » plutot que « m »), puis le rang.
    trouves.sort((a, b) => a.debut - b.debut || b.fin - a.fin || a.rang - b.rang);
    const retenus = [];
    for (const t of trouves) {
      const dernier = retenus[retenus.length - 1];
      if (!dernier || t.debut >= dernier.fin) retenus.push(t);
    }
    return retenus;
  }

  function bulle(t) {
    const abbr = document.createElement("abbr");
    abbr.className = `symbole ${t.classe}`.trim();
    abbr.textContent = t.mot;
    abbr.dataset.nom = t.sens;
    abbr.setAttribute("aria-label", t.sens);
    abbr.tabIndex = 0;
    return abbr;
  }

  function remplacer(noeud, morceaux) {
    const fragment = document.createDocumentFragment();
    morceaux.forEach((m) => fragment.appendChild(m));
    noeud.parentNode.replaceChild(fragment, noeud);
  }

  function annoterTexte(noeud) {
    const parent = noeud.parentNode;
    if (!parent) return;
    const texte = noeud.nodeValue;
    // 1. Les formules ecrites dans le texte passent en gras ; leur contenu est annote ensuite.
    if (!dansFormule(parent)) {
      const morceaux = [];
      let pos = 0;
      motifFormule.lastIndex = 0;
      for (let m = motifFormule.exec(texte); m; m = motifFormule.exec(texte)) {
        if (!/[=→≈≤≥<>]/.test(m[0])) continue;
        if (m.index > pos) morceaux.push(document.createTextNode(texte.slice(pos, m.index)));
        const span = document.createElement("span");
        span.className = "formule-texte";
        span.textContent = m[0];
        morceaux.push(span);
        pos = m.index + m[0].length;
      }
      if (morceaux.length) {
        if (pos < texte.length) morceaux.push(document.createTextNode(texte.slice(pos)));
        remplacer(noeud, morceaux);
        morceaux.forEach((m) => annoter(m));
        return;
      }
    }
    // 2. Les rappels : une bulle par mot reconnu.
    const trouves = candidats(texte, parent);
    if (!trouves.length) return;
    const morceaux = [];
    let pos = 0;
    for (const t of trouves) {
      if (t.debut > pos) morceaux.push(document.createTextNode(texte.slice(pos, t.debut)));
      morceaux.push(bulle(t));
      pos = t.fin;
    }
    if (pos < texte.length) morceaux.push(document.createTextNode(texte.slice(pos)));
    remplacer(noeud, morceaux);
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

  // Rappels propres a une notion dans une zone : les anciens sont retires, puis la zone est relue.
  function contexte(racine, { variables = {}, abreviations = {} } = {}) {
    if (!racine) return;
    // Tout est relu : un rappel propre a la notion prime sur un rappel commun (« ua » de la fiche).
    for (const a of racine.querySelectorAll("abbr.symbole")) a.replaceWith(document.createTextNode(a.textContent));
    racine.normalize();
    const cles = (d) => Object.keys(d || {}).filter((k) => k && d[k]);
    const cv = cles(variables), ca = cles(abreviations);
    if (cv.length || ca.length) {
      contextes.set(racine, {
        variables, abreviations,
        motifVariables: cv.length ? motifDe(cv) : null,
        motifAbreviations: ca.length ? motifDe(ca) : null,
      });
    } else {
      contextes.delete(racine);
    }
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

  // --- la bulle : une seule pour la page, placee par le script, toujours dans l'ecran ----------
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
  const variables = (racine, dictionnaire) => contexte(racine, { variables: dictionnaire });
  return { annoter, contexte, variables, notion, sensChimique };
})();
