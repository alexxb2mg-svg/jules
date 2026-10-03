// Jules - gabarit "forme-musicale" : un morceau dessine en blocs de couleur (meme lettre = meme couleur =
// meme musique), curseur forme (1 = AB, 2 = ABA, 3 = couplet-refrain, 4 = rondeau ABACA) et curseur lecture
// (0 a 100 % du morceau) qui deplace une tete de lecture et allume la partie en cours.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["forme-musicale"] = {
  dessiner(svg, valeurs) {
    const forme = Math.min(4, Math.max(1, Math.round(Number(valeurs.forme ?? 2))));
    const lecture = Math.min(100, Math.max(0, Number(valeurs.lecture ?? 0)));
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    // Une couleur = une partie : A (ou le refrain) en bleu, B (ou les couplets) en orange, C en vert.
    const BLEU = "#1F4E8C", ORANGE = "#E07B00", VERT = "#2E7D32";
    const FORMES = {
      1: { titre: "Forme AB", parties: [["A", "A", BLEU], ["B", "B", ORANGE]] },
      2: { titre: "Forme ABA", parties: [["A", "A", BLEU], ["B", "B", ORANGE], ["A", "A", BLEU]] },
      3: {
        titre: "Couplet-refrain",
        parties: [["C1", "C", ORANGE], ["R", "R", BLEU], ["C2", "C", ORANGE], ["R", "R", BLEU], ["C3", "C", ORANGE], ["R", "R", BLEU]],
      },
      4: {
        titre: "Rondeau ABACA",
        parties: [["A", "A", BLEU], ["B", "B", ORANGE], ["A", "A", BLEU], ["C", "C", VERT], ["A", "A", BLEU]],
      },
    };
    const { titre, parties } = FORMES[forme];
    const n = parties.length;
    const X0 = 20, L = 300, ECART = 4;
    const larg = L / n;
    const enCours = Math.min(n - 1, Math.floor((lecture / 100) * n));
    const [etiquette, musique] = parties[enCours];
    // Combien de fois cette musique a deja ete entendue (couplets : meme melodie, paroles nouvelles).
    const fois = parties.slice(0, enCours + 1).filter((p) => p[1] === musique).length;

    svg.setAttribute("viewBox", "0 0 340 250");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS
    el("text", { x: 170, y: 26, "font-size": 18, "font-weight": 700, "text-anchor": "middle", fill: "#14243B" }, titre);

    // Tete de lecture rouge, tracee sous les blocs : la partie en cours (opaque) la cache, la lettre reste lisible.
    const xt = X0 + (lecture / 100) * L;
    el("line", { x1: xt, y1: 50, x2: xt, y2: 150, stroke: "#C8102E", "stroke-width": 3 });

    parties.forEach(([texte, mus, couleur], i) => {
      const x = X0 + i * larg + ECART / 2;
      const actif = i === enCours;
      el("rect", {
        x, y: 62, width: larg - ECART, height: 70, rx: 6, fill: couleur,
        "fill-opacity": actif ? 1 : 0.4, stroke: actif ? "#14243B" : "none", "stroke-width": 3,
      });
      el("text", {
        x: x + (larg - ECART) / 2, y: 105, "font-size": n > 5 ? 17 : 22, "font-weight": 700,
        "text-anchor": "middle", fill: actif ? "#FFFFFF" : "#14243B",
      }, texte);
      // Trait sous chaque partie qui a la meme musique que la partie en cours : ce qui revient se voit.
      if (mus === musique) el("rect", { x, y: 138, width: larg - ECART, height: 6, rx: 3, fill: couleur });
    });

    // Fleche du temps.
    el("line", { x1: X0, y1: 160, x2: X0 + L - 8, y2: 160, stroke: "#6B7686", "stroke-width": 2 });
    el("polygon", { points: `${X0 + L},160 ${X0 + L - 10},155 ${X0 + L - 10},165`, fill: "#6B7686" });
    el("text", { x: X0, y: 178, "font-size": 13, fill: "#6B7686" }, "début");
    el("text", { x: X0 + L, y: 178, "font-size": 13, "text-anchor": "end", fill: "#6B7686" }, "temps →");

    el("polygon", { points: `${xt - 7},40 ${xt + 7},40 ${xt},51`, fill: "#C8102E" });

    // Ce que l'on entend sous la tete de lecture.
    let phrase;
    if (musique === "R") phrase = fois === 1 ? "Refrain : 1re fois" : `Refrain : il revient (${fois}e fois)`;
    else if (musique === "C") phrase = `Couplet ${fois} : paroles nouvelles`;
    else phrase = fois === 1 ? `Partie ${etiquette} : nouvelle` : `Partie ${etiquette} : elle revient (${fois}e fois)`;
    el("text", { x: 170, y: 208, "font-size": 16, "font-weight": 700, "text-anchor": "middle", fill: "#14243B" }, phrase);
    el("text", { x: 170, y: 234, "font-size": 13, "text-anchor": "middle", fill: "#6B7686" },
      forme === 3 ? "R = refrain · C = couplet" : "même lettre = même musique");
    return { forme, lecture, partie: etiquette, fois };
  },
};
