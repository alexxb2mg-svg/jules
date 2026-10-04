// Jules - gabarit "courbe-evolution" : une ou plusieurs courbes qui se dessinent quand on avance l'annee.
// Le jeu de donnees est choisi par le curseur « jeu » (fige par la fiche), seul « annee » est manipule par l'eleve.
// La partie de la courbe apres l'annee choisie n'est pas dessinee ; la valeur ecrite dans la legende est celle du
// dernier point connu (avec son annee), jamais une valeur inventee entre deux points.
//
// Jeux et sources (verifiees le 04/10/2026 ; aucune adresse web complete dans ce fichier, regle du depot) :
//   1  Allemagne 1928-1933 : chomeurs inscrits en JANVIER de chaque annee, en millions (P. Longerich, Deutschland
//      1918-1933, 1995, cite par l'article « Weimarer Republik » de Wikipedia en allemand : 2,85 en 1929,
//      plus de 3,2 en 1930, pres de 4,9 en 1931, plus de 6 en 1932 ; « plus de 6 millions debut 1933 » : Deutsches
//      Historisches Museum, LeMO « Weltwirtschaftskrise ») ; pas de point en 1928 (valeur de janvier non sourcee).
//      Vote NSDAP aux elections au Reichstag (Bundestag, « Reichstagswahlergebnisse 1919-1933 », d'apres J. Falter :
//      2,6 % en mai 1928, 18,3 % en septembre 1930, 37,4 % en juillet 1932, 43,9 % en mars 1933 ; l'election de
//      novembre 1932, 33,1 %, n'est pas tracee pour garder une courbe lisible).
//   2  Nombre d'Etats membres de l'ONU, 1945-1975 : un.org, « Growth in United Nations membership » (51 en 1945,
//      82 en 1957, 99 en 1960, 144 en 1975 ; annees sans admission = valeur de l'annee precedente).
//   3  France, taux de chomage 1950-1990 : Insee, « L'essentiel sur le chomage » (BIT, 1975-1990) ; avant 1975 pas de
//      serie BIT : estimation « moins de 2 % au debut des annees soixante » (Insee Premiere 1312, 2010), tracee en
//      pointille a 2 %, et environ 2 % en 1973 (Lumni, « l'essor du chomage entre 1973 et 1975 »).
//   4  France, part des femmes dans la population active (recensements 1954-1990) : Insee, M. Maruani et M. Meron,
//      « Un siecle de travail des femmes en France » (34,3 % en 1954 ... 43,7 % en 1990).
//   5  France metropolitaine, part des 65 ans ou plus au 1er janvier : Insee, estimations de population, reprises
//      par l'article « Demographie de la France » de Wikipedia (11,4 % en 1950, 11,6 % en 1960, 12,8 % en 1970,
//      14,0 % en 1980, 13,9 % en 1990) ; 13,9 % en 1990 confirme par l'Observatoire des territoires (« Le
//      vieillissement de la population et ses enjeux ») ; coherent avec Insee, Tableaux de l'economie francaise,
//      « Population par age » (60 ans ou plus : 16,2 % en 1950, 19,0 % en 1990).
//   6  France, part de l'emploi par secteur (en %, arrondis) : debut des annees 1950, Insee (Bouvier et Pilarski,
//      Insee Premiere 1201, cite par « La tertiarisation de l'economie francaise », 2011 : agriculture 29 %,
//      industrie 25 %, services marchands 25 %, non marchands 15 % ; la construction, non citee, est prise comme le
//      reste, environ 6 %) ; 1962 recensement (19,9 / 38,2 / 41,9, Deuframat, « L'evolution de l'emploi ») ; 1975-2002 Insee,
//      series longues (« L'emploi en France depuis trente ans ») ; 2018 Insee, Tableaux de l'economie francaise
//      (2,5 / 13,3 + 6,7 / 76,1). Industrie = industrie et construction.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["courbe-evolution"] = {
  dessiner(svg, valeurs) {
    const NS = "http://www.w3.org/2000/svg";
    const BLEU = "#1F4E8C", GRIS = "#6B7686", ENCRE = "#14243B", ROUGE = "#C8102E", VERT = "#2E7D32", ORANGE = "#E07B00";
    const nombre = (v, d) => (Number.isFinite(Number(v)) ? Number(v) : d);
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const virgule = (v) => String(v).replace(".", ",");

    // pas = estimation (trait pointille) ; chaque point : [annee, valeur] ou [annee, valeur, true] si estime.
    const JEUX = {
      1: {
        titre: "Allemagne, 1928-1933",
        de: 1928, a: 1933, axe: null,
        series: [
          { nom: "chômeurs (janvier)", couleur: ORANGE, max: 7, unite: (v) => `${virgule(v)} millions`,
            points: [[1929, 2.9], [1930, 3.2], [1931, 4.9], [1932, 6], [1933, 6]] },
          { nom: "vote nazi", couleur: BLEU, max: 50, unite: (v) => `${virgule(v)} %`,
            points: [[1928, 2.6], [1930, 18.3], [1932, 37.4], [1933, 43.9]] },
        ],
        repere: [1929.8, "krach de 1929"],
      },
      2: {
        titre: "États membres de l'ONU",
        de: 1945, a: 1975, axe: { max: 160, pas: 40 },
        series: [
          { nom: "États membres", couleur: BLEU, unite: (v) => `${v} États`,
            points: [[1945, 51], [1946, 55], [1947, 57], [1948, 58], [1949, 59], [1950, 60], [1954, 60], [1955, 76],
              [1956, 80], [1957, 82], [1959, 82], [1960, 99], [1961, 104], [1962, 110], [1963, 113], [1964, 115],
              [1965, 117], [1966, 122], [1967, 123], [1968, 126], [1969, 126], [1970, 127], [1971, 132], [1972, 132],
              [1973, 135], [1974, 138], [1975, 144]] },
        ],
        repere: [1960, "année de l'Afrique"],
      },
      3: {
        titre: "France : chômeurs sur 100 actifs",
        de: 1950, a: 1990, axe: { max: 12, pas: 3 },
        series: [
          { nom: "chômage", couleur: ROUGE, unite: (v) => `${virgule(v)} %`,
            points: [[1950, 2, true], [1960, 2, true], [1973, 2, true], [1975, 3.6], [1976, 4.0], [1977, 4.5],
              [1978, 4.7], [1979, 5.3], [1980, 5.6], [1981, 6.6], [1982, 7.1], [1983, 7.4], [1984, 8.7], [1985, 9.1],
              [1986, 9.1], [1987, 9.2], [1988, 8.9], [1989, 8.2], [1990, 8.0]] },
        ],
        repere: [1973, "choc pétrolier"],
      },
      4: {
        titre: "France : femmes sur 100 actifs",
        de: 1950, a: 1990, axe: { max: 50, pas: 10 },
        series: [
          { nom: "part des femmes", couleur: VERT, unite: (v) => `${virgule(v)} %`,
            points: [[1954, 34.3], [1962, 33.4], [1968, 34.5], [1975, 37.1], [1982, 40.3], [1990, 43.7]] },
        ],
        repere: [1975, "loi Veil"],
      },
      5: {
        titre: "France : 65 ans ou plus sur 100 habitants",
        de: 1950, a: 1990, axe: { max: 20, pas: 5 },
        series: [
          { nom: "65 ans ou plus", couleur: ORANGE, unite: (v) => `${virgule(v)} %`,
            points: [[1950, 11.4], [1960, 11.6], [1970, 12.8], [1980, 14.0], [1990, 13.9]] },
        ],
        repere: null,
      },
      6: {
        titre: "France : emplois sur 100, par secteur",
        de: 1950, a: 2020, axe: { max: 80, pas: 20 },
        series: [
          { nom: "agriculture", couleur: VERT, unite: (v) => `${virgule(v)} %`,
            points: [[1950, 29], [1962, 20], [1975, 10], [1984, 7], [1993, 5], [2002, 4], [2018, 2.5]] },
          { nom: "industrie", couleur: ORANGE, unite: (v) => `${virgule(v)} %`,
            points: [[1950, 31], [1962, 38], [1975, 37], [1984, 32], [1993, 27], [2002, 23], [2018, 20]] },
          { nom: "services", couleur: BLEU, unite: (v) => `${virgule(v)} %`,
            points: [[1950, 40], [1962, 42], [1975, 53], [1984, 61], [1993, 68], [2002, 73], [2018, 76]] },
        ],
        repere: [1973, "choc pétrolier"],
      },
    };

    const jeu = JEUX[Math.round(nombre(valeurs.jeu, 1))] || JEUX[1];
    const annee = Math.min(jeu.a, Math.max(jeu.de, nombre(valeurs.annee, jeu.de)));

    // --- mise en page ----------------------------------------------------------------------------------------
    const XG = jeu.axe ? 50 : 22, XD = 318, YH = 50, YB = 200; // zone du trace
    const lignesLegende = jeu.series.length + (jeu.axe ? 0 : 1);
    const H = Math.min(340, 246 + 22 * lignesLegende);
    svg.setAttribute("viewBox", `0 0 340 ${H}`);
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS
    const X = (an) => XG + ((an - jeu.de) / (jeu.a - jeu.de)) * (XD - XG);
    const texte = (x, y, chaine, taille, couleur, gras, ancre) => {
      let cx = x;
      if (!ancre || ancre === "middle") {
        const demi = (chaine.length * taille * 0.56) / 2;
        cx = Math.min(340 - 4 - demi, Math.max(4 + demi, x));
      }
      return el("text", { x: cx, y, "font-size": taille, "text-anchor": ancre || "middle", fill: couleur, "font-weight": gras ? 700 : 400 }, chaine);
    };

    texte(170, 22, jeu.titre, 15, ENCRE, true);

    // Axe vertical gradue (echelle commune) ou simple ligne de base (une echelle par courbe).
    if (jeu.axe) {
      for (let v = 0; v <= jeu.axe.max; v += jeu.axe.pas) {
        const y = YB - (v / jeu.axe.max) * (YB - YH);
        el("line", { x1: XG, y1: y, x2: XD, y2: y, stroke: "#D5DAE1", "stroke-width": v === 0 ? 2 : 1 });
        texte(XG - 6, y + 5, String(v), 13, GRIS, false, "end");
      }
    }
    el("line", { x1: XG, y1: YB, x2: XD, y2: YB, stroke: GRIS, "stroke-width": 2 });

    // Graduations des annees : bornes + pas rond, etiquettes sans chevauchement.
    const ecart = jeu.a - jeu.de;
    const pasAn = [1, 2, 5, 10, 20].find((s) => ecart / s <= 7) || 10;
    for (let an = Math.ceil(jeu.de / pasAn) * pasAn; an <= jeu.a; an += pasAn) {
      el("line", { x1: X(an), y1: YB, x2: X(an), y2: YB + 6, stroke: GRIS, "stroke-width": 2 });
      texte(X(an), YB + 22, String(an), 13, GRIS, false);
    }

    // Repere historique (trait orange discret, nomme quand l'annee choisie l'a depasse).
    if (jeu.repere && annee >= jeu.repere[0]) {
      const xr = X(jeu.repere[0]);
      el("line", { x1: xr, y1: YH - 6, x2: xr, y2: YB, stroke: ORANGE, "stroke-width": 2, "stroke-dasharray": "3 4" });
      texte(xr, YH - 10, jeu.repere[1], 13, ORANGE, true);
    }

    // Annee choisie : trait vertical.
    const xa = X(annee);
    el("line", { x1: xa, y1: YH, x2: xa, y2: YB, stroke: ENCRE, "stroke-width": 2, "stroke-dasharray": "6 4", opacity: 0.55 });

    // Courbes : de leur premier point jusqu'a l'annee choisie (interpolation lineaire jusqu'au trait).
    const resultat = {};
    jeu.series.forEach((s, i) => {
      const max = jeu.axe ? jeu.axe.max : s.max;
      const Y = (v) => YB - (Math.min(v, max) / max) * (YB - YH);
      const pts = s.points;
      const traces = []; // segments [x1, y1, x2, y2, estime]
      for (let k = 0; k + 1 < pts.length; k++) {
        const [a0, v0, e0] = pts[k], [a1, v1, e1] = pts[k + 1];
        if (a0 >= annee) break;
        const fin = Math.min(a1, annee);
        const vf = v0 + ((v1 - v0) * (fin - a0)) / (a1 - a0);
        traces.push([X(a0), Y(v0), X(fin), Y(vf), Boolean(e0 && e1)]);
      }
      for (const [x1, y1, x2, y2, est] of traces) {
        el("line", { x1, y1, x2, y2, stroke: s.couleur, "stroke-width": 4, "stroke-linecap": "round", "stroke-dasharray": est ? "7 6" : "none" });
      }
      // Points de donnees deja atteints.
      let dernier = null;
      for (const p of pts) {
        if (p[0] > annee) break;
        dernier = p;
        el("circle", { cx: X(p[0]), cy: Y(p[1]), r: 4, fill: p[2] ? "#FFFFFF" : s.couleur, stroke: s.couleur, "stroke-width": 2 });
      }
      // Legende : couleur, nom, derniere valeur connue (annee entre parentheses si ce n'est pas l'annee choisie).
      const yl = YB + 48 + 22 * i;
      el("line", { x1: 10, y1: yl - 5, x2: 34, y2: yl - 5, stroke: s.couleur, "stroke-width": 4, "stroke-linecap": "round" });
      let lu = "pas encore de donnée";
      if (dernier) {
        lu = dernier[2] ? `environ ${s.unite(dernier[1])} (estimation)` : s.unite(dernier[1]);
        if (dernier[0] !== annee && !dernier[2]) lu += ` (${dernier[0]})`;
      }
      texte(42, yl, `${s.nom} : ${lu}`, 14, ENCRE, false, "start");
      resultat[s.nom] = dernier ? dernier[1] : null;
    });
    if (!jeu.axe) {
      texte(10, YB + 48 + 22 * jeu.series.length, "Chaque courbe a sa propre échelle.", 13, GRIS, false, "start");
    }
    return { annee, ...resultat };
  },
};
