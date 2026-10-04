// Jules - gabarit "ombre-portee" : lampe, objet et ecran vus de cote. Les rayons qui frolent l'objet
// delimitent l'ombre portee sur l'ecran (a 3 m de la lampe) : taille de l'ombre = h x 3 / d.
// Curseurs : distance (lampe-objet, m), hauteur (de l'objet, cm), matiere (1 transparent, 2 translucide,
// 3 opaque). La figure n'ecrit aucune mesure de l'ombre : elle la montre.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["ombre-portee"] = {
  dessiner(svg, valeurs) {
    const d = Math.min(2.5, Math.max(0.5, Number(valeurs.distance ?? 1.5)));
    const h = Math.min(20, Math.max(5, Number(valeurs.hauteur ?? 10)));
    const matiere = Math.min(3, Math.max(1, Math.round(Number(valeurs.matiere ?? 3))));
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) {
        e.textContent = texte;
        // halo blanc sous la lettre : le texte reste lisible quand un rayon passe derriere
        e.setAttribute("stroke", "#FFFFFF");
        e.setAttribute("stroke-width", 4);
        e.setAttribute("paint-order", "stroke");
      }
      svg.appendChild(e);
      return e;
    };
    svg.setAttribute("viewBox", "0 0 340 340");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // Echelles : 3 m = 255 px a l'horizontale ; 1 cm = 2 px a la verticale (axe de la lampe a y = 150).
    const XL = 30, XE = 285, AXE = 150, PXM = (XE - XL) / 3, PXCM = 2;
    const X = (m) => XL + m * PXM;
    const xo = X(d), demi = (h * PXCM) / 2;
    const demiOmbre = demi * (3 / d); // Thales : l'ombre est h x 3 / d
    const LUMIERE = "#E07B00";

    // Ecran
    el("line", { x1: XE, y1: 22, x2: XE, y2: 278, stroke: "#6B7686", "stroke-width": 5 });
    el("text", { x: XE, y: 16, "font-size": 13, "text-anchor": "middle", fill: "#14243B" }, "écran");

    // Rayons qui frolent le haut et le bas de l'objet, prolonges jusqu'a l'ecran.
    const transparent = matiere === 1;
    for (const s of [-1, 1]) {
      el("line", { x1: XL, y1: AXE, x2: xo, y2: AXE + s * demi, stroke: LUMIERE, "stroke-width": 2.5 });
      el("line", {
        x1: xo, y1: AXE + s * demi, x2: XE, y2: AXE + s * demiOmbre, stroke: LUMIERE, "stroke-width": 2.5,
        "stroke-dasharray": transparent ? "none" : "6 4",
      });
    }
    // Zone d'ombre derriere l'objet, et ombre portee sur l'ecran.
    if (!transparent) {
      const opacite = matiere === 3 ? 0.28 : 0.12;
      el("polygon", {
        points: `${xo},${AXE - demi} ${XE},${AXE - demiOmbre} ${XE},${AXE + demiOmbre} ${xo},${AXE + demi}`,
        fill: "#14243B", "fill-opacity": opacite,
      });
      el("rect", {
        x: XE - 4, y: AXE - demiOmbre, width: 8, height: 2 * demiOmbre,
        fill: matiere === 3 ? "#14243B" : "#9AA3B0",
      });
      el("text", { x: XE + 9, y: AXE + 5, "font-size": 13, fill: "#14243B" }, "ombre");
    }

    // Objet (largeur 8 px) : plein si opaque, pale si translucide, contour seul si transparent.
    const remplissage = { 1: "#FFFFFF", 2: "#AFC4E0", 3: "#1F4E8C" }[matiere];
    el("rect", {
      x: xo - 4, y: AXE - demi, width: 8, height: 2 * demi, fill: remplissage,
      stroke: "#1F4E8C", "stroke-width": 2,
    });
    const nomMatiere = { 1: "transparent", 2: "translucide", 3: "opaque" }[matiere];
    el("text", { x: xo, y: AXE - demi - 22, "font-size": 13, "text-anchor": "middle", fill: "#1F4E8C" }, "objet");
    el("text", { x: xo, y: AXE - demi - 7, "font-size": 13, "text-anchor": "middle", fill: "#1F4E8C" }, nomMatiere);

    // Lampe
    el("circle", { cx: XL, cy: AXE, r: 11, fill: LUMIERE });
    el("text", { x: XL, y: AXE + 30, "font-size": 13, "text-anchor": "middle", fill: "#14243B" }, "lampe");

    // Regle graduee en metres sous la scene.
    el("line", { x1: XL, y1: 300, x2: XE, y2: 300, stroke: "#6B7686", "stroke-width": 2 });
    for (let m = 0; m <= 3; m++) {
      el("line", { x1: X(m), y1: 294, x2: X(m), y2: 306, stroke: "#6B7686", "stroke-width": 2 });
      el("text", { x: X(m), y: 324, "font-size": 13, "text-anchor": "middle", fill: "#6B7686" }, `${m} m`);
    }
    el("line", { x1: xo, y1: AXE + demi, x2: xo, y2: 300, stroke: "#1F4E8C", "stroke-width": 1.5, "stroke-dasharray": "3 4" });
    el("circle", { cx: xo, cy: 300, r: 4, fill: "#1F4E8C" });
    return { distance: d, hauteur: h, matiere, ombre: (h * 3) / d };
  },
};
