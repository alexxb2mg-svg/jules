// Jules - gabarit "force-mot-de-passe" : une rangee de cases (les caracteres du mot de passe) et une jauge du temps
// qu'il faudrait a un ordinateur pour essayer TOUTES les combinaisons, sur une echelle « seconde -> millions d'annees ».
// Curseurs : longueur (4 a 16 caracteres), types (1 = chiffres, 2 = + minuscules, 3 = + majuscules, 4 = + symboles).
//
// Calcul (recalcule, aucune valeur recopiee) : nombre de combinaisons = N^longueur, ou N = signes possibles par case :
// 10 chiffres ; + 26 minuscules = 36 ; + 26 majuscules = 62 ; + 37 caracteres speciaux = 99. Les 37 caracteres speciaux
// sont ceux que compte la CNIL dans son tableau d'equivalence (deliberation n° 2022-100 du 21 juillet 2022, JORF,
// recommandation relative aux mots de passe : 12 caracteres melant majuscules, minuscules, chiffres et 37 caracteres
// speciaux = environ 80 bits d'entropie, le minimum pour un mot de passe utilise seul).
// Duree = combinaisons / 10^10 essais par seconde. Hypothese de vitesse, ordre de grandeur prudent : une seule carte
// graphique recente teste plus de 10^11 empreintes MD5 par seconde (bancs d'essai publies du logiciel hashcat, carte
// RTX 4090) ; un site qui protege bien ses mots de passe ralentit beaucoup l'attaque. La figure n'ecrit que des ordres
// de grandeur en mots (« quelques heures », « des siecles ») et jamais le nombre de combinaisons : revele false.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["force-mot-de-passe"] = {
  dessiner(svg, valeurs) {
    const longueur = Math.min(16, Math.max(4, Math.round(Number(valeurs.longueur ?? 8))));
    const types = Math.min(4, Math.max(1, Math.round(Number(valeurs.types ?? 2))));
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    svg.setAttribute("viewBox", "0 0 340 300");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS
    const ENCRE = "#14243B", GRIS = "#6B7686", BLEU = "#1F4E8C", ROUGE = "#C8102E", VERT = "#2E7D32", ORANGE = "#E07B00";

    // --- Les quatre familles de signes : allumees jusqu'a « types » ---
    const FAMILLES = [
      { etiquette: "0-9", exemple: "7", taille: 10 },
      { etiquette: "a-z", exemple: "k", taille: 26 },
      { etiquette: "A-Z", exemple: "R", taille: 26 },
      { etiquette: "#!?", exemple: "%", taille: 37 },
    ];
    el("text", { x: 10, y: 20, "font-size": 14, fill: ENCRE, "font-weight": "bold" }, "signes utilisés");
    FAMILLES.forEach((f, i) => {
      const actif = i < types;
      const x = 10 + i * 82;
      el("rect", {
        x, y: 30, width: 74, height: 30, rx: 6, fill: actif ? "#E6EEF8" : "#FFFFFF",
        stroke: actif ? BLEU : GRIS, "stroke-width": actif ? 3 : 2, "stroke-dasharray": actif ? "none" : "5 4",
      });
      el("text", {
        x: x + 37, y: 51, "font-size": 15, "text-anchor": "middle", fill: actif ? BLEU : GRIS, "font-weight": "bold",
      }, f.etiquette);
    });

    // --- Le mot de passe : une case par caractere, un exemple de signe de chaque famille utilisee a tour de role ---
    el("text", { x: 10, y: 92, "font-size": 14, fill: ENCRE, "font-weight": "bold" }, `${longueur} caractères`);
    const largeur = Math.min(30, 320 / longueur);
    const gauche = 170 - (largeur * longueur) / 2;
    for (let i = 0; i < longueur; i++) {
      const f = FAMILLES[(i * 5 + 1) % types]; // chaque famille utilisee revient a tour de role
      el("rect", {
        x: gauche + i * largeur + 1, y: 102, width: largeur - 2, height: 32, rx: 4,
        fill: "#FFFFFF", stroke: BLEU, "stroke-width": 2,
      });
      el("text", {
        x: gauche + (i + 0.5) * largeur, y: 124, "font-size": 15, "text-anchor": "middle", fill: ENCRE,
      }, f.exemple);
    }

    // --- Jauge : temps pour essayer toutes les combinaisons (echelle logarithmique) ---
    let n = 0;
    for (let i = 0; i < types; i++) n += FAMILLES[i].taille;
    const log10Secondes = longueur * Math.log10(n) - 10; // log10(n^longueur / 1e10)
    const AN = 365.25 * 24 * 3600;
    const log10Ans = log10Secondes - Math.log10(AN);
    // Graduations : 1 s, 1 h, 1 an, 1000 ans, 1 million d'annees (en log10 des secondes).
    const MIN = -1, MAX = Math.log10(AN) + 7; // de 0,1 s a 10 millions d'annees
    const X0 = 20, X1 = 320, YJ = 196;
    const X = (l) => X0 + ((Math.min(MAX, Math.max(MIN, l)) - MIN) / (MAX - MIN)) * (X1 - X0);
    const JOUR = Math.log10(24 * 3600), SIECLE = Math.log10(100 * AN);
    const couleur = log10Secondes < JOUR ? ROUGE : log10Secondes < SIECLE ? ORANGE : VERT;
    el("text", { x: 10, y: 166, "font-size": 14, fill: ENCRE, "font-weight": "bold" }, "temps pour tout essayer");
    // fond en trois zones pales : vite trouve, moyen, solide
    el("rect", { x: X0, y: YJ - 12, width: X(JOUR) - X0, height: 24, fill: "#F8E1E4" });
    el("rect", { x: X(JOUR), y: YJ - 12, width: X(SIECLE) - X(JOUR), height: 24, fill: "#FCEBD6" });
    el("rect", { x: X(SIECLE), y: YJ - 12, width: X1 - X(SIECLE), height: 24, fill: "#E3F1E4" });
    el("rect", { x: X0, y: YJ - 12, width: Math.max(4, X(log10Secondes) - X0), height: 24, fill: couleur });
    el("rect", { x: X0, y: YJ - 12, width: X1 - X0, height: 24, fill: "none", stroke: GRIS, "stroke-width": 2 });
    const REPERES = [
      [0, "1 s"], [Math.log10(3600), "1 h"], [Math.log10(AN), "1 an"], [Math.log10(1000 * AN), "1000 ans"],
    ];
    for (const [l, texte] of REPERES) {
      el("line", { x1: X(l), y1: YJ + 12, x2: X(l), y2: YJ + 20, stroke: GRIS, "stroke-width": 2 });
      el("text", { x: X(l), y: YJ + 35, "font-size": 13, "text-anchor": "middle", fill: GRIS }, texte);
    }
    if (log10Secondes > MAX) {
      el("text", { x: X1 - 2, y: YJ + 5, "font-size": 15, "text-anchor": "end", fill: "#FFFFFF", "font-weight": "bold" }, "»");
    }

    // --- Verdict en mots (ordre de grandeur, jamais le nombre) ---
    let duree;
    if (log10Secondes < 0) duree = "moins d'une seconde";
    else if (log10Secondes < Math.log10(60)) duree = "quelques secondes";
    else if (log10Secondes < Math.log10(3600)) duree = "quelques minutes";
    else if (log10Secondes < JOUR) duree = "quelques heures";
    else if (log10Ans < 0) duree = "des jours ou des mois";
    else if (log10Ans < 2) duree = "des années";
    else if (log10Ans < 3) duree = "des siècles";
    else if (log10Ans < 6) duree = "des milliers d'années";
    else if (log10Ans < 9) duree = "des millions d'années";
    else duree = "des milliards d'années";
    const verdict = couleur === ROUGE ? "faible" : couleur === ORANGE ? "moyen" : "solide";
    el("text", { x: 170, y: 262, "font-size": 16, "text-anchor": "middle", fill: couleur, "font-weight": "bold" },
      `${verdict} : ${duree}`);
    el("text", { x: 170, y: 288, "font-size": 13, "text-anchor": "middle", fill: GRIS },
      "à 10 milliards d'essais par seconde");
    return { longueur, types, signes: n, solide: couleur === VERT ? 1 : 0 };
  },
};
