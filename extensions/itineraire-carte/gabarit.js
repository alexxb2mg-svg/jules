// Jules - gabarit "itineraire-carte" : un navire avance sur une carte simplifiee le long d'un itineraire historique.
// « avancee » = part du voyage deja faite, en % du TEMPS du voyage (0 = depart, 100 = arrivee) ; la route parcourue
// est en trait plein, la route a venir en pointille gris. « jeu » (fige par la fiche) choisit l'itineraire :
//   1  Magellan puis Elcano, premier tour du monde (1519-1522). Depart de Sanlucar de Barrameda le 20 septembre
//      1519 ; Rio de Janeiro le 13 decembre 1519 ; hivernage a San Julian (Patagonie) a partir du 31 mars 1520 ;
//      entree du detroit le 21 octobre 1520, sortie dans le Pacifique le 28 novembre 1520 ; iles Mariannes (Guam)
//      le 6 mars 1521 ; Magellan tue a Mactan (Philippines) le 27 avril 1521 ; Moluques (Tidore) du 8 novembre au
//      21 decembre 1521 ; Timor debut 1522 ; cap de Bonne-Esperance passe le 6 mai 1522 ; Cap-Vert le 9 juillet
//      1522 ; retour de la Victoria a Sanlucar le 6 septembre 1522 avec 18 hommes. Navires : quatre naos (caraques)
//      et une caravelle, le Santiago. Source : Wikipedia en anglais, « Magellan expedition » (d'apres L. Bergreen,
//      Over the Edge of the World, 2003, et I. Cameron, Magellan, 1974).
//   2  Christophe Colomb, premier voyage (aller) : Palos le 3 aout 1492, depart de La Gomera (Canaries) le
//      6 septembre, arrivee aux Bahamas (Guanahani) le 12 octobre 1492. Source : Wikipedia en anglais, « Voyages of
//      Christopher Columbus » (d'apres le journal de Colomb et S. E. Morison).
//   3  Commerce triangulaire (XVIIIe siecle, exemple d'un navire nantais) : Nantes -> golfe de Guinee (Ouidah) ->
//      Saint-Domingue (colonie francaise) -> Nantes ; contenu de la cale a chaque trajet : celui de la fiche CM1
//      « cm1-traite-esclaves-plantations » et du programme de CM1 (pas de date ecrite pour ce jeu).
// Les cotes sont tres simplifiees (quelques dizaines de points par continent) : c'est un fond de reperage, pas une
// carte exacte. Projection equirectangulaire (latitudes dilatees pour la carte du monde) ; polygones decoupes au cadre.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["itineraire-carte"] = {
  dessiner(svg, valeurs) {
    const NS = "http://www.w3.org/2000/svg";
    const BLEU = "#1F4E8C", GRIS = "#6B7686", ENCRE = "#14243B", ROUGE = "#C8102E", VERT = "#2E7D32", ORANGE = "#E07B00";
    const MER = "#E3ECF5", TERRE = "#C9BFA5";
    const nombre = (v, d) => (Number.isFinite(Number(v)) ? Number(v) : d);
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };

    // --- continents simplifies : [longitude, latitude] -------------------------------------------------------
    const TERRES = [
      // Amerique du Nord
      [[-166, 68], [-156, 71], [-130, 70], [-110, 68], [-90, 70], [-80, 64], [-78, 58], [-65, 60], [-56, 52], [-60, 46],
        [-70, 43], [-76, 38], [-76, 35], [-81, 31], [-80, 25], [-83, 29], [-90, 30], [-97, 27], [-97, 21], [-90, 21],
        [-87, 21], [-88, 16], [-84, 15], [-83, 10], [-79, 9], [-77, 8], [-80, 7], [-83, 8], [-87, 13], [-92, 15],
        [-96, 16], [-105, 20], [-110, 24], [-112, 30], [-115, 30], [-118, 34], [-124, 40], [-124, 47], [-130, 55],
        [-140, 60], [-150, 60], [-158, 57], [-165, 60]],
      // Groenland
      [[-55, 60], [-44, 60], [-22, 70], [-20, 80], [-62, 80], [-72, 77], [-55, 70]],
      // Cuba et Hispaniola (Saint-Domingue)
      [[-85, 22], [-80, 23], [-74, 20], [-77, 20], [-82, 21.5]],
      [[-74, 19.8], [-69, 19.5], [-68.5, 18.4], [-71.5, 17.8], [-74.4, 18.3]],
      // Amerique du Sud
      [[-77, 9], [-72, 12], [-63, 10], [-55, 6], [-50, 1], [-44, -2], [-35, -5], [-35, -9], [-39, -15], [-41, -22],
        [-48, -26], [-53, -34], [-58, -35], [-57, -38], [-62, -40], [-65, -45], [-68, -50], [-69, -53], [-71, -54],
        [-74, -50], [-74, -44], [-73, -37], [-71, -30], [-70, -18], [-76, -14], [-81, -5], [-80, 0], [-78, 3]],
      // Afrique
      [[-17, 21], [-16, 28], [-10, 30], [-6, 36], [10, 37], [11, 33], [20, 31], [25, 32], [32, 31], [34, 28], [43, 12],
        [51, 12], [48, 5], [40, -3], [40, -10], [35, -20], [33, -26], [28, -33], [20, -35], [18, -32], [12, -17],
        [13, -6], [9, -1], [9, 4], [4, 6], [-5, 5], [-8, 4], [-13, 8], [-17, 14]],
      // Madagascar
      [[49, -12], [50, -16], [47, -25], [44, -24], [44, -17]],
      // Eurasie
      [[-9, 43], [-9, 37], [-6, 36], [-2, 37], [3, 43], [8, 44], [12, 42], [16, 38], [18, 40], [13, 45], [20, 40],
        [23, 37], [26, 40], [28, 41], [36, 36], [34, 28], [39, 22], [43, 13], [52, 16], [57, 22], [58, 24], [50, 30],
        [57, 25], [62, 25], [67, 24], [72, 21], [73, 16], [77, 8], [80, 14], [80, 16], [87, 21], [92, 22], [94, 17],
        [98, 16], [98, 8], [103, 1], [104, 10], [109, 12], [106, 20], [110, 21], [117, 23], [121, 29], [121, 32],
        [118, 38], [122, 40], [126, 37], [129, 35], [130, 43], [140, 48], [141, 53], [135, 55], [143, 59], [156, 51],
        [162, 56], [164, 60], [175, 63], [180, 66], [180, 70], [160, 70], [140, 73], [113, 74], [100, 78], [80, 73],
        [70, 73], [60, 70], [50, 68], [40, 66], [33, 70], [25, 71], [15, 68], [5, 62], [6, 58], [11, 58], [11, 55],
        [8, 55], [8, 54], [4, 52], [2, 51], [-2, 48], [-4, 48], [-1, 46], [-2, 43]],
      // Grande-Bretagne
      [[-5, 50], [1, 51], [2, 53], [-1, 55], [-2, 57], [-5, 58.5], [-6, 56], [-3, 54], [-5, 52]],
      // Borneo, Sumatra, Nouvelle-Guinee, Philippines (reperes pour la route de Magellan)
      [[109, 1], [117, 7], [119, 1], [116, -4], [110, -3]],
      [[95, 5], [104, -2], [106, -6], [101, -3]],
      [[131, -1], [141, -3], [150, -10], [141, -9], [134, -4]],
      [[120, 18], [122, 18], [126, 7], [122, 7], [120, 13]],
      // Australie
      [[114, -22], [122, -18], [130, -12], [137, -12], [142, -11], [146, -19], [153, -25], [150, -37], [141, -38],
        [135, -35], [129, -32], [115, -34]],
    ];

    // --- itineraires : [longitude (deroulee vers l'ouest au-dela de -180), latitude, part du temps] -------------
    // Mois depuis le depart / duree totale (Magellan : 35,5 mois du 20/09/1519 au 06/09/1522).
    const JEUX = {
      1: {
        titre: "Magellan et Elcano, 1519-1522",
        cadre: [-180, 180, 72, -58], etire: 1.6, couleur: BLEU,
        route: [
          [-6.4, 36.8, 0], [-16.3, 28.5, 0.02], [-20, 10, 0.04], [-43.2, -22.9, 0.08], [-57, -35, 0.12],
          [-67.7, -49.3, 0.18], [-67.7, -49.3, 0.30], [-68.4, -52.4, 0.37], [-74.5, -52.5, 0.40], [-80, -35, 0.42],
          [-140, -15, 0.46], [-215.2, 13.4, 0.49], [-236.1, 10.3, 0.54], [-232.6, 0.7, 0.72], [-232.6, 0.7, 0.76],
          [-235.5, -9.5, 0.80], [-280, -30, 0.84], [-341.5, -35, 0.89], [-383.5, 15, 0.95], [-385.7, 37.7, 0.98],
          [-366.4, 36.8, 1],
        ],
        dates: [[0, "septembre 1519"], [0.08, "décembre 1519"], [0.18, "1520"], [0.42, "fin 1520"], [0.49, "mars 1521"],
          [0.54, "avril 1521"], [0.72, "novembre 1521"], [0.80, "début 1522"], [0.89, "mai 1522"], [0.95, "juillet 1522"],
          [1, "septembre 1522"]],
        lieux: [[-6.4, 36.8, "Espagne"], [-236.1, 10.3, "Philippines"]],
        cale: null,
      },
      2: {
        titre: "Christophe Colomb, 1492",
        cadre: [-90, 0, 48, 8], couleur: BLEU,
        route: [[-6.9, 37.2, 0], [-17.1, 28.1, 0.1], [-17.1, 28.1, 0.48], [-45, 27, 0.75], [-74.5, 24.1, 1]],
        dates: [[0, "3 août 1492"], [0.1, "août 1492"], [0.48, "6 septembre 1492"], [1, "12 octobre 1492"]],
        lieux: [[-6.9, 37.2, "Espagne"], [-74.5, 24.1, "Bahamas"]],
        cale: null,
      },
      3: {
        titre: "Le commerce triangulaire",
        cadre: [-95, 25, 56, -22], couleur: ORANGE,
        route: [[-1.6, 47.2, 0], [-10, 40, 0.06], [-20, 18, 0.15], [-18, 7, 0.22], [-6, 3, 0.28], [2.1, 6.4, 1 / 3],
          [-20, 2, 0.45], [-50, 12, 0.56], [-66, 21.5, 0.63], [-72.2, 20.1, 2 / 3], [-60, 33, 0.8], [-25, 45, 0.92],
          [-1.6, 47.2, 1]],
        dates: [],
        lieux: [[-1.6, 47.2, "Europe"], [2.1, 6.4, "Afrique"], [-72.2, 20.1, "Amérique"]],
        cale: [
          [1 / 3, "tissus, armes, alcool"],
          [2 / 3, "captifs africains"],
          [1, "sucre, café, cacao"],
        ],
      },
    };

    const jeu = JEUX[Math.round(nombre(valeurs.jeu, 1))] || JEUX[1];
    const t = Math.min(100, Math.max(0, nombre(valeurs.avancee, 0))) / 100;

    // --- projection --------------------------------------------------------------------------------------------
    const [LO0, LO1, LA0, LA1] = jeu.cadre;
    const ECH = 340 / (LO1 - LO0), ECHY = ECH * (jeu.etire || 1); // etire : latitudes dilatees (carte du monde)
    const YC = 30, HC = (LA0 - LA1) * ECHY; // carte de YC a YC + HC
    const H = Math.min(340, Math.round(YC + HC + (jeu.cale ? 56 : 38)));
    svg.setAttribute("viewBox", `0 0 340 ${H}`);
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS
    const enl = (lon) => ((((lon - LO0) % 360) + 360) % 360) + LO0; // longitude ramenee dans [LO0, LO0 + 360[
    const P = (lon, lat) => [(lon - LO0) * ECH, YC + (LA0 - lat) * ECHY];

    // Decoupe d'un polygone par le cadre (Sutherland-Hodgman), en coordonnees ecran.
    const decouper = (pts) => {
      const bords = [
        [(p) => p[0] >= 0, (a, b) => { const k = (0 - a[0]) / (b[0] - a[0]); return [0, a[1] + k * (b[1] - a[1])]; }],
        [(p) => p[0] <= 340, (a, b) => { const k = (340 - a[0]) / (b[0] - a[0]); return [340, a[1] + k * (b[1] - a[1])]; }],
        [(p) => p[1] >= YC, (a, b) => { const k = (YC - a[1]) / (b[1] - a[1]); return [a[0] + k * (b[0] - a[0]), YC]; }],
        [(p) => p[1] <= YC + HC, (a, b) => { const k = (YC + HC - a[1]) / (b[1] - a[1]); return [a[0] + k * (b[0] - a[0]), YC + HC]; }],
      ];
      let sortie = pts;
      for (const [dedans, coupe] of bords) {
        const entree = sortie;
        sortie = [];
        for (let i = 0; i < entree.length; i++) {
          const a = entree[(i + entree.length - 1) % entree.length], b = entree[i];
          if (dedans(b)) {
            if (!dedans(a)) sortie.push(coupe(a, b));
            sortie.push(b);
          } else if (dedans(a)) sortie.push(coupe(a, b));
        }
        if (!sortie.length) break;
      }
      return sortie;
    };
    const fmt = (pts) => pts.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ");

    el("rect", { x: 0, y: YC, width: 340, height: HC, fill: MER });
    for (const terre of TERRES) {
      const coupe = decouper(terre.map(([lo, la]) => P(lo, la)));
      if (coupe.length >= 3) el("polygon", { points: fmt(coupe), fill: TERRE });
    }
    el("rect", { x: 1, y: YC, width: 338, height: HC, fill: "none", stroke: GRIS, "stroke-width": 2 });
    el("text", { x: 170, y: 20, "font-size": 15, "text-anchor": "middle", fill: ENCRE, "font-weight": 700 }, jeu.titre);

    // Position sur la route au temps u (interpolation entre deux etapes).
    const position = (u) => {
      const r = jeu.route;
      for (let i = 0; i + 1 < r.length; i++) {
        const [lo0, la0, t0] = r[i], [lo1, la1, t1] = r[i + 1];
        if (u <= t1) {
          const k = t1 > t0 ? (u - t0) / (t1 - t0) : 1;
          return [lo0 + k * (lo1 - lo0), la0 + k * (la1 - la0)];
        }
      }
      const fin = r[r.length - 1];
      return [fin[0], fin[1]];
    };
    // Trace d'une portion de route [u0, u1] echantillonnee ; coupee quand elle passe le bord de la carte.
    const tracer = (u0, u1, attrs) => {
      if (u1 <= u0) return;
      const n = Math.max(2, Math.ceil((u1 - u0) * 240));
      let morceau = [];
      let precedent = null;
      const finir = () => { if (morceau.length >= 2) el("polyline", { points: fmt(morceau), fill: "none", ...attrs }); morceau = []; };
      for (let k = 0; k <= n; k++) {
        const [lo, la] = position(u0 + ((u1 - u0) * k) / n);
        const p = P(enl(lo), la);
        if (precedent && Math.abs(p[0] - precedent[0]) > 170) finir();
        morceau.push(p);
        precedent = p;
      }
      finir();
    };
    tracer(t, 1, { stroke: GRIS, "stroke-width": 2, "stroke-dasharray": "4 4" });
    tracer(0, t, { stroke: jeu.couleur, "stroke-width": 3, "stroke-linecap": "round" });

    // Lieux (point et nom).
    for (const [lo, la, nom] of jeu.lieux) {
      const [x, y] = P(enl(lo), la);
      el("circle", { cx: x, cy: y, r: 4, fill: ENCRE });
      const aDroite = x < 250;
      el("text", { x: aDroite ? x + 7 : x - 7, y: y - 6, "font-size": 13, "text-anchor": aDroite ? "start" : "end", fill: ENCRE, "font-weight": 700 }, nom);
    }

    // Navire : coque et voile, a la position du moment.
    const [lo, la] = position(t);
    const [xn, yn] = P(enl(lo), la);
    el("path", { d: `M ${xn - 9} ${yn} L ${xn + 9} ${yn} L ${xn + 5} ${yn + 6} L ${xn - 5} ${yn + 6} Z`, fill: ROUGE });
    el("path", { d: `M ${xn} ${yn - 13} L ${xn} ${yn - 1} L ${xn + 8} ${yn - 1} Z`, fill: "#FFFFFF", stroke: ROUGE, "stroke-width": 2 }).setAttribute("data-adresse", "graphe/navire");

    // Sous la carte : date du moment (jeux 1 et 2) ou contenu de la cale (jeu 3).
    const yb = YC + HC + 24;
    if (jeu.cale) {
      const [, contenu] = jeu.cale.find(([fin]) => t <= fin + 1e-9) || jeu.cale[jeu.cale.length - 1];
      const etape = t < 1 / 3 ? 0 : t < 2 / 3 ? 1 : 2;
      const COUL = [GRIS, ROUGE, VERT];
      el("rect", { x: 8, y: yb - 17, width: 324, height: 40, rx: 6, fill: "#FFFFFF", stroke: COUL[etape], "stroke-width": 3 });
      el("text", { x: 18, y: yb + 1, "font-size": 13, fill: GRIS }, "Dans la cale :");
      el("text", { x: 108, y: yb + 1, "font-size": 15, fill: COUL[etape], "font-weight": 700 }, contenu);
    } else {
      let date = jeu.dates[0][1];
      for (const [u, d] of jeu.dates) if (t >= u - 1e-9) date = d;
      el("text", { x: 170, y: yb, "font-size": 15, "text-anchor": "middle", fill: jeu.couleur, "font-weight": 700 }, date);
    }
    return { avancee: Math.round(t * 100), longitude: Math.round(enl(lo)), latitude: Math.round(la) };
  },
};
