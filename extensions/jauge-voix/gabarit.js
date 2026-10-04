// Jules - gabarit "jauge-voix" : regler sa voix pour etre compris. Deux jauges verticales (volume de 1 a 5, debit
// en mots par minute) avec une zone verte « on comprend », le public (un camarade, un petit groupe, toute la classe)
// et une phrase en blocs-mots dont les pauses s'elargissent a la ponctuation.
// Curseurs : volume (1 chuchoter a 5 crier), debit (60 a 180 mots/min), pauses (0 aucune, 1 aux points, 2 aux
// virgules et aux points), public (1 un camarade, 2 un petit groupe, 3 toute la classe).
//
// Faits (verifies) :
// - Debit : le programme de francais du cycle 3 (arrete du 10-4-2025, BO n° 16 du 17/04/2025, CM1) vise une
//   lecture correcte de « 110 mots par minute en moyenne » ; meme repere dans les reperes annuels de progression
//   Eduscol (CE2 90, CM1 110, CM2 120 mots correctement lus par minute). Zone verte retenue : 90 a 130 mots/min
//   (110 plus ou moins 20, soit du repere de CE2 a un peu plus que celui de CM2) : repere de lecture choisi pour
//   la figure, pas une norme officielle.
// - Volume : echelle de voix en 5 niveaux, pratique de classe repandue (« niveaux de voix » : chuchoter, parler a
//   un camarade, parler en groupe, parler a toute la classe, crier), pas un texte officiel. Zone verte selon le
//   public : un camarade 1-2, un petit groupe 2-3, toute la classe 3-4 ; crier (5) n'est jamais adapte en classe.
//   Le programme de cycle 3 (CM1, « Lire à voix haute avec expressivité ») demande de « Gérer l'intensité de sa
//   voix (volume, débit) ».
// Aucune valeur calculee ecrite : revele false.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["jauge-voix"] = {
  dessiner(svg, valeurs) {
    const NS = "http://www.w3.org/2000/svg";
    // Police explicite (comme chaine-accords) : la largeur des mots est mesuree tout de suite avec la police
    // reellement affichee ; sans elle, les traits de pause se decalent quand la police de la page arrive apres.
    const POLICE = "system-ui, Arial, sans-serif";
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", VERT = "#2E7D32", ORANGE = "#E07B00";
    const borne = (v, min, max, d) => {
      const n = Number(v);
      return Number.isFinite(n) ? Math.min(max, Math.max(min, n)) : d;
    };
    const volume = Math.round(borne(valeurs.volume, 1, 5, 3));
    const debit = borne(valeurs.debit, 60, 180, 110);
    const pauses = Math.round(borne(valeurs.pauses, 0, 2, 2));
    const public_ = Math.round(borne(valeurs.public, 1, 3, 3));
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (nom === "text") e.setAttribute("font-family", POLICE);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const ZONE_VOLUME = { 1: [1, 2], 2: [2, 3], 3: [3, 4] }[public_];
    const volumeOk = volume >= ZONE_VOLUME[0] && volume <= ZONE_VOLUME[1];
    const debitOk = debit >= 90 && debit <= 130;
    const pausesOk = pauses >= 1; // sans aucune pause, les phrases se melangent : jamais « on te comprend »
    const toutOk = volumeOk && debitOk && pausesOk;

    svg.setAttribute("viewBox", "0 0 340 320");
    svg.replaceChildren(); // vide le SVG ; tous les elements sont crees via createElementNS
    el("text", { x: 170, y: 24, "font-size": 17, "font-weight": "bold", "text-anchor": "middle", fill: toutOk ? VERT : ORANGE },
      toutOk ? "on te comprend" : volumeOk && debitOk ? "respire à la ponctuation" : "règle ta voix");

    const BAS = 220, HAUT = 70;
    // Jauge du volume : 5 cases empilees, zone verte selon le public.
    el("text", { x: 55, y: 56, "font-size": 14, "text-anchor": "middle", fill: ENCRE }, "volume");
    const H = (BAS - HAUT) / 5;
    for (let n = 1; n <= 5; n++) {
      const y = BAS - n * H;
      const dansZone = n >= ZONE_VOLUME[0] && n <= ZONE_VOLUME[1];
      el("rect", { x: 40, y, width: 30, height: H, fill: n <= volume ? (volumeOk ? VERT : ORANGE) : dansZone ? VERT : "#FFFFFF",
        "fill-opacity": n <= volume ? 1 : dansZone ? 0.2 : 1, stroke: ENCRE, "stroke-width": 2 });
    }
    el("text", { x: 76, y: HAUT + 18, "font-size": 13, fill: GRIS }, "crier");
    el("text", { x: 76, y: BAS - 9, "font-size": 13, fill: GRIS }, "chuchoter");
    el("text", { x: 55, y: 244, "font-size": 14, "text-anchor": "middle", fill: volumeOk ? VERT : ORANGE },
      volumeOk ? "bien" : volume < ZONE_VOLUME[0] ? "trop bas" : "trop fort");

    // Jauge du debit : 60 a 180 mots par minute, zone verte 90 a 130.
    const Y = (d) => BAS - ((d - 60) * (BAS - HAUT)) / 120;
    el("text", { x: 175, y: 56, "font-size": 14, "text-anchor": "middle", fill: ENCRE }, "débit");
    el("rect", { x: 160, y: Y(130), width: 30, height: Y(90) - Y(130), fill: VERT, "fill-opacity": 0.2 });
    el("rect", { x: 163, y: Y(debit), width: 24, height: BAS - Y(debit), fill: debitOk ? VERT : ORANGE });
    el("rect", { x: 160, y: HAUT, width: 30, height: BAS - HAUT, fill: "none", stroke: ENCRE, "stroke-width": 2 });
    for (const d of [60, 120, 180]) {
      el("line", { x1: 190, y1: Y(d), x2: 197, y2: Y(d), stroke: ENCRE, "stroke-width": 2 });
      el("text", { x: 200, y: Y(d) + 5, "font-size": 13, fill: GRIS }, String(d));
    }
    el("text", { x: 175, y: 244, "font-size": 14, "text-anchor": "middle", fill: debitOk ? VERT : ORANGE },
      debitOk ? "bien" : debit < 90 ? "trop lent" : "trop vite");
    el("text", { x: 175, y: 260, "font-size": 13, "text-anchor": "middle", fill: GRIS }, "mots/min");

    // Public : 1, 4 ou 12 tetes.
    el("text", { x: 290, y: 56, "font-size": 14, "text-anchor": "middle", fill: ENCRE }, "public");
    const tetes = { 1: 1, 2: 4, 3: 12 }[public_];
    for (let i = 0; i < tetes; i++) {
      const col = tetes === 1 ? 0 : i % (tetes === 4 ? 2 : 3);
      const lig = tetes === 1 ? 0 : Math.floor(i / (tetes === 4 ? 2 : 3));
      const cx = tetes === 1 ? 290 : tetes === 4 ? 274 + col * 32 : 266 + col * 24;
      const cy = tetes === 1 ? 130 : tetes === 4 ? 105 + lig * 50 : 88 + lig * 36;
      el("circle", { cx, cy, r: 7, fill: GRIS });
      el("path", { d: `M${cx - 10},${cy + 20} Q${cx},${cy + 4} ${cx + 10},${cy + 20} Z`, fill: GRIS });
    }
    el("text", { x: 290, y: 244, "font-size": 13, "text-anchor": "middle", fill: GRIS },
      { 1: "un camarade", 2: "un groupe", 3: "la classe" }[public_]);

    // Phrase en blocs-mots : les pauses s'elargissent a la virgule (|) et au point (||).
    const MOTS = [["Le", 0], ["loup", 0], ["arrive,", 1], ["il", 0], ["a", 0], ["faim.", 2], ["Vite !", 0]];
    const textes = MOTS.map(([mot]) => el("text", { x: 0, y: 298, "font-size": 15, fill: ENCRE }, mot));
    const largeurs = textes.map((t, i) => {
      let w = 0;
      try { w = t.getComputedTextLength(); } catch (e) { w = 0; }
      return w > 0 ? w : MOTS[i][0].length * 8; // estimation si le SVG n'est pas encore affiche
    });
    const ecart = (signe) => 7 + (signe === 1 && pauses >= 2 ? 16 : 0) + (signe === 2 && pauses >= 1 ? 26 : 0);
    const total = largeurs.reduce((s, w) => s + w, 0) + MOTS.slice(0, -1).reduce((s, [, signe]) => s + ecart(signe), 0);
    let x = Math.max(4, (340 - total) / 2);
    MOTS.forEach(([, signe], i) => {
      textes[i].setAttribute("x", x.toFixed(1));
      x += largeurs[i];
      if (i < MOTS.length - 1) {
        const e = ecart(signe);
        const marques = signe === 2 && pauses >= 1 ? 2 : signe === 1 && pauses >= 2 ? 1 : 0;
        for (let m = 0; m < marques; m++) {
          const xm = x + e / 2 + (marques === 2 ? (m ? 4 : -4) : 0);
          el("line", { x1: xm, y1: 282, x2: xm, y2: 302, stroke: BLEU, "stroke-width": 3 });
        }
        x += e;
      }
    });
    return { volume, debit, pauses, public: public_ };
  },
};
