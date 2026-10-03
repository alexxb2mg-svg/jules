// Jules - gabarit "frise" : frise chronologique generique, bornee par deux curseurs (debut, fin) et parcourue par
// un repere mobile. Les reperes NOMMES (evenements, periodes, oeuvres) ne sont pas dans ce fichier : ils sont portes
// par la fiche (curseurs figes et lectures du bloc graphe). Noms de curseurs reconnus :
//   « début » (ou debut), fin   bornes de la frise, figees par la fiche (min = max) ; nombres negatifs = av. J.-C.
//   date (ou annee)             repere principal (bleu), en annees
//   mois                        a la place de date : frise graduee en mois (1 = janvier ... 12 = decembre)
//   souvenir                    a la place de date : frise en ages (« je vis : 10 ans »)
//   intervalle                  second repere (vert) a date + intervalle, ecart ecrit en orange
//   auteur                      avec souvenir : second repere a l'age ou l'auteur ecrit (« j'ecris : 50 ans »)
//   de, « à » (ou a)            une periode surlignee en orange au-dessus de l'axe, vive quand le repere est dedans
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["frise"] = {
  dessiner(svg, valeurs) {
    const NS = "http://www.w3.org/2000/svg";
    const BLEU = "#1F4E8C", GRIS = "#6B7686", ENCRE = "#14243B", ROUGE = "#C8102E", VERT = "#2E7D32", ORANGE = "#E07B00";
    const MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"];
    const MOIS_COURT = ["janv.", "févr.", "mars", "avril", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."];
    const nombre = (v, d) => (Number.isFinite(Number(v)) ? Number(v) : d);
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };

    // --- ce que la fiche a donne ----------------------------------------------------------------------------
    const unite = "mois" in valeurs ? "mois" : "souvenir" in valeurs ? "age" : "annee";
    const cle = unite === "mois" ? "mois" : unite === "age" ? "souvenir" : "date" in valeurs ? "date" : "annee";
    let lo = nombre(valeurs["début"] ?? valeurs.debut, unite === "mois" ? 1 : unite === "age" ? 0 : 1900);
    let hi = nombre(valeurs.fin, unite === "mois" ? 12 : unite === "age" ? 80 : 2000);
    if (lo > hi) [lo, hi] = [hi, lo];
    if (lo === hi) hi = lo + 1;
    const p = nombre(valeurs[cle], (lo + hi) / 2);
    let q = null; // second repere
    if (unite === "age" && "auteur" in valeurs) q = nombre(valeurs.auteur, p);
    else if (unite !== "age" && "intervalle" in valeurs) q = p + nombre(valeurs.intervalle, 0);
    const finPeriode = valeurs["à"] ?? valeurs.a;
    const periode = "de" in valeurs && finPeriode !== undefined ? [nombre(valeurs.de, lo), nombre(finPeriode, hi)].sort((m, n) => m - n) : null;

    // --- mise en page --------------------------------------------------------------------------------------
    const X0 = 28, X1 = 312, YA = 100; // axe de X0 a X1, barre centree sur YA
    const H = q === null ? 160 : 230;
    const borne = (v) => Math.min(hi, Math.max(lo, v));
    const X = (v) => X0 + ((borne(v) - lo) / (hi - lo)) * (X1 - X0);
    const ecrire = (v) => {
      if (unite === "mois") return MOIS[(Math.round(v) - 1 + 1200) % 12];
      if (unite === "age") return `${v} ans`;
      if (v < 0) return `${-v} av. J.-C.`;
      return v === 0 ? "vers J.-C." : String(v);
    };
    const graduation = (v) => (unite === "mois" ? MOIS_COURT[(Math.round(v) - 1 + 1200) % 12] : String(v).replace("-", "−"));
    // Texte centre sur x mais jamais hors du cadre (largeur estimee : 0,6 em par caractere).
    const texte = (x, y, chaine, taille, couleur, gras) => {
      const demi = (chaine.length * taille * 0.6) / 2;
      const cx = Math.min(340 - 4 - demi, Math.max(4 + demi, x));
      return el("text", { x: cx, y, "font-size": taille, "text-anchor": "middle", fill: couleur, "font-weight": gras ? 700 : 400 }, chaine);
    };

    svg.setAttribute("viewBox", `0 0 340 ${H}`);
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // Periode surlignee (de -> a), au-dessus de l'axe.
    if (periode && periode[1] >= lo && periode[0] <= hi) {
      const dedans = p >= periode[0] && p <= periode[1];
      const xa = X(periode[0]), xb = X(periode[1]);
      el("rect", { x: xa, y: 62, width: Math.max(4, xb - xa), height: 16, rx: 4, fill: ORANGE, opacity: dedans ? 1 : 0.35 });
    }

    // Axe : avenir en gris, passe (jusqu'au repere) en bleu.
    el("rect", { x: X0, y: YA - 6, width: X1 - X0, height: 12, rx: 6, fill: "#D5DAE1" });
    el("rect", { x: X0, y: YA - 6, width: Math.max(0, X(p) - X0), height: 12, rx: 6, fill: BLEU, opacity: 0.85 });
    if (q !== null) {
      // L'ecart entre les deux reperes, en orange sur l'axe.
      const xa = Math.min(X(p), X(q)), xb = Math.max(X(p), X(q));
      el("rect", { x: xa, y: YA - 6, width: Math.max(0, xb - xa), height: 12, fill: ORANGE });
    }

    // Graduations : pas « rond » (1, 2, 5, 10, 20, 50...), au plus 6 intervalles ; bornes toujours ecrites.
    const pas = unite === "mois" ? 1 : [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000].find((s) => (hi - lo) / s <= 6) || 5000;
    const etiquettes = [lo, hi];
    for (let v = Math.ceil(lo / pas) * pas; v <= hi; v += pas) {
      el("line", { x1: X(v), y1: YA + 6, x2: X(v), y2: YA + 13, stroke: GRIS, "stroke-width": 2 });
      if (Math.abs(X(v) - X(lo)) > 40 && Math.abs(X(hi) - X(v)) > 40) etiquettes.push(v);
    }
    for (const v of [lo, hi]) el("line", { x1: X(v), y1: YA + 6, x2: X(v), y2: YA + 13, stroke: GRIS, "stroke-width": 2 });
    for (const v of etiquettes) texte(X(v), YA + 31, graduation(v), 13, GRIS, false);
    // Avant / apres J.-C. : le zero est marque quand la frise le traverse.
    if (unite === "annee" && lo < 0 && hi > 0) {
      el("line", { x1: X(0), y1: YA - 14, x2: X(0), y2: YA + 14, stroke: ENCRE, "stroke-width": 2 });
      if (X(0) - X0 > 80) el("text", { x: X(0) - 6, y: YA + 50, "font-size": 13, "text-anchor": "end", fill: GRIS }, "av. J.-C.");
      if (X1 - X(0) > 80) el("text", { x: X(0) + 6, y: YA + 50, "font-size": 13, "text-anchor": "start", fill: GRIS }, "ap. J.-C.");
    }

    // Repere principal (bleu), etiquette en haut ; pointille s'il sort de la frise.
    const xp = X(p), dehors = p < lo || p > hi;
    el("line", { x1: xp, y1: 40, x2: xp, y2: YA + 16, stroke: BLEU, "stroke-width": 3, "stroke-dasharray": dehors ? "5 4" : "none" });
    el("circle", { cx: xp, cy: YA, r: 8, fill: "#FFFFFF", stroke: BLEU, "stroke-width": 3 }).setAttribute("data-adresse", "graphe/repere");
    texte(xp, 30, unite === "age" ? `je vis : ${ecrire(p)}` : ecrire(p), 16, BLEU, true);

    if (q !== null) {
      // Second repere (vert), etiquette en bas ; ecart ecrit sous la frise.
      const xq = X(q), avant = unite === "age" && q < p;
      // Le trait vert s'interrompt a la hauteur des graduations pour ne pas couvrir leurs nombres.
      const tirets = q < lo || q > hi ? "5 4" : "none";
      el("line", { x1: xq, y1: YA - 16, x2: xq, y2: YA + 14, stroke: VERT, "stroke-width": 3, "stroke-dasharray": tirets });
      el("line", { x1: xq, y1: YA + 38, x2: xq, y2: 168, stroke: VERT, "stroke-width": 3, "stroke-dasharray": tirets });
      el("circle", { cx: xq, cy: YA, r: 7, fill: VERT });
      texte(xq, 186, unite === "age" ? `j'écris : ${ecrire(q)}` : ecrire(q), 16, VERT, true);
      const ecart = Math.abs(q - p);
      const mot = unite === "mois" ? "mois" : "ans";
      texte((Math.min(xp, xq) + Math.max(xp, xq)) / 2, 216, avant ? "impossible : on écrit après avoir vécu" : `écart : ${ecart} ${mot}`, 14, avant ? ROUGE : ORANGE, true);
    }
    return { [cle]: p, ...(q === null ? {} : { second: q }), debut: lo, fin: hi };
  },
};
