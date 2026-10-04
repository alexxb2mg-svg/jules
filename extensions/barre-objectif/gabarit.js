// Jules - gabarit "barre-objectif" : une minute de lecture a voix haute, en une barre horizontale.
// Valeurs lus (mots lus en une minute) et erreurs (mots mal lus). La partie bleue = mots bien lus (lus - erreurs),
// la partie rouge = erreurs, posees bout a bout sur une regle graduee de 0 a 160 mots ; un trait vert marque le
// repere du CM1. Le nombre de mots bien lus n'est JAMAIS ecrit : l'eleve le lit sur la regle (revele false).
// Fait verifie : « Lire correctement en ciblant 110 mots par minute en moyenne » (objectif « Lire avec fluidite »),
// Eduscol, Exemples pour la mise en oeuvre du programme de francais en CM1 (programmes 2025), p. 3,
// https://eduscol.education.gouv.fr/sites/default/files/document/exemplesmiseenoeuvrecm1-francaispdf-111546.pdf
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["barre-objectif"] = {
  dessiner(svg, valeurs) {
    const NS = "http://www.w3.org/2000/svg";
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", ROUGE = "#C8102E", VERT = "#2E7D32";
    const borne = (v, defaut, mini, maxi) => {
      const x = Number(v);
      return Math.min(maxi, Math.max(mini, Number.isFinite(x) ? x : defaut));
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
        "text-anchor": ancre || "middle" }, contenu);

    const MAX = 160, REPERE = 110;
    const lus = Math.round(borne(valeurs.lus, 95, 0, MAX));
    const erreurs = Math.round(borne(valeurs.erreurs, 9, 0, lus)); // jamais plus d'erreurs que de mots lus
    const bien = lus - erreurs;

    svg.setAttribute("viewBox", "0 0 340 230");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    const X0 = 26, X1 = 314, Y = 76, H = 42;
    const px = (mots) => X0 + (mots / MAX) * (X1 - X0);

    ecrire(170, 24, "Une minute de lecture", 16, ENCRE, true);

    // fond de la barre : la minute entiere (vide)
    el("rect", { x: X0, y: Y, width: X1 - X0, height: H, rx: 6, fill: "#FFFFFF", stroke: GRIS, "stroke-width": 2 });
    // mots bien lus (bleu) puis erreurs (rouge), bout a bout
    if (bien > 0) el("rect", { x: X0, y: Y, width: px(bien) - X0, height: H, fill: BLEU, stroke: "none" });
    if (erreurs > 0) el("rect", { x: px(bien), y: Y, width: px(lus) - px(bien), height: H, fill: ROUGE, stroke: "none" });
    // fin de lecture : un trait fonce au bout de la barre
    el("line", { x1: px(lus), y1: Y - 4, x2: px(lus), y2: Y + H + 4, stroke: ENCRE, "stroke-width": 3 });

    // regle graduee : un trait tous les 10 mots, un nombre tous les 20
    const YR = Y + H + 8;
    el("line", { x1: X0, y1: YR, x2: X1, y2: YR, stroke: ENCRE, "stroke-width": 2 });
    for (let m = 0; m <= MAX; m += 10) {
      const grand = m % 20 === 0;
      el("line", { x1: px(m), y1: YR, x2: px(m), y2: YR + (grand ? 10 : 6), stroke: ENCRE, "stroke-width": 2 });
      if (grand) ecrire(px(m), YR + 26, String(m), 13, ENCRE, false);
    }
    ecrire(X1, YR + 44, "mots", 13, GRIS, false, "end");

    // repere du CM1 : trait vert vertical
    el("line", { x1: px(REPERE), y1: Y - 22, x2: px(REPERE), y2: YR + 12, stroke: VERT, "stroke-width": 3,
      "stroke-dasharray": "6 4" });
    ecrire(px(REPERE), Y - 28, "repère CM1", 14, VERT, true);

    // legende : une couleur = une idee
    const YL = 204;
    el("rect", { x: 28, y: YL - 14, width: 18, height: 18, rx: 3, fill: BLEU });
    ecrire(52, YL, "mots bien lus", 14, BLEU, true, "start");
    el("rect", { x: 196, y: YL - 14, width: 18, height: 18, rx: 3, fill: ROUGE });
    ecrire(220, YL, "erreurs", 14, ROUGE, true, "start");

    return { lus, erreurs, bien_lus: bien, repere_atteint: bien >= REPERE };
  },
};
