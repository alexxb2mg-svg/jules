// Jules - gabarit "frise-pulsations" : les pulsations d'une phrase musicale (5 secondes) dessinees en ronds sur
// une ligne de temps. tempo = ecartement des ronds (pulsations par minute) ; mesure = temps par mesure (le 1er
// est accentue : rond plein, barre de mesure avant) ; nuance = nuance de depart (1 = pp ... 6 = ff, taille des
// ronds) ; ecart = evolution de la nuance sur la phrase (> 0 crescendo, < 0 decrescendo). Une valeur absente
// (curseur que la fiche ne propose pas) n'est pas montree : pas de mesure, nuance moyenne sans nom, pas d'evolution.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["frise-pulsations"] = {
  dessiner(svg, valeurs) {
    const borne = (v, min, max) => Math.min(max, Math.max(min, v));
    const tempo = borne(Number(valeurs.tempo ?? 90), 40, 200);
    const avecMesure = valeurs.mesure !== undefined;
    const mesure = borne(Math.round(Number(valeurs.mesure ?? 4)), 2, 4);
    const avecNuance = valeurs.nuance !== undefined;
    const avecEcart = valeurs.ecart !== undefined;
    const depart = borne(Math.round(Number(valeurs.nuance ?? 4)), 1, 6);
    const ecart = borne(Math.round(Number(valeurs.ecart ?? 0)), -5, 5);
    const arrivee = borne(depart + ecart, 1, 6);
    const NUANCES = ["pp", "p", "mp", "mf", "f", "ff"];
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const DUREE = 5, X0 = 24, L = 300; // 5 secondes sur 300 px : 60 px par seconde
    const X = (s) => X0 + (s / DUREE) * L;
    const periode = 60 / tempo; // secondes entre deux pulsations
    const nb = Math.floor(DUREE / periode + 1e-9) + 1; // pulsations de 0 s a 5 s compris
    const rayon = (niveau) => 2.5 + (niveau - 1) * 1.1; // pp 2,5 px ... ff 8 px : 16 px de large au plus, ecart minimal 18 px (200 / min)
    const Y = 92;

    svg.setAttribute("viewBox", "0 0 340 220");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS
    el("text", { x: 170, y: 24, "font-size": 16, "font-weight": 700, "text-anchor": "middle", fill: "#14243B" },
      `Tempo : ${tempo} pulsations par minute`);
    if (avecMesure) {
      el("text", { x: 170, y: 44, "font-size": 13, "text-anchor": "middle", fill: "#6B7686" },
        `mesure à ${mesure} temps : le 1er temps est plein`);
    }

    for (let i = 0; i < nb; i++) {
      const x = X(i * periode);
      const niveau = nb > 1 ? depart + (arrivee - depart) * (i / (nb - 1)) : depart;
      const temps = (i % mesure) + 1;
      const fort = !avecMesure || temps === 1;
      if (avecMesure && temps === 1) {
        // Barre de mesure a mi-chemin de la pulsation precedente (jamais sur un rond, jamais hors du cadre).
        const xb = Math.max(X0 - 14, x - (L / DUREE) * periode / 2);
        el("line", { x1: xb, y1: Y - 26, x2: xb, y2: Y + 22, stroke: "#6B7686", "stroke-width": 2 });
      }
      el("circle", {
        cx: x, cy: Y, r: rayon(niveau), fill: fort ? "#1F4E8C" : "#FFFFFF", stroke: "#1F4E8C", "stroke-width": 2.5,
      });
      if (avecMesure) {
        el("text", {
          x, y: Y + 40, "font-size": 13, "text-anchor": "middle",
          "font-weight": temps === 1 ? 700 : 400, fill: temps === 1 ? "#1F4E8C" : "#6B7686",
        }, String(temps));
      }
    }

    // Ligne du temps graduee en secondes.
    const YT = 150;
    el("line", { x1: X0, y1: YT, x2: X0 + L, y2: YT, stroke: "#6B7686", "stroke-width": 2 });
    for (let s = 0; s <= DUREE; s++) {
      el("line", { x1: X(s), y1: YT - 5, x2: X(s), y2: YT + 5, stroke: "#6B7686", "stroke-width": 2 });
      el("text", { x: X(s), y: YT + 20, "font-size": 13, "text-anchor": "middle", fill: "#6B7686" }, `${s} s`);
    }

    // Nuances ecrites comme sur une partition, et soufflet (crescendo / decrescendo) en orange.
    if (avecNuance) {
      const YN = 204;
      const style = { "font-size": 18, "font-style": "italic", "font-weight": 700, "font-family": "Georgia, serif", fill: "#14243B" };
      el("text", { ...style, x: X0, y: YN }, NUANCES[depart - 1]);
      if (arrivee !== depart) {
        el("text", { ...style, x: X0 + L, y: YN, "text-anchor": "end" }, NUANCES[arrivee - 1]);
        const xa = X0 + 34, xb = X0 + L - 34, yc = YN - 6;
        const [ouvert, ferme] = arrivee > depart ? [xb, xa] : [xa, xb];
        el("polyline", {
          points: `${ouvert},${yc - 9} ${ferme},${yc} ${ouvert},${yc + 9}`,
          fill: "none", stroke: "#E07B00", "stroke-width": 2.5, "stroke-linejoin": "round",
        });
      } else if (avecEcart) {
        // ecart non nul mais deja au bout de l'echelle : on le dit au lieu de dessiner un soufflet faux.
        const mot = ecart > 0 ? "déjà le plus fort possible" : ecart < 0 ? "déjà le plus doux possible" : "nuance stable";
        el("text", { x: X0 + 40, y: YN, "font-size": 13, fill: "#6B7686" }, mot);
      }
    }
    return { tempo, pulsations: nb, mesure: avecMesure ? mesure : null, depart, arrivee };
  },
};
