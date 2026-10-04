// Jules - gabarit "aire-attraction" : une aire d'attraction de grande ville vue du dessus (modele simplifie). Au
// centre le pole (ville-centre puis banlieue), autour la couronne, au-dela l'espace hors attraction. Une maison
// s'eloigne du centre (« distance », en km) : le trajet domicile-travail vers le centre s'allonge et la zone
// traversee change de nom. « annee » fait s'etaler la couronne de 1970 a 2020 (periurbanisation).
// Definitions : Insee, zonage en aires d'attraction des villes 2020 (Insee Focus n° 211, 2020) : une aire = un pole
// (population et emploi) + une couronne (communes dont au moins 15 % des actifs travaillent dans le pole) ; 93 % de
// la population vit dans une aire, 51 % dans un pole, 43 % dans une couronne. Le programme de 3e dit encore « aire
// urbaine » (ville-centre, banlieue, espace periurbain).
// Distances : MODELE indicatif d'une grande ville (pas une ville reelle) : ville-centre jusqu'a 5 km, banlieue
// jusqu'a 15 km, couronne jusqu'a 25 km en 1970 et 45 km en 2020 (+4 km par decennie). Ces rayons ne sont pas des
// chiffres Insee : ils servent a faire voir l'ordre des zones et l'etalement, pas a mesurer une ville.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["aire-attraction"] = {
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

    const distance = Math.min(50, Math.max(0, nombre(valeurs.distance, 2)));
    const annee = Math.min(2020, Math.max(1970, nombre(valeurs.annee, 1970)));
    const R_CENTRE = 5, R_BANLIEUE = 15;
    const rCouronne = 25 + ((annee - 1970) / 50) * 20; // 25 km en 1970 -> 45 km en 2020
    const zone = distance < R_CENTRE ? "ville-centre" : distance < R_BANLIEUE ? "banlieue" : distance < rCouronne ? "couronne périurbaine" : "hors de l'aire";

    // --- mise en page : disque de 50 km de rayon (au-dela : bord) -------------------------------------------
    const H = 320;
    svg.setAttribute("viewBox", `0 0 340 ${H}`);
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS
    const CX = 124, CY = 152, ECH = 2.3; // 1 km = 2,3 px ; 52 km = 120 px
    const r = (km) => km * ECH;

    // Espace hors attraction (champs), couronne (vert), pole : banlieue (bleu clair) et ville-centre (bleu).
    el("rect", { x: CX - r(52), y: CY - r(52), width: r(104), height: r(104), rx: 10, fill: "#EEF1F4" });
    el("circle", { cx: CX, cy: CY, r: r(rCouronne), fill: VERT, opacity: 0.28 });
    el("circle", { cx: CX, cy: CY, r: r(R_BANLIEUE), fill: "#FFFFFF" }); // fond blanc : meme teinte que la legende
    el("circle", { cx: CX, cy: CY, r: r(R_BANLIEUE), fill: BLEU, opacity: 0.35 });
    el("circle", { cx: CX, cy: CY, r: r(R_CENTRE), fill: BLEU });
    // Couronne de 1970 en pointille quand elle s'est etalee depuis.
    if (annee > 1970) el("circle", { cx: CX, cy: CY, r: r(25), fill: "none", stroke: VERT, "stroke-width": 2, "stroke-dasharray": "5 4" });

    // Trajet domicile-travail : de la maison au centre (lieu de travail), en orange.
    const angle = -Math.PI / 6; // maison vers l'est-nord-est
    const xm = CX + r(distance) * Math.cos(angle), ym = CY + r(distance) * Math.sin(angle);
    if (distance > 0) {
      el("line", { x1: CX, y1: CY, x2: xm, y2: ym, stroke: ORANGE, "stroke-width": 4, "stroke-linecap": "round", "stroke-dasharray": "8 5" });
    }
    // Bureau au centre (carre blanc), maison (pentagone).
    el("rect", { x: CX - 6, y: CY - 6, width: 12, height: 12, fill: "#FFFFFF", stroke: ENCRE, "stroke-width": 2 });
    const maison = [[0, -11], [10, -2], [10, 9], [-10, 9], [-10, -2]].map(([dx, dy]) => `${xm + dx},${ym + dy}`).join(" ");
    el("polygon", { points: maison, fill: ROUGE, stroke: "#FFFFFF", "stroke-width": 2 }).setAttribute("data-adresse", "graphe/maison");

    // Legende a droite : quatre zones, celle de la maison en gras et encadree.
    const ZONES = [
      ["ville-centre", BLEU, 1, ["ville-", "centre"]],
      ["banlieue", BLEU, 0.35, ["banlieue"]],
      ["couronne périurbaine", VERT, 0.28, ["couronne", "périurbaine"]],
      ["hors de l'aire", "#EEF1F4", 1, ["hors", "de l'aire"]],
    ];
    const XL = 254;
    texte(XL - 2, 22, "pôle", 13, BLEU, true, "start");
    ZONES.forEach(([nom, couleur, op, lignes], i) => {
      const y = 32 + i * 60;
      el("rect", { x: XL, y, width: 22, height: 22, rx: 4, fill: couleur, opacity: op, stroke: nom === zone ? ENCRE : GRIS, "stroke-width": nom === zone ? 3 : 1 });
      lignes.forEach((m, k) => texte(XL - 2, y + 37 + k * 15, m, 13, ENCRE, nom === zone, "start"));
    });
    el("line", { x1: XL - 5, y1: 30, x2: XL - 5, y2: 142, stroke: BLEU, "stroke-width": 2 });

    // Bas : la zone de la maison et la longueur du trajet (aller), en km.
    texte(8, H - 34, `La maison est dans : ${zone}`, 15, ENCRE, true, "start");
    texte(8, H - 12, distance === 0 ? "Elle est au centre, à côté du travail." : `Trajet vers le centre : ${distance} km (aller)`, 14, ORANGE, true, "start");
    texte(CX, CY - r(rCouronne) - 6 < 14 ? 14 : CY - r(rCouronne) - 6, `couronne en ${annee}`, 13, VERT, true);
    return { distance, annee, zone };

    function texte(x, y, chaine, taille, couleur, gras, ancre) {
      let cx = x;
      if (!ancre || ancre === "middle") {
        const demi = (chaine.length * taille * 0.56) / 2;
        cx = Math.min(340 - 4 - demi, Math.max(4 + demi, x));
      }
      return el("text", { x: cx, y, "font-size": taille, "text-anchor": ancre || "middle", fill: couleur, "font-weight": gras ? 700 : 400 }, chaine);
    }
  },
};
