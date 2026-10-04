// Jules - gabarit "patron-cube" : un patron de cube a plat dont les faces se replient (CM1, solides).
// pliage 0 = patron a plat, 10 = pliage fini (chaque face a tourne d'un quart de tour autour de son arete
// commune avec sa voisine). modele 1 = patron en croix, 2 = patron en escalier (deux des 11 patrons du cube),
// 3 = six carres qui ne forment PAS un patron (un bloc de 2 carres sur 2) : plie jusqu'au bout, deux faces
// arrivent au meme endroit (en rouge) et un cote du cube reste ouvert (pointilles rouges).
// Vue en perspective (on regarde la table de biais) ; calcul 3D par rotations autour des aretes, faces dessinees
// de la plus lointaine a la plus proche, legerement transparentes pour deviner les faces cachees.
// Sources : programme de mathematiques du cycle 3, arrete du 10-4-2025 (BO n° 16 du 17/04/2025), solides et
// patrons ; Eduscol, « Exemples de reussite » CM1 (2025), p. 21-22 ; le cube a 11 patrons distincts, aucun ne
// contient un bloc de 2 x 2 carres (resultat classique de geometrie, repris par la fiche « les solides »).
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["patron-cube"] = {
  // dessiner(svg, valeurs) : pliage de 0 a 10, modele 1 (croix), 2 (escalier) ou 3 (faux patron).
  dessiner(svg, valeurs) {
    const ent = (v, d, mini, maxi) => {
      const n = Math.round(Number(v ?? d));
      return Math.min(maxi, Math.max(mini, Number.isFinite(n) ? n : d));
    };
    const pliage = ent(valeurs.pliage, 5, 0, 10);
    const modele = ent(valeurs.modele, 1, 1, 3);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const f = (n) => n.toFixed(1);
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", ROUGE = "#C8102E";
    svg.setAttribute("viewBox", "0 0 340 340");
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    // Les patrons : carres [colonne, rangee, parent] ; la face 0 reste posee sur la table, chaque autre face
    // tourne autour de l'arete qu'elle partage avec son parent. Rangee qui grandit = plus loin sur la table.
    const PATRONS = {
      1: [[1, 1, -1], [1, 0, 0], [1, 2, 0], [1, 3, 2], [0, 1, 0], [2, 1, 0]],
      2: [[1, 1, -1], [1, 0, 0], [0, 0, 1], [2, 1, 0], [2, 2, 3], [3, 2, 4]],
      3: [[1, 0, -1], [0, 0, 0], [2, 0, 0], [3, 0, 2], [1, 1, 0], [2, 1, 2]],
    };
    const faces = PATRONS[modele];

    // Transformations affines 3D : [[r00, r01, r02, t0], [r10, ...], [r20, ...]].
    const ID = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]];
    const compose = (A, B) => A.map((ligne) => [0, 1, 2, 3].map((j) =>
      ligne[0] * B[0][j] + ligne[1] * B[1][j] + ligne[2] * B[2][j] + (j === 3 ? ligne[3] : 0)));
    const applique = (M, p) => M.map((l) => l[0] * p[0] + l[1] * p[1] + l[2] * p[2] + l[3]);
    // Rotation d'angle t autour de l'axe horizontal (selon x si ax = 0, selon y si ax = 1) passant par P.
    const rotation = (ax, P, t) => {
      const c = Math.cos(t), s = Math.sin(t);
      const R = ax === 0 ? [[1, 0, 0], [0, c, -s], [0, s, c]] : [[c, 0, s], [0, 1, 0], [-s, 0, c]];
      return R.map((l, i) => [l[0], l[1], l[2], P[i] - (l[0] * P[0] + l[1] * P[1] + l[2] * P[2])]);
    };
    const replie = (theta) => {
      const T = [];
      faces.forEach(([i, j, p], k) => {
        if (p < 0) { T[k] = ID; return; }
        const [pi, pj] = faces[p];
        const ax = pi === i ? 0 : 1;                     // arete commune horizontale (selon x) ou verticale
        const P = ax === 0 ? [0, Math.max(j, pj), 0] : [Math.max(i, pi), 0, 0];
        const centre = [i + 0.5, j + 0.5, 0];
        // Sens : la face doit monter (z > 0) dans le repere de son parent.
        const sens = applique(rotation(ax, P, 0.3), centre)[2] > 0 ? 1 : -1;
        T[k] = compose(T[p], rotation(ax, P, sens * theta));
      });
      return faces.map(([i, j], k) => [[i, j, 0], [i + 1, j, 0], [i + 1, j + 1, 0], [i, j + 1, 0]].map((q) => applique(T[k], q)));
    };

    // Vue : on tourne la table de 25 degres et on la regarde d'en haut, de biais (50 degres).
    const PHI = (-25 * Math.PI) / 180, ELEV = (50 * Math.PI) / 180;
    const vue = ([x, y, z]) => {
      const xr = x * Math.cos(PHI) - y * Math.sin(PHI), yr = x * Math.sin(PHI) + y * Math.cos(PHI);
      return { X: xr, Y: -(yr * Math.sin(ELEV) + z * Math.cos(ELEV)), prof: yr * Math.cos(ELEV) - z * Math.sin(ELEV) };
    };
    // Cadrage fixe pour un modele (ne bouge pas avec le pliage) : boite englobante de plusieurs pliages.
    let xmin = Infinity, xmax = -Infinity, ymin = Infinity, ymax = -Infinity;
    for (const t of [0, 0.25, 0.5, 0.75, 1]) {
      for (const coins of replie((t * Math.PI) / 2)) for (const q of coins) {
        const v = vue(q);
        xmin = Math.min(xmin, v.X); xmax = Math.max(xmax, v.X); ymin = Math.min(ymin, v.Y); ymax = Math.max(ymax, v.Y);
      }
    }
    const echelle = Math.min(90, 290 / (xmax - xmin), 250 / (ymax - ymin));
    const ox = 170 - ((xmin + xmax) / 2) * echelle, oy = 150 - ((ymin + ymax) / 2) * echelle;
    const ecran = (q) => { const v = vue(q); return `${f(ox + v.X * echelle)},${f(oy + v.Y * echelle)}`; };

    // Les faces, de la plus lointaine a la plus proche ; les deux faces en double (modele 3 plie) passent en
    // dernier, par-dessus, pour qu'on les voie meme si elles sont au fond du cube (schema, pas photo).
    const fini = pliage === 10;
    const doublon = modele === 3 && fini ? new Set([4, 5]) : new Set();
    const coins = replie((pliage / 10) * (Math.PI / 2));
    const ordre = coins.map((c, k) => ({ k, prof: c.reduce((s, q) => s + vue(q).prof, 0) / 4 }))
      .sort((a, b) => (doublon.has(a.k) - doublon.has(b.k)) || (b.prof - a.prof));
    for (const { k } of ordre) {
      const rouge = doublon.has(k);
      el("polygon", {
        points: coins[k].map(ecran).join(" "),
        fill: rouge ? "#F6D5DA" : k === 0 ? "#C9D6E8" : "#DCE8F6", "fill-opacity": rouge ? 0.6 : 0.9,
        stroke: rouge ? ROUGE : BLEU, "stroke-width": rouge ? 3 : 2.5, "stroke-linejoin": "round",
      });
    }
    if (modele === 3 && fini) {
      // Le cote reste ouvert : l'emplacement de la face qui manque, en pointilles rouges.
      el("polygon", {
        points: [[1, 0, 0], [2, 0, 0], [2, 0, 1], [1, 0, 1]].map(ecran).join(" "),
        fill: "none", stroke: ROUGE, "stroke-width": 3, "stroke-dasharray": "7 5", "stroke-linejoin": "round",
      });
    }
    const noms = { 1: "modèle 1 : la croix", 2: "modèle 2 : l'escalier", 3: "modèle 3 : six carrés à essayer" };
    el("text", { x: 170, y: 322, "font-size": 15, fill: ENCRE, "text-anchor": "middle", "font-family": "sans-serif" }, noms[modele]);
    if (modele === 3 && fini) {
      // Legende courte de ce qui cloche, dans la couleur des traces rouges.
      el("text", { x: 170, y: 284, "font-size": 13, fill: ROUGE, "text-anchor": "middle", "font-family": "sans-serif" }, "en rouge : 2 faces au même endroit");
      el("text", { x: 170, y: 302, "font-size": 13, fill: ROUGE, "text-anchor": "middle", "font-family": "sans-serif" }, "pointillés : un côté reste ouvert");
    } else {
      el("text", { x: 170, y: 302, "font-size": 13, fill: GRIS, "text-anchor": "middle", "font-family": "sans-serif" }, "face foncée : posée sur la table");
    }
    return { pliage, modele };
  },
};
