// Jules - gabarit "chaine-accords" : des mots en blocs, le mot qui commande l'accord en vert, des fleches vertes
// vers les mots qui s'accordent avec lui, et les marques d'accord (e, s, x, nt...) en orange.
// Quatre lectures selon les curseurs de la fiche :
//   adjectifs + place                -> le groupe nominal s'allonge autour d'un seul nom noyau (CM1)
//   exemple + genre + nombre         -> chaine d'accords dans le groupe nominal (CM1, discussion) ;
//     + noms 2 (exemple 1 a 3)        -> deux noms coordonnes, un adjectif commun (3e) ;
//     exemple 4 + place               -> participe passe avec avoir : 0 COD apres, 1 COD avant (3e)
//   verbe + voisin + genre + nombre  -> accord sujet-verbe, piege du groupe intercale (CM1)
//   genre + nombre (seuls)           -> quels mots varient, lesquels restent invariables (CM1)
// Faits (3e) : un adjectif qui qualifie deux noms coordonnes se met au pluriel, au masculin des qu'un des noms est
// masculin (le pantalon et la veste neufs ; la jupe et la veste neuves) ; avec avoir, le participe passe s'accorde
// avec le COD seulement s'il est place avant le verbe, souvent le pronom relatif « que » qui reprend son antecedent
// (les pommes que j'ai mangees), et reste invariable si le COD est apres (j'ai mange les pommes).
// Sources : Eduscol, « La grammaire du francais — Terminologie grammaticale » (accords : adjectif, participe passe)
// https://eduscol.education.gouv.fr/sites/default/files/document/guide-la-grammaire-du-francais-terminologie-grammaticale-67998.pdf ;
// Wikipedia, « Accord du participe passe en francais » (oldid 239496579) et « Accord (grammaire) » (oldid 238071441),
// sources des fiches 3e chaines-daccord et accord-participe-passe-avec-avoir.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["chaine-accords"] = {
  dessiner(svg, valeurs) {
    const NS = "http://www.w3.org/2000/svg";
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", VERT = "#2E7D32", ORANGE = "#E07B00";
    const a = (cle) => Object.prototype.hasOwnProperty.call(valeurs, cle);
    const n = (cle, defaut, mini, maxi) => {
      const v = Number(valeurs[cle]);
      return Math.min(maxi, Math.max(mini, Math.round(Number.isFinite(v) ? v : defaut)));
    };
    const el = (nom, attrs, parent) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      (parent || svg).appendChild(e);
      return e;
    };
    const POLICE = "system-ui, Arial, sans-serif";
    const texte = (x, y, contenu, taille, couleur, gras) => {
      const t = el("text", { x, y, "font-size": taille, fill: couleur, "text-anchor": "middle", "font-family": POLICE,
        "font-weight": gras ? 700 : 400 });
      t.textContent = contenu;
      return t;
    };
    // largeur d'un texte : mesuree si le SVG est affiche, sinon estimee
    const mesure = (contenu, taille, gras) => {
      const t = el("text", { x: 0, y: -50, "font-size": taille, "font-family": POLICE, "font-weight": gras ? 700 : 400 });
      t.textContent = contenu;
      let l = 0;
      try { l = t.getComputedTextLength(); } catch (e) { l = 0; }
      svg.removeChild(t);
      return l > 0 ? l : contenu.length * taille * (gras ? 0.6 : 0.55);
    };
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // Un bloc : { bouts: [[texte, marque?]], classe, ton: noyau | accord | gris | change | neutre }
    // m(texte) = une marque d'accord (orange) ; b(texte) = le reste du mot.
    const b = (t) => [t, false], m = (t) => [t, true];
    const COULEUR = { noyau: VERT, accord: BLEU, gris: GRIS, change: ORANGE, neutre: BLEU };
    const FOND = { noyau: "#E9F4EA", accord: "#FFFFFF", gris: "#FFFFFF", change: "#FDF0E1", neutre: "#FFFFFF" };

    // place une rangee de blocs centree a la hauteur y ; police reduite (jamais sous 14) si la rangee deborde
    const rangee = (blocs, y) => {
      let taille = 22, larg = [], total = 0;
      const ecart = 8, pad = 20;
      for (; taille >= 14; taille--) {
        larg = blocs.map((bl) => Math.max(mesure(bl.bouts.map((x) => x[0]).join(""), taille, true) + pad,
          mesure(bl.classe, 13, false) + 10));
        total = larg.reduce((s, l) => s + l, 0) + ecart * (blocs.length - 1);
        if (total <= 326) break;
      }
      let x = 170 - total / 2;
      const H = 44;
      blocs.forEach((bl, i) => {
        const c = COULEUR[bl.ton];
        el("rect", { x, y, width: larg[i], height: H, rx: 8, fill: FOND[bl.ton], stroke: c,
          "stroke-width": bl.ton === "gris" ? 2 : 3, "stroke-dasharray": bl.ton === "gris" ? "5 4" : "none" });
        const t = texte(x + larg[i] / 2, y + 29, "", taille, bl.ton === "noyau" ? VERT : bl.ton === "gris" ? GRIS : ENCRE, true);
        for (const [bout, marque] of bl.bouts) {
          const s = el("tspan", marque ? { fill: ORANGE, "text-decoration": "underline" } : {}, t);
          s.textContent = bout;
        }
        texte(x + larg[i] / 2, y + H + 18, bl.classe, 13, c, bl.ton === "noyau");
        bl.cx = x + larg[i] / 2;
        bl.haut = y;
        x += larg[i] + ecart;
      });
    };
    // fleche verte en arc, du mot qui commande vers un mot qui s'accorde (au-dessus des blocs)
    const arc = (de, vers, couleur, decal) => {
      const x1 = de.cx + (vers.cx > de.cx ? 1 : -1) * (8 + 12 * (decal || 0)), x2 = vers.cx, y = de.haut - 2;
      const h = Math.min(72, 22 + Math.abs(x2 - x1) * 0.28);
      el("path", { d: `M${x1},${y} C${x1},${y - h} ${x2},${y - h} ${x2},${y - 8}`, fill: "none", stroke: couleur, "stroke-width": 3 });
      el("polygon", { points: `${x2},${y} ${x2 - 6},${y - 11} ${x2 + 6},${y - 11}`, fill: couleur });
    };
    const genreNombre = (f, p) => `${f ? "féminin" : "masculin"}, ${p ? "pluriel" : "singulier"}`;

    // ------------------------------------------------ le groupe nominal autour du nom noyau
    if (a("adjectifs")) {
      const nb = n("adjectifs", 1, 0, 2), apres = n("place", 1, 0, 1);
      svg.setAttribute("viewBox", "0 0 340 220");
      const det = { bouts: [b("le")], classe: "déterminant", ton: "neutre" };
      const nom = { bouts: [b("chat")], classe: "nom noyau", ton: "noyau" };
      const adj = (t) => ({ bouts: [b(t)], classe: "adjectif", ton: "accord" });
      let blocs, adjs = [];
      if (nb === 0) blocs = [det, nom];
      else if (apres === 0) { adjs = nb === 1 ? [adj("petit")] : [adj("joli"), adj("petit")]; blocs = [det, ...adjs, nom]; }
      else { adjs = nb === 1 ? [adj("gris")] : [adj("gris"), adj("tigré")]; blocs = [det, nom, ...adjs]; }
      rangee(blocs, 100);
      adjs.forEach((x) => arc(nom, x, VERT));
      texte(170, 200, nb === 0 ? "groupe minimal : déterminant + nom" : "un seul nom noyau : chat", 15, VERT, true);
      return { adjectifs: nb, place: apres };
    }

    // ------------------------------------------------ accord sujet-verbe (avec le piege du groupe intercale)
    if (a("voisin") || a("verbe")) {
      const p = n("nombre", 0, 0, 1), f = n("genre", 0, 0, 1), ecran = n("voisin", 0, 0, 1), etre = n("verbe", 0, 0, 1);
      svg.setAttribute("viewBox", "0 0 340 220");
      const sujet = { bouts: [b("L"), p ? m("es") : f ? m("a") : b("e"), b(" chat")].concat(f ? [m("te")] : [], p ? [m("s")] : []),
        classe: "sujet", ton: "noyau" };
      const blocs = [sujet];
      if (ecran) blocs.push({ bouts: [b("du voisin")], classe: "complément", ton: "gris" });
      let cibles;
      if (etre) {
        const aux = { bouts: p ? [b("so"), m("nt")] : [b("est")], classe: "être", ton: "accord" };
        const pp = { bouts: [b("parti")].concat(f ? [m("e")] : [], p ? [m("s")] : []), classe: "participe", ton: "accord" };
        blocs.push(aux, pp);
        cibles = [aux, pp];
      } else {
        const v = { bouts: [b("miaule")].concat(p ? [m("nt")] : []), classe: "verbe", ton: "accord" };
        blocs.push(v);
        cibles = [v];
      }
      rangee(blocs, 100);
      cibles.forEach((c, i) => arc(sujet, c, VERT, i));
      texte(170, 200, "sujet : " + genreNombre(f, p), 15, VERT, true);
      return { genre: f, nombre: p, voisin: ecran, verbe: etre };
    }

    // ------------------------------------------------ chaine d'accords dans le groupe nominal (3 exemples, deux noms) et participe passe avec avoir
    if (a("exemple")) {
      // lecture proposee dans la discussion : exemple, genre, nombre, noms et place y sont declarees (extension.yaml)
      const ex = n("exemple", valeurs.exemple ?? 1, 1, 4), f = n("genre", valeurs.genre ?? 0, 0, 1), p = n("nombre", valeurs.nombre ?? 0, 0, 1);
      const noms = n("noms", 1, 1, 2);
      svg.setAttribute("viewBox", "0 0 340 220");
      if (ex === 4) {
        // participe passe avec avoir (3e) : place 0 = COD apres le verbe, pas d'accord ; 1 = COD place avant
        // (pronom relatif « que » qui reprend son antecedent), le participe s'accorde avec lui.
        const avant = n("place", 1, 0, 1);
        const cod = { bouts: p ? [b("les "), b(f ? "pommes" : "gâteaux")] : [b(f ? "la pomme" : "le gâteau")],
          classe: avant ? "antécédent" : "COD", ton: "noyau" };
        const aux = { bouts: [b("j'ai")], classe: "avoir", ton: "gris" };
        const pp = { bouts: [b("mangé")].concat(avant && f ? [m("e")] : [], avant && p ? [m("s")] : []),
          classe: "participe", ton: "accord" };
        rangee(avant ? [cod, { bouts: [b("que")], classe: "COD", ton: "neutre" }, aux, pp] : [aux, pp, cod], 100);
        if (avant) arc(cod, pp, VERT);
        texte(170, 200, avant ? "COD avant : accord, " + genreNombre(f, p) : "COD après : pas d'accord", 15,
          avant ? VERT : GRIS, true);
        return { exemple: ex, genre: f, nombre: p, noms, place: avant };
      }
      if (noms === 2) {
        // deux noms coordonnes (3e) : l'adjectif se met au pluriel, au masculin des que l'un des noms est masculin
        // genre 0 : le pantalon (m.) et la veste (f.) -> neufs ; genre 1 : la jupe et la veste (f.) -> neuves
        const s = p ? [m("s")] : [];
        const n1 = { bouts: p ? [b("les "), b(f ? "jupe" : "pantalon")].concat(s) : [b(f ? "la jupe" : "le pantalon")],
          classe: f ? "nom féminin" : "nom masculin", ton: "noyau" };
        const et = { bouts: [b("et")], classe: "", ton: "gris" };
        const n2 = { bouts: p ? [b("les "), b("veste")].concat(s) : [b("la veste")], classe: "nom féminin", ton: "noyau" };
        const adj = { bouts: f ? [b("neu"), m("ves")] : [b("neuf"), m("s")], classe: "adjectif", ton: "accord" };
        rangee([n1, et, n2, adj], 100);
        arc(n1, adj, VERT);
        arc(n2, adj, VERT, 1);
        texte(170, 200, f ? "deux noms féminins : féminin pluriel" : "masculin + féminin : masculin pluriel", 15, VERT, true);
        return { exemple: ex, genre: f, nombre: p, noms };
      }
      const det = p ? [b("l"), m("es")] : f ? [b("l"), m("a")] : [b("le")];
      const s = p ? [m("s")] : [];
      let adj1, nom, adj2;
      if (ex === 1) {
        adj1 = [b("petit")].concat(f ? [m("e")] : [], s);
        nom = [b("chien")].concat(f ? [m("ne")] : [], s);
        adj2 = [b("noir")].concat(f ? [m("e")] : [], s);
      } else if (ex === 2) {
        adj1 = f ? [b("be"), m("lle")].concat(s) : p ? [b("beau"), m("x")] : [b("beau")];
        nom = f ? [b("jument")].concat(s) : p ? [b("chev"), m("aux")] : [b("cheval")];
        adj2 = f ? [b("blan"), m("che")].concat(s) : [b("blanc")].concat(s);
      } else {
        // gros et gris finissent deja par s : rien a ajouter au masculin pluriel
        adj1 = [b("gros")].concat(f ? [m("se")].concat(s) : []);
        nom = [b("chat")].concat(f ? [m("te")] : [], s);
        adj2 = [b("gris")].concat(f ? [m("e")].concat(s) : []);
      }
      const bdet = { bouts: det, classe: "déterminant", ton: "accord" };
      const ba1 = { bouts: adj1, classe: "adjectif", ton: "accord" };
      const bnom = { bouts: nom, classe: "nom noyau", ton: "noyau" };
      const ba2 = { bouts: adj2, classe: "adjectif", ton: "accord" };
      rangee([bdet, ba1, bnom, ba2], 100);
      [bdet, ba1, ba2].forEach((x) => arc(bnom, x, VERT));
      texte(170, 200, "nom noyau : " + genreNombre(f, p), 15, VERT, true);
      return { exemple: ex, genre: f, nombre: p };
    }

    // ------------------------------------------------ classes de mots : qui varie, qui reste invariable
    const f = n("genre", 0, 0, 1), p = n("nombre", 0, 0, 1);
    svg.setAttribute("viewBox", "0 0 340 250");
    const varie = f || p;
    const det = { bouts: p ? [b("L"), m("es")] : f ? [b("L"), m("a")] : [b("Le")], classe: "déterminant", ton: varie ? "change" : "neutre" };
    const adj = { bouts: [b("petit")].concat(f ? [m("e")] : [], p ? [m("s")] : []), classe: "adjectif", ton: varie ? "change" : "neutre" };
    const nom = { bouts: [b("chat")].concat(f ? [m("te")] : [], p ? [m("s")] : []), classe: "nom", ton: varie ? "change" : "neutre" };
    const verbe = { bouts: p ? [b("dorm"), m("ent")] : [b("dort")], classe: "verbe", ton: p ? "change" : "neutre" };
    const adv = { bouts: [b("bien")], classe: "adverbe", ton: "gris" };
    rangee([det, adj, nom], 24);
    rangee([verbe, adv], 112);
    // legende : une couleur = une idee
    el("rect", { x: 40, y: 206, width: 18, height: 18, rx: 4, fill: "#FDF0E1", stroke: ORANGE, "stroke-width": 3 });
    const t1 = texte(64, 221, "a changé", 14, ORANGE, true);
    t1.setAttribute("text-anchor", "start");
    el("rect", { x: 186, y: 206, width: 18, height: 18, rx: 4, fill: "#FFFFFF", stroke: GRIS, "stroke-width": 2, "stroke-dasharray": "5 4" });
    const t2 = texte(210, 221, "invariable", 14, GRIS, true);
    t2.setAttribute("text-anchor", "start");
    return { genre: f, nombre: p };
  },
};
