// Jules - gabarit "suite-motifs" : une suite de motifs en carres qui grandit d'etape en etape (CM1).
// Etape n : un bloc « depart » (bleu) puis (n - 1) blocs de « ajout » carres (orange), chaque bloc en colonne,
// separes d'un petit espace : la regle « on ajoute toujours le meme nombre » se voit et se compte.
// Le bloc ajoute a l'etape affichee est orange plein, les ajouts plus anciens orange pale.
// Au-dela de 4 etapes, seules les etapes 1, 2, 3 et la derniere sont dessinees (trois points entre les deux) :
// pour une etape lointaine, on n'a pas besoin de tout dessiner. Aucun nombre de carres n'est ecrit.
// Source (notion) : programme de mathematiques du cycle 3, arrete du 10-4-2025 (BO n° 16 du 17/04/2025), suites
// et programmes de calcul ; Eduscol, « Exemples de reussite » CM1 (2025), p. 14.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["suite-motifs"] = {
  // dessiner(svg, valeurs) : etape de 1 a 8, depart de 1 a 5 carres, ajout de 1 a 5 carres par etape.
  dessiner(svg, valeurs) {
    const ent = (v, d, mini, maxi) => {
      const n = Math.round(Number(v ?? d));
      return Math.min(maxi, Math.max(mini, Number.isFinite(n) ? n : d));
    };
    const etape = ent(valeurs.etape, 3, 1, 8);
    const depart = ent(valeurs.depart, 1, 1, 5);
    const ajout = ent(valeurs.ajout, 2, 1, 5);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", ORANGE = "#E07B00";
    svg.setAttribute("viewBox", "0 0 340 340");
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    // Etapes dessinees : toutes jusqu'a 4, sinon 1, 2, 3 ... et la derniere.
    const lignes = etape <= 4 ? Array.from({ length: etape }, (_, i) => i + 1) : [1, 2, 3, etape];
    const saut = etape > 4;

    // Taille d'un carre : fixee par depart et ajout seulement (bouger « etape » ne change jamais l'echelle).
    // Place prevue : 4 lignes, les trois points, 8 blocs en largeur.
    const hauteurBloc = Math.max(depart, ajout);
    const DISPO = (318 - 22) / 4 - 12;
    const c = Math.max(10, Math.min(22, Math.floor(DISPO / hauteurBloc) - 2));
    const pasV = c + 2, ECART = 8, X0 = 84;
    const hauteurLigne = hauteurBloc * pasV;

    let y = 14;
    lignes.forEach((n, i) => {
      if (saut && i === 3) {
        // Les trois points : des etapes non dessinees.
        for (let k = 0; k < 3; k++) el("circle", { cx: X0 + 10 + k * 14, cy: y + 4, r: 3, fill: GRIS });
        y += 22;
      }
      const bas = y + hauteurLigne;
      el("text", { x: 10, y: (y + bas) / 2 + 5, "font-size": 14, fill: n === etape ? ENCRE : GRIS, "font-weight": n === etape ? 700 : 400, "font-family": "sans-serif" }, `étape ${n}`);
      let x = X0;
      for (let b = 0; b < n; b++) {
        const nb = b === 0 ? depart : ajout;
        const nouveau = b > 0 && b === n - 1;
        const remplissage = b === 0 ? "#DCE8F6" : nouveau ? ORANGE : "#FBE3C4";
        const trait = b === 0 ? BLEU : ORANGE;
        for (let k = 0; k < nb; k++) {
          el("rect", { x, y: bas - (k + 1) * pasV + 1, width: c, height: c, rx: 2, fill: remplissage, stroke: trait, "stroke-width": 2 });
        }
        x += c + ECART;
      }
      y = bas + 12;
    });
    return { etape, depart, ajout, c };
  },
};
