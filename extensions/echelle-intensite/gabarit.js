// Jules - gabarit "echelle-intensite" : des mots ranges du plus faible au plus fort sur une echelle verticale.
// Valeurs : serie (1 a 7, la serie de mots) et degre (0 a 4, le mot montre). Une jauge bleue monte jusqu'au mot
// choisi, ecrit en blanc sur fond bleu ; les autres restent en petit. Series 1 et 2 : deux contraires aux deux bouts
// (le mot oppose s'allume en orange avec une accolade « contraire ») ; series 3 a 6 : un meme sens qui se renforce
// (synonymes de force differente) ; serie 7 : un avis en anglais, avec un visage qui sourit de plus en plus.
// Absorbe la proposition d'audit « echelle-nuances » (SPEC vague 2, § 2.2).
// Sources des series : gradations usuelles des manuels (inquietude, crainte, peur, frayeur, terreur ; agace, irrite,
// fache, furieux, enrage) ; programme de francais du cycle 4 (Annexe 1, education.gouv.fr : « Maitriser le classement
// par degre d'intensite et de generalite », « analyser en contexte le sens des mots : synonymie, antonymie ») ;
// cycle 3 (synonymie, antonymie : Eduscol, exemples pour la mise en oeuvre du programme de francais en CM1, 2025).
// L'ordre fin entre deux voisins (irrite / fache, satisfait / content) reste une affaire de nuance : la figure montre
// une tendance, pas une regle.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["echelle-intensite"] = {
  dessiner(svg, valeurs) {
    const NS = "http://www.w3.org/2000/svg";
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", ORANGE = "#E07B00";
    const entier = (v, defaut, mini, maxi) => {
      const x = Number(v);
      return Math.min(maxi, Math.max(mini, Math.round(Number.isFinite(x) ? x : defaut)));
    };
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte; // texte brut, jamais interprete
      svg.appendChild(e);
      return e;
    };
    const POLICE = "system-ui, Arial, sans-serif";
    const ecrire = (x, y, contenu, taille, couleur, gras, ancre) =>
      el("text", { x, y, "font-size": taille, fill: couleur, "font-family": POLICE, "font-weight": gras ? 700 : 400,
        "text-anchor": ancre || "start" }, contenu);
    const largeur = (t, taille, gras) => {
      let l = 0;
      try { l = t.getComputedTextLength(); } catch (e) { l = 0; }
      return l > 0 ? l : t.textContent.length * taille * (gras ? 0.6 : 0.55);
    };

    // mots[0] = le plus faible (ou un bout), mots[4] = le plus fort (ou l'autre bout)
    const SERIES = [
      { titre: "Deux contraires aux deux bouts", mots: ["glacé", "froid", "tiède", "chaud", "brûlant"], bouts: true },
      { titre: "Deux contraires aux deux bouts", mots: ["minuscule", "petit", "moyen", "grand", "immense"], bouts: true },
      { titre: "La peur, de faible à fort", mots: ["inquiétude", "crainte", "peur", "frayeur", "terreur"], bas: "faible", haut: "fort" },
      { titre: "La colère, de faible à fort", mots: ["agacé", "irrité", "fâché", "furieux", "enragé"], bas: "faible", haut: "fort" },
      { titre: "La joie, de faible à fort", mots: ["satisfait", "content", "heureux", "ravi", "euphorique"], bas: "faible", haut: "fort" },
      { titre: "Du doute à la certitude", mots: ["peut-être", "il semble que", "sans doute", "certainement", "assurément"], bas: "doute", haut: "certain" },
      { titre: "Mon avis (anglais)", mots: ["I hate it!", "I don't like it.", "It's OK.", "I like it.", "I love it!"], bas: "je déteste", haut: "j'adore", visage: true },
    ];
    const serie = entier(valeurs.serie, 1, 1, SERIES.length);
    const degre = entier(valeurs.degre, 2, 0, 4);
    const S = SERIES[serie - 1];

    svg.setAttribute("viewBox", "0 0 340 340");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    ecrire(20, 26, S.titre, 15, ENCRE, true);
    const y = (i) => 296 - 46 * i; // ligne de base du mot i
    const GX = 40, GL = 22, GH = 92, GB = 312; // jauge : x, largeur, haut, bas

    // jauge : vide, puis remplie jusqu'au mot choisi
    el("rect", { x: GX, y: GH, width: GL, height: GB - GH, rx: 11, fill: "#FFFFFF", stroke: GRIS, "stroke-width": 2 });
    const haut = y(degre) - 6;
    el("rect", { x: GX, y: haut, width: GL, height: GB - haut, rx: 11, fill: BLEU });
    for (let i = 0; i < 5; i++) {
      el("line", { x1: GX + GL, y1: y(i) - 6, x2: GX + GL + 8, y2: y(i) - 6, stroke: GRIS, "stroke-width": 2 });
    }
    if (S.bas) {
      ecrire(GX + GL / 2, 332, S.bas, 13, GRIS, false, "middle");
      ecrire(GX + GL / 2, 84, S.haut, 13, GRIS, false, "middle");
    }

    // les mots ; celui du degre en blanc sur fond bleu
    const oppose = S.bouts && degre !== 2 ? 4 - degre : -1;
    for (let i = 0; i < 5; i++) {
      if (i === degre) {
        const t = ecrire(84, y(i), S.mots[i], 20, "#FFFFFF", true);
        const l = largeur(t, 20, true);
        const fond = el("rect", { x: 76, y: y(i) - 24, width: l + 16, height: 32, rx: 8, fill: BLEU });
        svg.insertBefore(fond, t); // le fond passe sous le texte
        el("polygon", { points: `${GX + GL + 10},${y(i) - 6} ${74},${y(i) - 14} ${74},${y(i) + 2}`, fill: BLEU });
      } else {
        ecrire(84, y(i), S.mots[i], 16, i === oppose ? ORANGE : ENCRE, i === oppose);
      }
    }

    // contraires : accolade orange entre le mot choisi et l'autre bout
    if (oppose >= 0) {
      const ya = y(degre) - 8, yb = y(oppose) - 8, X = 296;
      el("path", { d: `M${X - 12},${ya} H${X} V${yb} H${X - 12}`, fill: "none", stroke: ORANGE, "stroke-width": 3 });
      const t = ecrire(X + 18, (ya + yb) / 2, "contraire", 14, ORANGE, true, "middle");
      t.setAttribute("transform", `rotate(-90 ${X + 18} ${(ya + yb) / 2})`);
    }

    // avis en anglais : un visage qui sourit de plus en plus
    if (S.visage) {
      const cx = 296, cy = 50;
      el("circle", { cx, cy, r: 26, fill: "#FDF0E1", stroke: ORANGE, "stroke-width": 3 });
      el("circle", { cx: cx - 9, cy: cy - 7, r: 3.5, fill: ENCRE });
      el("circle", { cx: cx + 9, cy: cy - 7, r: 3.5, fill: ENCRE });
      const c = cy + 10 + (degre - 2) * 7; // sous la bouche : sourire ; au-dessus : bouche triste
      el("path", { d: `M${cx - 13},${cy + 10} Q${cx},${c} ${cx + 13},${cy + 10}`, fill: "none", stroke: ENCRE,
        "stroke-width": 3, "stroke-linecap": "round" });
    }
    return { serie, degre, mot: S.mots[degre] };
  },
};
