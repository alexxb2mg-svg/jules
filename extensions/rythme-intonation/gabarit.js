// Jules - gabarit "rythme-intonation" : la musique d'un mot anglais. Un rond par syllabe, le rond de la syllabe
// forte plus gros (orange), les autres petits (bleus) ; au-dessus, la courbe de la voix, qui monte sur la syllabe
// forte puis monte (question fermee) ou descend (affirmation) a la fin. Valeurs : n (syllabes, 1 a 4), r (place de
// la syllabe forte comptee depuis la fin, 1 = derniere ; ramenee a n si r > n), fin (-1 la voix descend, 1 elle
// monte), force (0 voix normale, 1 plus forte, 2 tres forte : exclamation, courbe epaisse et point d'exclamation).
// Un mot exemple est ecrit sous les ronds, decoupe en syllabes, la syllabe forte en MAJUSCULES.
// Sources des accents (une seule syllabe accentuee principale, transcription API) : Wiktionary anglais,
// prononciation RP/GA, consultee le 04/10/2026 : cat /ˈkæt/, hotel /həʊˈtɛl/, teacher /ˈtiː.tʃə/,
// kangaroo /ˌkæŋ.ɡəˈɹuː/, banana /bəˈnɑːnə/, elephant /ˈɛlɪfənt/, misunderstand /mɪs.ʌn.dəˈstænd/,
// information /ˌɪn.fəˈmeɪ.ʃn̩/, America /əˈmɛɹɪkə/, caterpillar /ˈkætəˌpɪlə/ (accent secondaire non dessine).
// Intonation : voix montante pour une question fermee (yes/no), descendante pour une affirmation ou une question
// en wh- (Cambridge Grammar, « Intonation », dictionary.cambridge.org/grammar/british-grammar/intonation).
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["rythme-intonation"] = {
  dessiner(svg, valeurs) {
    const NS = "http://www.w3.org/2000/svg";
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", ORANGE = "#E07B00";
    const entier = (v, defaut, min, max) => {
      const x = Number(v);
      return Math.min(max, Math.max(min, Math.round(Number.isFinite(x) ? x : defaut)));
    };
    const n = entier(valeurs.n, 3, 1, 4);
    const r = Math.min(n, entier(valeurs.r, 2, 1, 4));
    const fin = Number(valeurs.fin ?? 1) < 0 ? -1 : 1;
    const force = entier(valeurs.force, 0, 0, 2);
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte; // texte brut, jamais interprete
      svg.appendChild(e);
      return e;
    };
    const f = (x) => x.toFixed(1);
    svg.setAttribute("viewBox", "0 0 340 290");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // Mots exemples : MOTS[n][r] = syllabes (accent verifie, voir l'en-tete).
    const MOTS = {
      1: { 1: ["cat"] },
      2: { 1: ["ho", "tel"], 2: ["tea", "cher"] },
      3: { 1: ["kan", "ga", "roo"], 2: ["ba", "na", "na"], 3: ["el", "e", "phant"] },
      4: { 1: ["mis", "un", "der", "stand"], 2: ["in", "for", "ma", "tion"], 3: ["A", "me", "ri", "ca"],
        4: ["ca", "ter", "pil", "lar"] },
    };
    const syllabes = MOTS[n][r];
    const forte = n - r; // indice de la syllabe forte
    const pas = 340 / (n + 1);
    const xs = syllabes.map((_, i) => pas * (i + 1));

    el("text", { x: 170, y: 22, "font-size": 14, "text-anchor": "middle", fill: GRIS }, "gros rond = syllabe forte");

    // Courbe de la voix : plus haute sur la syllabe forte, puis la fin monte ou descend (fleche).
    const Y0 = 118, HAUT = 78;
    const pts = [{ x: xs[0] - 34, y: Y0 }];
    xs.forEach((x, i) => pts.push({ x, y: i === forte ? HAUT : Y0 }));
    const derniere = xs[xs.length - 1];
    pts.push({ x: Math.min(318, derniere + 44), y: fin > 0 ? 42 : 146 });
    let d = `M${f(pts[0].x)},${f(pts[0].y)}`;
    for (let i = 1; i < pts.length - 1; i++) {
      const m = { x: (pts[i].x + pts[i + 1].x) / 2, y: (pts[i].y + pts[i + 1].y) / 2 };
      d += ` Q${f(pts[i].x)},${f(pts[i].y)} ${f(m.x)},${f(m.y)}`;
    }
    const bout = pts[pts.length - 1], avant = pts[pts.length - 2];
    d += ` L${f(bout.x)},${f(bout.y)}`;
    const epaisseur = [3, 6, 9][force];
    el("path", { d, fill: "none", stroke: BLEU, "stroke-width": epaisseur, "stroke-linecap": "round", "stroke-linejoin": "round" });
    // Pointe de fleche dans la direction du dernier troncon.
    const mil = { x: (avant.x + bout.x) / 2, y: (avant.y + bout.y) / 2 };
    const ang = Math.atan2(bout.y - mil.y, bout.x - mil.x), L = 14 + 2 * force;
    const p1 = { x: bout.x - L * Math.cos(ang - 0.5), y: bout.y - L * Math.sin(ang - 0.5) };
    const p2 = { x: bout.x - L * Math.cos(ang + 0.5), y: bout.y - L * Math.sin(ang + 0.5) };
    el("polygon", { points: `${f(bout.x)},${f(bout.y)} ${f(p1.x)},${f(p1.y)} ${f(p2.x)},${f(p2.y)}`, fill: BLEU, stroke: BLEU, "stroke-width": 2, "stroke-linejoin": "round" });

    // Ronds des syllabes et syllabes ecrites dessous.
    xs.forEach((x, i) => {
      const fort = i === forte;
      el("circle", { cx: f(x), cy: 190, r: fort ? 24 + 3 * force : 12, fill: fort ? ORANGE : "#C9D6EA", stroke: fort ? ENCRE : BLEU, "stroke-width": 2 });
      el("text", { x: f(x), y: 246, "font-size": fort ? 19 : 16, "font-weight": fort ? 700 : 400, "text-anchor": "middle", fill: fort ? ORANGE : ENCRE },
        fort ? syllabes[i].toUpperCase() : syllabes[i]);
    });

    // Le mot entier, avec la ponctuation que la voix fait entendre.
    const mot = syllabes.join("");
    // Exclamation : « ! », ou « ?! » si la voix monte (question etonnee) ; sinon « ? » ou « . » selon la fin.
    const ponct = force === 2 ? (fin > 0 ? "?!" : "!") : fin > 0 ? "?" : ".";
    el("text", { x: 170, y: 280, "font-size": 18, "font-weight": 700, "text-anchor": "middle", fill: ENCRE },
      mot.charAt(0).toUpperCase() + mot.slice(1) + ponct);
    return { n, r, fin, force };
  },
};
