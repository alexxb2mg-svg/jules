// Jules - gabarit "horloge" : cadran a aiguilles. Valeurs h (heure de depart, 0 a 23), m (minutes de depart)
// et duree (minutes ecoulees). Les aiguilles montrent l'heure de depart : la petite avance avec les minutes.
// La duree est une part du cadran coloriee en vert, a partir de la grande aiguille, jusqu'a une aiguille verte
// en pointilles (minutes d'arrivee) ; chaque heure entiere ecoulee ajoute un anneau vert autour du cadran.
// L'heure n'est jamais ecrite en chiffres : seuls les nombres du cadran et le moment de la journee le sont.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["horloge"] = {
  dessiner(svg, valeurs) {
    const h = ((Math.round(Number(valeurs.h ?? 9)) % 24) + 24) % 24;
    const m = Math.min(59, Math.max(0, Number(valeurs.m ?? 15)));
    const duree = Math.max(0, Number(valeurs.duree ?? 0));
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte; // texte brut, jamais interprete
      svg.appendChild(e);
      return e;
    };
    const f = (n) => n.toFixed(1);
    svg.setAttribute("viewBox", "0 0 340 340");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    const cx = 170, cy = 182, R = 118;
    // Point du cadran a la fraction t d'un tour (0 = midi, sens des aiguilles d'une montre), au rayon r.
    const point = (t, r) => ({ x: cx + r * Math.sin(2 * Math.PI * t), y: cy - r * Math.cos(2 * Math.PI * t) });

    // Moment de la journee (l'heure du cadran est la meme le matin et l'apres-midi).
    const moment = h < 6 ? "la nuit" : h < 12 ? "le matin" : h < 18 ? "l'après-midi" : "le soir";
    el("text", { x: cx, y: 24, "font-size": 16, "font-weight": 700, "text-anchor": "middle", fill: "#14243B" }, `Départ : ${moment}`);

    // Anneaux verts : une heure entiere ecoulee par anneau (3 au plus).
    const heuresPleines = Math.min(3, Math.floor(duree / 60));
    for (let i = 0; i < heuresPleines; i++) {
      el("circle", { cx, cy, r: R + 8 + i * 8, fill: "none", stroke: "#2E7D32", "stroke-width": 4 });
    }

    // Cadran.
    el("circle", { cx, cy, r: R, fill: "#FFFFFF", stroke: "#14243B", "stroke-width": 3 });

    // Part de cadran parcourue par la grande aiguille pendant la duree (reste apres les heures entieres).
    const reste = duree % 60;
    const t0 = m / 60, t1 = (m + reste) / 60;
    if (reste > 0) {
      const a = point(t0, R - 4), b = point(t1, R - 4);
      const grand = reste > 30 ? 1 : 0;
      el("path", { d: `M${cx},${cy} L${f(a.x)},${f(a.y)} A${R - 4},${R - 4} 0 ${grand} 1 ${f(b.x)},${f(b.y)} Z`, fill: "#CDE8CF", stroke: "none" });
    } // heures pile : rien a colorier, les anneaux suffisent (la grande aiguille est revenue a sa place)

    // Graduations : 60 petites, 12 grandes, et les nombres 1 a 12.
    for (let i = 0; i < 60; i++) {
      const grande = i % 5 === 0;
      const a = point(i / 60, R - 3), b = point(i / 60, R - (grande ? 14 : 8));
      el("line", { x1: f(a.x), y1: f(a.y), x2: f(b.x), y2: f(b.y), stroke: grande ? "#14243B" : "#6B7686", "stroke-width": grande ? 3 : 2 });
    }
    for (let n = 1; n <= 12; n++) {
      const p = point(n / 12, R - 32);
      el("text", { x: f(p.x), y: f(p.y + 7), "font-size": 20, "font-weight": 700, "text-anchor": "middle", fill: "#14243B" }, String(n));
    }

    // Aiguille verte en pointilles : minutes d'arrivee (seulement s'il y a une duree).
    if (duree > 0) {
      const b = point(t1, R - 44);
      el("line", { x1: cx, y1: cy, x2: f(b.x), y2: f(b.y), stroke: "#2E7D32", "stroke-width": 4, "stroke-dasharray": "8 5", "stroke-linecap": "round" });
    }

    // Petite aiguille (heures, bleue, courte et epaisse) : avance d'1/12 de tour par heure, plus les minutes.
    const ph = point(((h % 12) + m / 60) / 12, R * 0.36);
    el("line", { x1: cx, y1: cy, x2: f(ph.x), y2: f(ph.y), stroke: "#1F4E8C", "stroke-width": 9, "stroke-linecap": "round" });
    // Grande aiguille (minutes, rouge, longue et fine) : s'arrete avant les nombres pour ne pas les cacher.
    const pm = point(t0, R - 44);
    el("line", { x1: cx, y1: cy, x2: f(pm.x), y2: f(pm.y), stroke: "#C8102E", "stroke-width": 5, "stroke-linecap": "round" });
    el("circle", { cx, cy, r: 7, fill: "#14243B" });
    return { h, m, duree };
  },
};
