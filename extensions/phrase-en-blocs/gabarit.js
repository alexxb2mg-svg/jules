// Jules - gabarit "phrase-en-blocs" : une phrase decoupee en blocs colores par fonction (sujet bleu, verbe rouge,
// COD vert, complement circonstanciel orange), qu'on transforme ou qu'on manipule avec des curseurs entiers.
// Le curseur phrase choisit la scene (fige par chaque fiche, min = max) :
//   1 types et formes : « Tu ranges ta chambre. » ; type 1 declaratif, 2 interrogatif avec inversion,
//     3 interrogatif avec « est-ce que », 4 imperatif ; negatif 1 : « ne » et « pas » entourent le verbe.
//   2 manipuler les groupes : « Le chat poursuit la souris dans le jardin. » ; groupe 1 sujet, 2 COD,
//     3 complement circonstanciel ; position 1 = groupe deplace (en tete ; le sujet, deja en tete, passe a la fin) ;
//     pronom 1 = groupe remplace par un pronom (il, la, y) ; supprime 1 = groupe enleve. supprime l'emporte sur
//     pronom, et l'un ou l'autre sur position.
//     La phrase se barre en rouge quand la manipulation la rend fausse ou incomplete.
//   3 nature et fonction : le meme groupe nominal « le matin » dans trois phrases ; position 0 sujet
//     (« Le matin est calme. »), 1 COD (« Léa aime le matin. »), 2 complement circonstanciel (« Léa lit le matin. ») :
//     l'etiquette du dessus (fonction) change, celle du dessous (nature : groupe nominal) reste.
// Faits verifies : trois types de phrases (declaratif, interrogatif, imperatif) et forme negative « ne... pas »
// autour du verbe conjugue ; sujet absent a l'imperatif, « range » sans s (verbe en -er, 2e personne du singulier) ;
// complement circonstanciel deplacable et supprimable, COD ni deplacable ni supprimable sans changer le sens ;
// pronom personnel complement place avant le verbe (« Le chat la poursuit »), « y » pour un complement de lieu.
// Sources : Programme de francais du cycle 3, arrete du 10-4-2025, BO n° 16 du 17/04/2025, p. 17-18
// (https://www.education.gouv.fr/sites/default/files/programme-de-fran-ais-pour-le-cycle-3-439824.pdf) ;
// Eduscol, « La grammaire du francais — Terminologie grammaticale », p. 43, 67-68, 85
// (https://eduscol.education.gouv.fr/sites/default/files/document/guide-la-grammaire-du-francais-terminologie-grammaticale-67998.pdf).
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["phrase-en-blocs"] = {
  dessiner(svg, valeurs) {
    const NS = "http://www.w3.org/2000/svg";
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", ROUGE = "#C8102E", VERT = "#2E7D32", ORANGE = "#E07B00";
    const n = (cle, defaut, mini, maxi) => {
      const v = Number(valeurs[cle]);
      return Math.min(maxi, Math.max(mini, Math.round(Number.isFinite(v) ? v : defaut)));
    };
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte; // texte brut, jamais interprete
      svg.appendChild(e);
      return e;
    };
    const POLICE = "system-ui, Arial, sans-serif";
    const ecrire = (x, y, contenu, taille, couleur, gras) =>
      el("text", { x, y, "font-size": taille, fill: couleur, "font-family": POLICE, "font-weight": gras ? 700 : 400,
        "text-anchor": "middle" }, contenu);
    // largeur d'un texte : mesuree si le SVG est affiche, sinon estimee
    const mesure = (contenu, taille, gras) => {
      const t = el("text", { x: 0, y: -50, "font-size": taille, "font-family": POLICE, "font-weight": gras ? 700 : 400 }, contenu);
      let l = 0;
      try { l = t.getComputedTextLength(); } catch (e) { l = 0; }
      svg.removeChild(t);
      return l > 0 ? l : contenu.length * taille * (gras ? 0.6 : 0.55);
    };

    // une fonction = une couleur
    const TON = {
      sujet: { c: BLEU, fond: "#E8EEF6", nom: "sujet" },
      verbe: { c: ROUGE, fond: "#FBE7EA", nom: "verbe" },
      cod: { c: VERT, fond: "#E9F4EA", nom: "COD" },
      cc: { c: ORANGE, fond: "#FDF0E1", nom: "circonstanciel" },
      neg: { c: ROUGE, fond: "#FFFFFF", nom: "négation", tirets: true },
      ajout: { c: GRIS, fond: "#FFFFFF", nom: "question", tirets: true },
      efface: { c: GRIS, fond: "#FFFFFF", nom: "pas de sujet", tirets: true, barre: true },
      autre: { c: GRIS, fond: "#FFFFFF", nom: "" },
      point: { c: ENCRE, fond: "none", nom: "" },
    };
    const bloc = (t, ton, etiquette) => ({ t, ton, etiquette: etiquette === undefined ? TON[ton].nom : etiquette });

    // place les blocs sur une ou deux rangees centrees ; police de 20 a 14 ; renvoie le bas de la derniere rangee
    const H = 40, ECART = 6;
    const placer = (blocs, y0, sansEtiquette) => {
      const largeurs = (taille) => blocs.map((b) => b.ton === "point" ? mesure(b.t, taille + 6, true) + 4 :
        Math.max(mesure(b.t, taille, true) + 18, sansEtiquette ? 0 : mesure(b.etiquette, 13, false) + 6));
      const total = (ls) => ls.reduce((s, l) => s + l, 0) + ECART * (ls.length - 1);
      // une rangee si elle tient en police >= 17 (lisible a 240 px) ; sinon deux rangees equilibrees, police la plus
      // grande possible (20 a 14) ; le point final reste toujours avec le dernier bloc
      const tous = blocs.map((b, i) => i);
      let taille = 20, ls = largeurs(taille);
      while (taille > 17 && total(ls) > 326) { taille -= 1; ls = largeurs(taille); }
      let rangees = [tous];
      if (total(ls) > 326) {
        const deux = (lt) => { // meilleure coupure k : rangee 1 = [0, k), rangee 2 = [k, n)
          let mieux = null;
          for (let k = 1; k < blocs.length - 1; k++) {
            const w = Math.max(total(lt.slice(0, k)), total(lt.slice(k)));
            if (!mieux || w < mieux.w) mieux = { k, w };
          }
          return mieux;
        };
        taille = 20; ls = largeurs(taille);
        let c = deux(ls);
        while (taille > 14 && c.w > 326) { taille -= 1; ls = largeurs(taille); c = deux(ls); }
        rangees = [tous.slice(0, c.k), tous.slice(c.k)];
      }
      let y = y0;
      for (const r of rangees) {
        let x = 170 - total(r.map((i) => ls[i])) / 2;
        for (const i of r) {
          const b = blocs[i], s = TON[b.ton];
          if (b.ton === "point") {
            ecrire(x + ls[i] / 2, y + 30, b.t, taille + 6, ENCRE, true);
          } else {
            el("rect", { x, y, width: ls[i], height: H, rx: 8, fill: s.fond, stroke: s.c, "stroke-width": s.tirets ? 2 : 3,
              "stroke-dasharray": s.tirets ? "5 4" : "none" });
            ecrire(x + ls[i] / 2, y + 27, b.t, taille, s.tirets ? s.c : ENCRE, true);
            if (s.barre) el("line", { x1: x + 8, y1: y + 20, x2: x + ls[i] - 8, y2: y + 20, stroke: GRIS, "stroke-width": 2 });
            if (!sansEtiquette && b.etiquette) ecrire(x + ls[i] / 2, y + H + 16, b.etiquette, 13, s.c, false);
          }
          b.x = x; b.l = ls[i]; b.y = y;
          x += ls[i] + ECART;
        }
        y += H + (sansEtiquette ? 14 : 36);
      }
      return { bas: y, rangees: rangees.length, taille };
    };
    // phrase fausse ou incomplete : un trait rouge sur chaque rangee
    const barrer = (blocs) => {
      const parY = {};
      for (const b of blocs) {
        const r = (parY[b.y] = parY[b.y] || { x1: b.x, x2: b.x + b.l });
        r.x1 = Math.min(r.x1, b.x); r.x2 = Math.max(r.x2, b.x + b.l);
      }
      for (const y in parY) {
        el("line", { x1: parY[y].x1 - 4, y1: Number(y) + H / 2, x2: parY[y].x2 + 4, y2: Number(y) + H / 2, stroke: ROUGE, "stroke-opacity": 0.75,
          "stroke-width": 3, "stroke-linecap": "round" });
      }
    };
    const verdict = (y, ok, texte) => {
      el("rect", { x: 20, y, width: 300, height: 34, rx: 8, fill: ok ? "#E9F4EA" : "#FBE7EA", stroke: ok ? VERT : ROUGE,
        "stroke-width": 2 });
      ecrire(170, y + 23, texte, 15, ok ? VERT : ROUGE, true);
    };

    const scene = n("phrase", 2, 1, 3);
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // ------------------------------------------------ 1. types et formes de phrases
    if (scene === 1) {
      const type = n("type", 1, 1, 4), neg = n("negatif", 0, 0, 1);
      svg.setAttribute("viewBox", "0 0 340 240");
      const TITRES = ["déclaratif : une information", "interrogatif : une question", "interrogatif : une question",
        "impératif : un ordre"];
      ecrire(170, 24, TITRES[type - 1], 16, ENCRE, true);
      const sujet = bloc("tu", "sujet"), cod = bloc("ta chambre", "cod");
      const NE = bloc("ne", "neg"), PAS = bloc("pas", "neg");
      let blocs;
      if (type === 1) blocs = [bloc("Tu", "sujet"), ...(neg ? [NE] : []), bloc("ranges", "verbe"), ...(neg ? [PAS] : []), cod, bloc(".", "point")];
      else if (type === 2) blocs = [...(neg ? [bloc("Ne", "neg")] : []), bloc(neg ? "ranges-tu" : "Ranges-tu", "verbe", "verbe + sujet"),
        ...(neg ? [PAS] : []), cod, bloc("?", "point")];
      else if (type === 3) blocs = [bloc("Est-ce que", "ajout"), sujet, ...(neg ? [NE] : []), bloc("ranges", "verbe"),
        ...(neg ? [PAS] : []), cod, bloc("?", "point")];
      else blocs = [bloc("tu", "efface"), ...(neg ? [bloc("Ne", "neg")] : []), bloc(neg ? "range" : "Range", "verbe"),
        ...(neg ? [PAS] : []), cod, bloc("!", "point")];
      const r = placer(blocs, 48);
      const PONCT = ["point", "point d'interrogation", "point d'interrogation", "point d'exclamation"];
      ecrire(170, Math.max(r.bas + 10, 168), `${neg ? "forme négative" : "forme affirmative"} · ${PONCT[type - 1]}`, 14,
        neg ? ROUGE : GRIS, neg === 1);
      return { phrase: scene, type, negatif: neg };
    }

    // ------------------------------------------------ 3. nature et fonction : le meme groupe nominal, trois roles
    if (scene === 3) {
      const pos = n("position", 0, 0, 2);
      svg.setAttribute("viewBox", "0 0 340 240");
      const ROLE = ["sujet", "cod", "cc"][pos];
      const gn = bloc(pos === 0 ? "Le matin" : "le matin", ROLE, "");
      const blocs = pos === 0 ? [gn, bloc("est", "autre", ""), bloc("calme", "autre", ""), bloc(".", "point")]
        : pos === 1 ? [bloc("Léa", "autre", ""), bloc("aime", "autre", ""), gn, bloc(".", "point")]
          : [bloc("Léa", "autre", ""), bloc("lit", "autre", ""), gn, bloc(".", "point")];
      placer(blocs, 92, true);
      const cx = gn.x + gn.l / 2, c = TON[ROLE].c;
      const FONCTION = ["sujet", "COD", "complément circonstanciel"][pos];
      // au-dessus : la fonction, qui change
      ecrire(170, 30, "fonction : " + FONCTION, 17, c, true);
      el("line", { x1: cx, y1: 40, x2: cx, y2: 84, stroke: c, "stroke-width": 3 });
      el("polygon", { points: `${cx},${90} ${cx - 6},${79} ${cx + 6},${79}`, fill: c });
      // au-dessous : la nature, qui ne change pas
      el("line", { x1: cx, y1: 136, x2: cx, y2: 172, stroke: ENCRE, "stroke-width": 3 });
      el("polygon", { points: `${cx},${132} ${cx - 6},${143} ${cx + 6},${143}`, fill: ENCRE });
      ecrire(170, 196, "nature : groupe nominal", 17, ENCRE, true);
      ecrire(170, 222, "elle ne change pas", 14, GRIS, false);
      return { phrase: scene, position: pos, fonction: FONCTION };
    }

    // ------------------------------------------------ 2. manipuler les groupes : deplacer, remplacer, supprimer
    const groupe = n("groupe", 3, 1, 3), sup = n("supprime", 0, 0, 1), pro = sup ? 0 : n("pronom", 0, 0, 1);
    const dep = sup || pro ? 0 : n("position", 0, 0, 1);
    svg.setAttribute("viewBox", "0 0 340 284");
    // phrase de depart : [sujet] [verbe] [COD] [CC] .
    const S = { gn: "le chat", pro: "il" }, C = { gn: "la souris", pro: "la" }, L = { gn: "dans le jardin", pro: "y" };
    const maj = (t) => t.charAt(0).toUpperCase() + t.slice(1);
    // verdict : etat (« phrase correcte », « fausse », « incomplete ») et raison courte en dessous
    let ok = true, etat = "phrase correcte", raison = "";
    const parts = { sujet: bloc(S.gn, "sujet"), verbe: bloc("poursuit", "verbe"), cod: bloc(C.gn, "cod"), cc: bloc(L.gn, "cc") };
    let ordre = ["sujet", "verbe", "cod", "cc"];
    const cle = ["sujet", "cod", "cc"][groupe - 1];
    if (sup === 1) {
      ordre = ordre.filter((k) => k !== cle);
      if (cle === "cc") raison = "on peut l'enlever";
      else if (cle === "cod") { ok = false; etat = "phrase incomplète"; raison = "il poursuit quoi ?"; }
      else { ok = false; etat = "phrase fausse"; raison = "il manque le sujet"; }
    } else if (pro === 1) {
      if (cle === "sujet") parts.sujet = bloc(S.pro, "sujet", "pronom sujet");
      if (cle === "cod") { parts.cod = bloc(C.pro, "cod", "pronom COD"); ordre = ["sujet", "cod", "verbe", "cc"]; }
      if (cle === "cc") { parts.cc = bloc(L.pro, "cc", "pronom"); ordre = ["sujet", "cc", "verbe", "cod"]; }
      raison = cle === "sujet" ? "il remplace « le chat »" : cle === "cod" ? "la = la souris, placé avant le verbe"
        : "y = dans le jardin, avant le verbe";
    } else if (dep === 1) {
      if (cle === "sujet") { ordre = ["verbe", "cod", "cc", "sujet"]; ok = false; etat = "phrase fausse"; raison = "le sujet ne bouge pas"; }
      else if (cle === "cod") { ordre = ["cod", "sujet", "verbe", "cc"]; ok = false; etat = "phrase fausse"; raison = "le COD ne bouge pas"; }
      else { ordre = ["cc", "sujet", "verbe", "cod"]; raison = "on peut le déplacer"; }
    } else {
      etat = "la phrase de départ";
    }
    const blocs = ordre.map((k) => parts[k]);
    // majuscule au premier mot, virgule apres un complement circonstanciel deplace en tete
    blocs[0] = Object.assign({}, blocs[0], { t: maj(blocs[0].t) });
    if (ordre[0] === "cc" && dep === 1) blocs[0].t += ",";
    blocs.push(bloc(".", "point"));
    // le groupe manipule est montre par une fleche
    const r = placer(blocs, 28);
    if (!ok) barrer(blocs.filter((b) => b.ton !== "point"));
    const cible = blocs.find((b) => b === parts[cle] || (b.etiquette === parts[cle].etiquette && b.ton === parts[cle].ton));
    if (cible && sup !== 1) {
      // fleche au-dessus du bloc manipule, pointe vers le bas (dans l'espace libre entre les rangees)
      const cx = cible.x + cible.l / 2, yb = cible.y - 2;
      el("polygon", { points: `${cx},${yb} ${cx - 7},${yb - 11} ${cx + 7},${yb - 11}`, fill: TON[cle].c });
    }
    const yv = Math.max(r.bas + 10, 150);
    verdict(yv, ok, etat);
    if (raison) ecrire(170, yv + 56, raison, 14, ok ? VERT : ROUGE, false);
    const AIDE = ["groupe manipulé : sujet", "groupe manipulé : COD", "groupe manipulé : circonstanciel"];
    ecrire(170, yv + 80, AIDE[groupe - 1], 14, TON[cle].c, true);
    return { phrase: scene, groupe, position: dep, supprime: sup, pronom: pro, correcte: ok };
  },
};
