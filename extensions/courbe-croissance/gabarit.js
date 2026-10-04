// Jules - gabarit "courbe-croissance" : deux courbes de taille selon l'age (8 a 18 ans) pour deux enfants A et B.
// A commence sa poussee de croissance (puberte) a 10 ans, B « ecart » annees plus tard ; un trait vertical suit
// l'age regarde, un point sur chaque courbe et une ligne d'etat disent ou en est chacun. Valeurs :
//   age   8..18 : age regarde (ans) ;
//   ecart 0..4  : annees entre le debut de la poussee de A et celui de B.
// Modele SIMPLIFIE (pas une courbe reelle d'enfant) : A mesure 128 cm a 8 ans ; avant la poussee, 5 cm par an
// jusqu'a 10 ans puis 4 cm par an (ralentissement juste avant une poussee tardive) ; a partir du debut de la
// poussee, gains annuels 7, 8, 6, 3, 1 cm, puis plus rien (taille adulte). B, dont la puberte arrive plus tard,
// est un peu plus petit dans l'enfance (3 cm de moins par annee d'ecart a 8 ans, comme dans le retard pubertaire
// simple ou l'enfant suit un couloir plus bas). A finit a 163 cm a 15 ans, B arrive a 163 + ecart cm (au plus
// 166 cm a 18 ans) : partir tot ou tard change le MOMENT de la poussee, presque pas la taille d'arrivee.
// (Un modele sans ralentissement ni depart plus bas donnait 182 cm a B pour ecart 4 : faux message.)
// Ordres de grandeur verifies (04/10/2026) :
//   - quand la puberte tarde, la vitesse reste celle de l'enfance et ralentit juste avant la poussee ; l'enfant
//     est souvent plus petit que ses camarades pendant l'enfance mais sa taille finale est normale. Sources :
//     SFD, JNDES 2015, « Conduite a tenir devant un retard de croissance staturale » (d'apres Karlberg) ;
//     Manuel MSD (edition professionnelle), « Retard pubertaire » (retard pubertaire constitutionnel).
//   - avant la puberte, environ 5 cm par an ; pic de la poussee pubertaire vers 8 cm par an chez la fille (6 a 11),
//     environ 23 cm gagnes pendant la puberte, taille finale moyenne d'une femme en France 163 cm vers 16 ans.
//     Sources : association Grandir, « Croissance normale » (grandir.asso.fr/page/1266489-croissance-normale) ;
//     Manuel MSD (Merck), « Croissance physique et maturation sexuelle des adolescents » (poussee des filles entre
//     9,5 et 13,5 ans, jusqu'a 9 cm l'annee du pic) ; courbes AFPA-CRESS/Inserm 2018 du carnet de sante.
//   - debut de la puberte entre 8 et 13 ans chez les filles, 9 et 14 ans chez les garcons (Naitre et grandir,
//     « La puberte precoce » ; Manuel MSD) : ecart 0..3 (debut a 10..13 ans) reste dans la fourchette des
//     filles ; ecart 4 (debut a 14 ans) n'est dans la variation normale que pour un garcon. Les enfants A et B
//     ne sont pas sexues dans la figure ; les tailles d'arrivee (163..166 cm) restent des ordres de grandeur.
//   - lectures de la fiche : a 17 ans et plus, A a fini (gains nuls apres 15 ans) mais B grandit encore entre 17
//     et 18 ans : 1 cm pour ecart 3, 3 cm pour ecart 4 (etat « ralentit ») ; la lecture « age >= 17 » le dit.
// Aucune reponse d'exercice n'est ecrite (les exercices de la fiche utilisent d'autres mesures) : revele false.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["courbe-croissance"] = {
  dessiner(svg, valeurs) {
    const borne = (x, a, b, d) => {
      const n = Math.round(Number(x ?? d));
      return Number.isFinite(n) ? Math.min(b, Math.max(a, n)) : d;
    };
    const age = borne(valeurs.age, 8, 18, 11);
    const ecart = borne(valeurs.ecart, 0, 4, 3);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const c in attrs) e.setAttribute(c, attrs[c]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const ENCRE = "#14243B", BLEU = "#1F4E8C", VERT = "#2E7D32", GRIS = "#6B7686";

    const GAINS = [7, 8, 6, 3, 1]; // cm par an a partir du debut de la poussee
    const tailles = (debut) => {
      const t = [128 - 3 * (debut - 10)];
      for (let a = 8; a < 18; a++) {
        const p = a - debut;
        t.push(t[t.length - 1] + (p < 0 ? (a < 10 ? 5 : 4) : p < GAINS.length ? GAINS[p] : 0));
      }
      return t; // t[i] = taille a 8 + i ans
    };
    const etat = (debut) => {
      const p = age - debut;
      return p < 0 ? "grandit doucement" : p <= 2 ? "poussée !" : p <= 4 ? "ralentit" : "taille adulte";
    };
    const enfants = [
      { lettre: "A", debut: 10, couleur: BLEU, tirets: "" },
      { lettre: "B", debut: 10 + ecart, couleur: VERT, tirets: "9 6" },
    ];

    svg.setAttribute("viewBox", "0 0 340 310");
    svg.replaceChildren(); // vide le SVG ; tous les elements sont crees via createElementNS

    const X0 = 52, PX = 27, Y0 = 268, PY = 2.8; // 8 ans -> x = 52 ; 110 cm -> y = 268 ; 180 cm -> y = 72
    const X = (a) => X0 + (a - 8) * PX;
    const Y = (cm) => Y0 - (cm - 110) * PY;

    // Etat de chacun a l'age regarde (une ligne par enfant, a sa couleur).
    enfants.forEach((e, i) => {
      el("text", { x: 14, y: 22 + i * 20, "font-size": 15, "font-weight": "bold", fill: e.couleur }, `${e.lettre} : ${etat(e.debut)}`);
    });
    el("text", { x: 326, y: 22, "font-size": 15, "text-anchor": "end", fill: ENCRE }, `${age} ans`);

    // Axes et graduations.
    el("line", { x1: X0, y1: Y0, x2: X(18) + 4, y2: Y0, stroke: GRIS, "stroke-width": 2 });
    el("line", { x1: X0, y1: Y0, x2: X0, y2: Y(180), stroke: GRIS, "stroke-width": 2 });
    for (let a = 8; a <= 18; a++) {
      el("line", { x1: X(a), y1: Y0, x2: X(a), y2: Y0 + (a % 2 === 0 ? 7 : 4), stroke: GRIS, "stroke-width": 2 });
      if (a % 2 === 0) el("text", { x: X(a), y: Y0 + 22, "font-size": 13, "text-anchor": "middle", fill: ENCRE }, String(a));
    }
    el("text", { x: X(18), y: Y0 + 38, "font-size": 13, "text-anchor": "end", fill: GRIS }, "âge (ans)");
    for (const cm of [120, 140, 160]) {
      el("line", { x1: X0 - 5, y1: Y(cm), x2: X(18), y2: Y(cm), stroke: "#E3E7ED", "stroke-width": 1 });
      el("text", { x: X0 - 8, y: Y(cm) + 5, "font-size": 13, "text-anchor": "end", fill: ENCRE }, String(cm));
    }
    el("text", { x: X0 + 4, y: Y(180) + 4, "font-size": 13, fill: GRIS }, "taille (cm)");

    // Trait de l'age regarde.
    el("line", { x1: X(age), y1: Y0, x2: X(age), y2: Y(180) + 10, stroke: GRIS, "stroke-width": 2, "stroke-dasharray": "4 4" });

    // Courbes : trait fin, plus epais pendant la poussee (trois annees a 6 cm ou plus).
    for (const e of enfants) {
      const t = tailles(e.debut);
      const pts = t.map((cm, i) => `${X(8 + i)},${Y(cm).toFixed(1)}`);
      el("polyline", { points: pts.join(" "), fill: "none", stroke: e.couleur, "stroke-width": 2.5, "stroke-dasharray": e.tirets, "stroke-linejoin": "round" });
      const d0 = e.debut - 8;
      if (d0 < 10) {
        const fin = Math.min(10, d0 + 3);
        el("polyline", { points: pts.slice(d0, fin + 1).join(" "), fill: "none", stroke: e.couleur, "stroke-width": 6, "stroke-dasharray": e.tirets, "stroke-linecap": "round", "stroke-linejoin": "round" });
      }
      el("circle", { cx: X(age), cy: Y(t[age - 8]), r: 6, fill: e.couleur, stroke: "#FFFFFF", "stroke-width": 2 });
    }
    // Lettres en bout de courbe (B decalee si les deux fins sont proches).
    const finA = tailles(10)[10], finB = tailles(10 + ecart)[10];
    el("text", { x: X(18) - 4, y: Y(finA) + 20, "font-size": 15, "font-weight": "bold", "text-anchor": "end", fill: BLEU }, "A");
    el("text", { x: X(18) - 4, y: Y(finB) - 10 - (finB - finA < 6 ? 6 : 0), "font-size": 15, "font-weight": "bold", "text-anchor": "end", fill: VERT }, "B");
    return { age, ecart, tailleA: tailles(10)[age - 8], tailleB: tailles(10 + ecart)[age - 8] };
  },
};
