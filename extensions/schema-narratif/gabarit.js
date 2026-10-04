// Jules - gabarit "schema-narratif" : les cinq etapes d'un recit sous une courbe de tension.
// Valeurs : moment (1 a 5, etape montree), peripeties (1 a 3, nombre de pics de tension au milieu du recit),
// anglais (0 : nom de l'etape en francais ; 1 : mot anglais qui annonce l'etape, nom francais en dessous).
// Un repere rond glisse sur la courbe ; la case de l'etape s'allume ; le nom de l'etape est ecrit en grand dessous.
// Sources : schema narratif (quinaire) en cinq etapes, P. Larivaille, « L'analyse (morpho)logique du recit »,
// Poetique n° 19, 1974 (situation initiale, complication, actions, resolution, situation finale), repris par les
// programmes du cycle 3 (« Il liste globalement les etapes d'un recit », Eduscol, exemples pour la mise en oeuvre
// du programme de francais en CM1, 2025). Mots anglais : ceux de la fiche CM1 anglais « suivre une histoire »
// (Once upon a time, One day, Suddenly, In the end ; sources de la fiche : Eduscol, Anglais CM1, attendus de fin
// d'annee) ; « Finally » (enfin) est un ajout de ce gabarit pour l'etape de la resolution.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["schema-narratif"] = {
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
    const ecrire = (x, y, contenu, taille, couleur, gras) =>
      el("text", { x, y, "font-size": taille, fill: couleur, "font-family": POLICE, "font-weight": gras ? 700 : 400,
        "text-anchor": "middle" }, contenu);

    const moment = entier(valeurs.moment, 1, 1, 5);
    const peripeties = entier(valeurs.peripeties, 2, 1, 3);
    const anglais = entier(valeurs.anglais, 0, 0, 1);

    const ETAPES = [
      { court: "début", nom: "situation initiale", dit: "qui ? où ? quand ? tout est calme", en: "Once upon a time…" },
      { court: "problème", nom: "élément perturbateur", dit: "un problème arrive", en: "One day…" },
      { court: "aventures", nom: "péripéties", dit: "le héros agit, échoue, recommence", en: "Suddenly…" },
      { court: "solution", nom: "résolution", dit: "le problème est réglé", en: "Finally…" },
      { court: "fin", nom: "situation finale", dit: "tout redevient calme", en: "In the end…" },
    ];

    svg.setAttribute("viewBox", "0 0 340 290");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    const X0 = 10, L = 64; // cinq colonnes de 64 px (le mot « aventures » tient dans sa case en 13 px)
    const centre = (i) => X0 + L * i + L / 2; // i = 0..4
    const CALME = 150, HAUT = 52, MOYEN = 104;

    // colonne de l'etape montree, en fond
    el("rect", { x: X0 + L * (moment - 1) + 2, y: 30, width: L - 4, height: 186, rx: 8, fill: "#E8EEF6", stroke: "none" });

    // courbe de tension : calme, montee, pics des peripeties, descente, calme
    const pts = [[X0, CALME], [centre(0), CALME], [centre(1), MOYEN]];
    const a = X0 + L * 2 + 6, b = X0 + L * 3 - 6; // zone des peripeties
    const pas = (b - a) / peripeties;
    for (let k = 0; k < peripeties; k++) {
      const x0 = a + pas * k;
      pts.push([x0 + pas / 2, HAUT + (peripeties - 1 - k) * 8]); // chaque pic un peu plus haut : la tension monte
      pts.push([x0 + pas, k === peripeties - 1 ? HAUT + 2 : HAUT + 34]);
    }
    pts.push([centre(3), MOYEN + 6], [centre(4), CALME], [X0 + L * 5, CALME]);
    el("polyline", { points: pts.map((p) => p.join(",")).join(" "), fill: "none", stroke: BLEU, "stroke-width": 3,
      "stroke-linejoin": "round" });
    ecrire(X0 + 14, 44, "tension", 13, GRIS, false).setAttribute("text-anchor", "start");

    // hauteur de la courbe a l'abscisse x (lineaire entre deux points)
    const hauteur = (x) => {
      for (let k = 1; k < pts.length; k++) {
        const [xa, ya] = pts[k - 1], [xb, yb] = pts[k];
        if (x <= xb) return ya + ((yb - ya) * (x - xa)) / (xb - xa || 1);
      }
      return CALME;
    };
    // repere : ou en est l'histoire
    const xr = moment === 3 ? a + pas / 2 : centre(moment - 1);
    const yr = hauteur(xr);
    el("line", { x1: xr, y1: yr + 10, x2: xr, y2: 166, stroke: ORANGE, "stroke-width": 2, "stroke-dasharray": "4 4" });
    el("circle", { cx: xr, cy: yr, r: 9, fill: ORANGE, stroke: "#FFFFFF", "stroke-width": 3 });

    // cinq cases numerotees, celle du moment allumee
    ETAPES.forEach((e, i) => {
      const actif = i === moment - 1;
      el("rect", { x: X0 + L * i + 3, y: 168, width: L - 6, height: 44, rx: 7, fill: actif ? BLEU : "#FFFFFF",
        stroke: actif ? BLEU : GRIS, "stroke-width": actif ? 3 : 2 });
      ecrire(centre(i), 186, String(i + 1), 14, actif ? "#FFFFFF" : GRIS, true);
      ecrire(centre(i), 204, e.court, 13, actif ? "#FFFFFF" : ENCRE, false);
    });

    // l'etape montree, en clair
    const e = ETAPES[moment - 1];
    if (anglais) {
      ecrire(170, 246, e.en, 22, ORANGE, true);
      ecrire(170, 274, `${e.nom} : ${e.dit}`, 13, ENCRE, false);
    } else {
      ecrire(170, 246, e.nom, 20, BLEU, true);
      ecrire(170, 274, e.dit, 15, ENCRE, false);
    }
    return { moment, peripeties, anglais, etape: e.nom };
  },
};
