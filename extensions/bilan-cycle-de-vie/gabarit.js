// Jules - gabarit "bilan-cycle-de-vie" : l'impact d'un objet technique, ramene a UNE annee d'usage, etape par
// etape du cycle de vie (une barre par etape), et en dessous les objets fabriques sur 10 ans.
// Curseurs : duree (annees avant la premiere panne, 1 a 10), conso (consommation a l'usage, 1 = tres econome a
// 5 = tres gourmand), repare (0 = remplace a la panne, 1 = repare une fois : l'objet sert deux fois plus
// longtemps), recycle (part de matiere recyclee, 0 a 100 %), transport (distance parcourue, milliers de km).
// MODELE SIMPLIFIE, en « points d'impact » sans unite (aucun nombre n'est ecrit sur la figure) :
//   fabrication (extraction + fabrication) = 60 x (1 - 0,5 x recycle / 100) par objet ;
//   transport = 3 + 1,2 x transport par objet ; fin de vie = 4 par objet ; reparation = 6 (10 % de la fabrication) ;
//   ces impacts « par objet » sont divises par sa duree de vie (duree, ou 2 x duree s'il est repare) ;
//   utilisation = 6 x conso par annee.
// Ordres de grandeur verifies (EX-205) :
// - la fabrication domine l'empreinte des equipements electroniques : etude ADEME-Arcep 2022 (« Evaluation de
//   l'impact environnemental du numerique en France », donnees 2020), la phase de fabrication represente 78 % de
//   l'empreinte carbone du numerique et l'utilisation 21 % ; d'ou, aux valeurs par defaut, fabrication > usage ;
// - un appareil gourmand garde longtemps (refrigerateur, chauffage) a l'inverse un impact domine par l'usage : la
//   figure le montre pour conso >= 4 et duree >= 3 ;
// - la matiere recyclee evite l'extraction : l'aluminium recycle demande environ 95 % d'energie en moins que
//   l'aluminium primaire (International Aluminium Institute, repris par Hydro) ; le modele retient une baisse
//   moderee (la moitie au plus) car la fabrication de l'objet (mise en forme, assemblage) reste a faire ;
// - le transport (phase « distribution ») et la fin de vie se partagent le reste, environ 1 %, dans la meme etude
//   ADEME-Arcep : le modele les garde petits ; la barre transport grossit avec la distance sans jamais depasser
//   la fabrication (au plus 27 points, contre 30 a 60 pour la fabrication).
// - indice de reparabilite : note sur 10 affichee en France depuis le 1er janvier 2021 (loi AGEC du
//   10 fevrier 2020) ; reparer evite une nouvelle fabrication.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["bilan-cycle-de-vie"] = {
  dessiner(svg, valeurs) {
    const borne = (v, d, mini, maxi) => {
      const n = Number(v ?? d);
      return Math.min(maxi, Math.max(mini, Number.isFinite(n) ? n : d));
    };
    const duree = Math.round(borne(valeurs.duree, 3, 1, 10));
    const conso = Math.round(borne(valeurs.conso, 2, 1, 5));
    const repare = Math.round(borne(valeurs.repare, 0, 0, 1));
    const recycle = borne(valeurs.recycle, 0, 0, 100);
    const transport = borne(valeurs.transport, 2, 0, 20);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    svg.setAttribute("viewBox", "0 0 340 340");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", ROUGE = "#C8102E", VERT = "#2E7D32", ORANGE = "#E07B00";

    // --- Modele (points d'impact par annee d'usage) ---
    const vie = duree * (repare ? 2 : 1);
    const fab = 60 * (1 - (0.5 * recycle) / 100);
    const parAn = {
      fabrication: (fab + (repare ? 6 : 0)) / vie,
      transport: (3 + 1.2 * transport) / vie,
      utilisation: 6 * conso,
      fin: 4 / vie,
    };

    // --- Une barre par etape, meme echelle (60 points par an = toute la largeur) ---
    el("text", { x: 10, y: 20, "font-size": 14, fill: ENCRE, "font-weight": "bold" }, "impact par année d'usage");
    const X0 = 112, LMAX = 218, ECHELLE = LMAX / 60;
    const etapes = [
      ["fabrication", "fabrication", BLEU],
      ["transport", "transport", ORANGE],
      ["utilisation", "utilisation", ROUGE],
      ["fin", "fin de vie", GRIS],
    ];
    let plusGros = "fabrication";
    for (const [cle] of etapes) if (parAn[cle] > parAn[plusGros]) plusGros = cle;
    etapes.forEach(([cle, libelle, couleur], i) => {
      const y = 34 + i * 38;
      el("text", { x: 104, y: y + 19, "font-size": 14, "text-anchor": "end", fill: couleur, "font-weight": cle === plusGros ? "bold" : "normal" }, libelle);
      el("line", { x1: X0, y1: y - 2, x2: X0, y2: y + 28, stroke: GRIS, "stroke-width": 2 });
      const l = Math.max(3, Math.min(LMAX, parAn[cle] * ECHELLE));
      el("rect", { x: X0, y, width: l, height: 26, rx: 3, fill: couleur });
      if (parAn[cle] * ECHELLE > LMAX) {
        // au-dela de l'echelle (fabrication d'un objet garde 1 an seulement) : fleche de depassement
        el("path", { d: `M${X0 + LMAX + 2},${y} l8,13 l-8,13 z`, fill: couleur });
      }
    });

    // --- Frise des 10 ans : un bloc par objet fabrique, une cle verte a chaque reparation ---
    const FX = 20, FL = 300, PAS = FL / 10, FY = 214;
    el("text", { x: 10, y: 200, "font-size": 14, fill: ENCRE, "font-weight": "bold" }, "sur 10 ans : les objets fabriqués");
    let nObjets = 0;
    for (let debut = 0; debut < 10; debut += vie) {
      nObjets += 1;
      const fin = Math.min(10, debut + vie);
      el("rect", {
        x: FX + debut * PAS + 2, y: FY, width: (fin - debut) * PAS - 4, height: 30, rx: 6,
        fill: "#E4ECF6", stroke: BLEU, "stroke-width": 2,
      });
      // pastille « neuf » au debut de chaque objet
      el("rect", { x: FX + debut * PAS + 6, y: FY + 7, width: 16, height: 16, rx: 3, fill: BLEU });
      if (repare && debut + duree < 10) {
        const xr = FX + (debut + duree) * PAS;
        el("circle", { cx: xr, cy: FY + 15, r: 9, fill: "#FFFFFF", stroke: VERT, "stroke-width": 3 });
        el("line", { x1: xr - 4, y1: FY + 15, x2: xr + 4, y2: FY + 15, stroke: VERT, "stroke-width": 3 });
        el("line", { x1: xr, y1: FY + 11, x2: xr, y2: FY + 19, stroke: VERT, "stroke-width": 3 });
      }
    }
    // axe des annees
    el("line", { x1: FX, y1: FY + 40, x2: FX + FL, y2: FY + 40, stroke: GRIS, "stroke-width": 2 });
    for (let a = 0; a <= 10; a += 1) {
      el("line", { x1: FX + a * PAS, y1: FY + 36, x2: FX + a * PAS, y2: FY + 44, stroke: GRIS, "stroke-width": 2 });
    }
    el("text", { x: FX, y: FY + 60, "font-size": 13, "text-anchor": "middle", fill: GRIS }, "0");
    el("text", { x: FX + 5 * PAS, y: FY + 60, "font-size": 13, "text-anchor": "middle", fill: GRIS }, "5 ans");
    el("text", { x: FX + FL, y: FY + 60, "font-size": 13, "text-anchor": "middle", fill: GRIS }, "10");
    // legende
    el("rect", { x: 20, y: 290, width: 14, height: 14, rx: 3, fill: BLEU });
    el("text", { x: 40, y: 302, "font-size": 13, fill: BLEU }, "objet neuf");
    if (repare) {
      el("circle", { cx: 150, cy: 297, r: 8, fill: "#FFFFFF", stroke: VERT, "stroke-width": 3 });
      el("text", { x: 164, y: 302, "font-size": 13, fill: VERT }, "réparation");
    }
    el("text", { x: 10, y: 330, "font-size": 13, fill: GRIS }, "modèle simplifié, sans unité");
    return { fabrication: parAn.fabrication, transport: parAn.transport, utilisation: parAn.utilisation, fin: parAn.fin, objets: nObjets };
  },
};
