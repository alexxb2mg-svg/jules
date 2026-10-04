// Jules - gabarit "bande-fractions" : une bande par unite, coupee en d parts egales ; e bandes entieres puis
// n parts coloriees (sans e, n peut depasser d : les parts en trop remplissent la bande suivante). Curseur g : on
// regroupe les parts par paquets de g ; quand g divise d et le nombre de parts coloriees, les paquets tombent
// juste et la meme longueur coloriee s'ecrit avec moins de parts (simplification).
// La figure n'ecrit aucune fraction : l'eleve compte les parts et les paquets lui-meme.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["bande-fractions"] = {
  dessiner(svg, valeurs) {
    const entier = (v, defaut, min, max) => {
      const x = Math.round(Number(v ?? defaut));
      return Math.min(max, Math.max(min, Number.isFinite(x) ? x : defaut));
    };
    const d = entier(valeurs.d, 4, 1, 24);
    const e = entier(valeurs.e, 0, 0, 6);
    // avec des bandes entieres (e donne), n compte les parts EN PLUS : au plus d - 1, sinon c'est une bande de plus
    const avecEntiers = valeurs.e !== undefined;
    const nDemande = entier(valeurs.n, 3, 0, 48);
    const n = avecEntiers ? Math.min(nDemande, d - 1) : nDemande;
    const k = entier(valeurs.g, 1, 1, 24);
    const total = e * d + n; // nombre de parts coloriees
    const bandes = Math.max(1, Math.ceil(total / d));
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const noeud = document.createElementNS(NS, nom);
      for (const cle in attrs) noeud.setAttribute(cle, attrs[cle]);
      if (texte !== undefined) noeud.textContent = texte;
      svg.appendChild(noeud);
      return noeud;
    };
    // hauteur selon le nombre de bandes (au moins 170, au plus 340) : pas de grand vide sous une seule bande
    const X0 = 20, L = 280; // la bande va de x = 20 a x = 300 ; le numero de l'unite est ecrit a droite
    const ecart = bandes <= 4 ? 16 : 8;
    const h = Math.min(56, (252 - (bandes - 1) * ecart) / bandes);
    const bas = 40 + bandes * h + (bandes - 1) * ecart; // bas de la derniere bande
    const H = Math.min(340, Math.max(170, Math.ceil(bas + 44)));
    svg.setAttribute("viewBox", `0 0 340 ${H}`);
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    const part = L / d;
    const paquets = k > 1;
    const justes = d % k === 0 && total % k === 0;
    const limite = avecEntiers && nDemande > n; // n demande trop grand : on le dit au lieu de se taire
    el("text", { x: 170, y: 22, "font-size": 14, "text-anchor": "middle", fill: limite ? "#C8102E" : "#6B7686" },
      limite ? `au plus ${d - 1} part${d > 2 ? "s" : ""} en plus des bandes entières` : "1 bande = 1 unité");

    for (let r = 0; r < bandes; r++) {
      const y = 40 + r * (h + ecart);
      // parts coloriees de cette bande
      const pleines = Math.min(d, Math.max(0, total - r * d));
      if (pleines > 0) {
        el("rect", { x: X0, y, width: pleines * part, height: h, fill: "#1F4E8C", "fill-opacity": 0.8 });
      }
      // traits de partage : fins et gris quand on regroupe, sinon nets
      for (let j = 1; j < d; j++) {
        const surPaquet = paquets && j % k === 0;
        if (surPaquet) continue;
        el("line", {
          x1: X0 + j * part, y1: y, x2: X0 + j * part, y2: y + h,
          stroke: paquets ? "#9AA3AF" : "#14243B", "stroke-width": 2,
        });
      }
      if (paquets) {
        for (let j = k; j < d; j += k) {
          el("line", { x1: X0 + j * part, y1: y - 3, x2: X0 + j * part, y2: y + h + 3, stroke: "#14243B", "stroke-width": 4 });
        }
        // paquet incomplet en bout de bande (k ne divise pas d)
        const reste = d % k;
        if (reste > 0) {
          el("rect", {
            x: X0 + (d - reste) * part + 2, y: y + 2, width: reste * part - 4, height: h - 4,
            fill: "none", stroke: "#C8102E", "stroke-width": 3, "stroke-dasharray": "6 4",
          });
        }
        // paquet coupe par la fin du coloriage (k ne divise pas le nombre de parts coloriees)
        if (pleines > 0 && pleines < d && pleines % k !== 0) {
          const debut = Math.floor(pleines / k) * k;
          const fin = debut + k;
          if (fin <= d) { // sinon c'est le paquet incomplet du bout, deja entoure
            el("rect", {
              x: X0 + debut * part + 2, y: y + 2, width: (fin - debut) * part - 4, height: h - 4,
              fill: "none", stroke: "#C8102E", "stroke-width": 3, "stroke-dasharray": "6 4",
            });
          }
        }
      }
      el("rect", { x: X0, y, width: L, height: h, fill: "none", stroke: "#14243B", "stroke-width": 2.5 });
      el("text", {
        x: X0 + L + 10, y: y + h / 2 + 5, "font-size": 14, "text-anchor": "start", fill: "#6B7686",
      }, String(r + 1));
    }

    if (paquets) {
      el("text", {
        x: 170, y: bas + 32, "font-size": 15, "text-anchor": "middle", "font-weight": "bold",
        fill: justes ? "#2E7D32" : "#C8102E",
      }, justes ? `Paquets de ${k} : ils tombent juste` : `Paquets de ${k} : ils ne tombent pas juste`);
    }
    return { n, d, e, g: k, total, bandes, justes };
  },
};
