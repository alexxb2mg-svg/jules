// Jules - gabarit "pistes-superposees" : 1 a 4 pistes horizontales empilees (une par voix, instrument ou source
// sonore) portant des blocs de son sur 16 mesures, et une barre de lecture verticale (lecture, 0 a 100 %) qui
// allume ce qui sonne au meme moment. On lit le successif de gauche a droite, le simultane de haut en bas.
// decalage = 0 : chaque piste joue sa propre partie (une couleur par partie : melodie, ostinato, bourdon, basse) ;
// decalage > 0 : canon, chaque voix chante la MEME melodie (meme couleur) et entre `decalage` mesures apres la
// precedente.
// Sources : programme d'education musicale du cycle 4 (BO n° 31 du 30/07/2020), six domaines dont « le successif
// et le simultane » ; Eduscol, « Education musicale, L'ecoute, reperes » (2017) : « percevoir et/ou produire un
// ostinato rythmique [...] domaine Successif et simultane » ; Wikipedia « Polyphonie » (oldid 236946485, source
// de la fiche 3e) et « Canon (musique) » : un canon superpose une meme melodie chantee par plusieurs voix qui
// entrent l'une apres l'autre. Aucune donnee chiffree n'est ecrite par la figure (compte des pistes sous la barre).
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["pistes-superposees"] = {
  dessiner(svg, valeurs) {
    const borne = (v, mini, maxi, defaut) => {
      const n = Number(v ?? defaut);
      return Math.min(maxi, Math.max(mini, Number.isFinite(n) ? n : defaut));
    };
    const voix = Math.round(borne(valeurs.voix, 1, 4, 2));
    const decalage = Math.round(borne(valeurs.decalage, 0, 4, 0));
    const lecture = borne(valeurs.lecture, 0, 100, 25);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", ROUGE = "#C8102E", VERT = "#2E7D32", ORANGE = "#E07B00";
    // Une partie = des blocs [debut, duree] en mesures, sur un motif de 4 mesures repete.
    const MELODIE = [[0, 1], [1.25, 0.5], [2, 1.25], [3.5, 0.5]];
    const PARTIES = [
      { couleur: BLEU, motif: MELODIE }, // melodie
      { couleur: ORANGE, motif: [[0, 0.5], [1, 0.5], [2, 0.5], [3, 0.5]] }, // ostinato : court et regulier
      { couleur: VERT, motif: [[0, 3.75]] }, // bourdon : note tenue
      { couleur: ENCRE, motif: [[0, 1.75], [2, 1.75]] }, // basse
    ];
    const MESURES = 16, X0 = 44, L = 288, Y0 = 34, H_PISTE = 46;
    const X = (m) => X0 + (m / MESURES) * L;
    const canon = decalage > 0;
    const t = Math.min((lecture / 100) * MESURES, MESURES - 0.001);

    svg.setAttribute("viewBox", "0 0 340 310");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // Grille legere des mesures (une ligne toutes les 4 mesures, plus marquee).
    for (let m = 0; m <= MESURES; m += 4) {
      el("line", { x1: X(m), y1: Y0 - 4, x2: X(m), y2: Y0 + 4 * H_PISTE, stroke: "#D5DAE1", "stroke-width": 2 });
    }

    let sonnent = 0;
    for (let v = 0; v < 4; v++) {
      const yc = Y0 + v * H_PISTE + H_PISTE / 2;
      const active = v < voix;
      el("text", { x: 22, y: yc + 5, "font-size": 15, "font-weight": 700, "text-anchor": "middle", fill: active ? ENCRE : "#B8C0CB" }, String(v + 1));
      if (!active) {
        // Piste vide : on voit qu'on peut ajouter une voix.
        el("line", { x1: X0, y1: yc, x2: X0 + L, y2: yc, stroke: "#B8C0CB", "stroke-width": 2, "stroke-dasharray": "4 6" });
        continue;
      }
      el("line", { x1: X0, y1: yc, x2: X0 + L, y2: yc, stroke: GRIS, "stroke-width": 2, "stroke-opacity": 0.35 });
      const partie = canon ? PARTIES[0] : PARTIES[v];
      const entree = canon ? v * decalage : 0;
      let joue = false;
      for (let debut = entree; debut < MESURES; debut += 4) {
        for (const [d, duree] of partie.motif) {
          const s = debut + d;
          if (s >= MESURES) continue;
          const e = Math.min(MESURES, s + duree);
          const dessous = t >= s && t < e;
          if (dessous) joue = true;
          el("rect", {
            x: X(s), y: yc - 13, width: Math.max(4, X(e) - X(s) - 2), height: 26, rx: 5, fill: partie.couleur,
            "fill-opacity": dessous ? 1 : 0.35, stroke: dessous ? ENCRE : "none", "stroke-width": 3,
          });
        }
      }
      if (canon && v > 0) {
        // Entree retardee : petite fleche grise vers le debut de la voix.
        el("polygon", { points: `${X(entree) - 2},${yc - 20} ${X(entree) + 8},${yc - 20} ${X(entree) + 3},${yc - 14}`, fill: GRIS });
      }
      if (joue) sonnent += 1;
    }

    // Barre de lecture rouge, au-dessus des blocs.
    const xb = X(t);
    el("line", { x1: xb, y1: Y0 - 8, x2: xb, y2: Y0 + 4 * H_PISTE + 2, stroke: ROUGE, "stroke-width": 3 });
    el("polygon", { points: `${xb - 7},${Y0 - 16} ${xb + 7},${Y0 - 16} ${xb},${Y0 - 6}`, fill: ROUGE });

    // Fleche du temps.
    const ya = Y0 + 4 * H_PISTE + 16;
    el("line", { x1: X0, y1: ya, x2: X0 + L - 8, y2: ya, stroke: GRIS, "stroke-width": 2 });
    el("polygon", { points: `${X0 + L},${ya} ${X0 + L - 10},${ya - 5} ${X0 + L - 10},${ya + 5}`, fill: GRIS });
    el("text", { x: X0 + L, y: ya + 17, "font-size": 13, "text-anchor": "end", fill: GRIS }, "temps →");

    // Ce qui sonne sous la barre (un compte de pistes visibles, pas la reponse d'un exercice).
    let phrase;
    if (sonnent === 0) phrase = "Sous la barre : silence";
    else if (sonnent === 1) phrase = "Sous la barre : 1 seul son";
    else phrase = `Sous la barre : ${sonnent} sons en même temps`;
    el("text", { x: 170, y: ya + 42, "font-size": 16, "font-weight": 700, "text-anchor": "middle", fill: ENCRE }, phrase);
    el("text", { x: 170, y: ya + 62, "font-size": 13, "text-anchor": "middle", fill: GRIS },
      voix === 1 ? "une seule piste : les sons se suivent"
        : canon ? "même couleur = même mélodie, décalée" : "une couleur = une partie différente");
    return { voix, decalage, lecture, sonnent };
  },
};
