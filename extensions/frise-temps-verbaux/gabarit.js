// Jules - gabarit "frise-temps-verbaux" : une fleche du temps avec « maintenant », l'action placee dessus,
// et le nom du temps qui convient. Un seul gabarit, cinq lectures selon les curseurs de la fiche :
//   moment + fini                -> temps simples et composes du francais (3e, discussion)
//   longueur + fini              -> aspect borne / non borne, accompli / non accompli (3e)
//   moment + lien                -> preterit / present perfect / present / futur (anglais 3e)
//   moment + indirect            -> concordance au discours indirect, « un cran vers le passe » (anglais 3e)
//   moment + habitude + personne -> present, imparfait, passe compose, futur de « jouer » decompose (CM1)
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["frise-temps-verbaux"] = {
  dessiner(svg, valeurs) {
    const NS = "http://www.w3.org/2000/svg";
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", ROUGE = "#C8102E", VERT = "#2E7D32", ORANGE = "#E07B00";
    const a = (cle) => Object.prototype.hasOwnProperty.call(valeurs, cle);
    const n = (cle, defaut) => (Number.isFinite(Number(valeurs[cle])) ? Number(valeurs[cle]) : defaut);
    const borne = (v, mini, maxi) => Math.min(maxi, Math.max(mini, Math.round(v)));
    const el = (nom, attrs, parent) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      (parent || svg).appendChild(e);
      return e;
    };
    const texte = (x, y, contenu, taille, couleur, ancre, gras) => {
      const t = el("text", { x, y, "font-size": taille, fill: couleur, "text-anchor": ancre || "middle",
        "font-family": "system-ui, Arial, sans-serif", "font-weight": gras ? 700 : 400 });
      t.textContent = contenu;
      return t;
    };
    // largeur approchee d'un texte (pas de mesure : le SVG n'est pas toujours dans la page)
    const largeur = (contenu, taille) => contenu.length * taille * 0.56;
    // centre un texte sans qu'il sorte du cadre 10..330
    const centre = (x, contenu, taille) => {
      const demi = largeur(contenu, taille) / 2;
      return Math.min(330 - demi, Math.max(10 + demi, x));
    };
    const fleche = (x1, y1, x2, y2, couleur, epaisseur) => {
      el("line", { x1, y1, x2, y2, stroke: couleur, "stroke-width": epaisseur, "stroke-linecap": "round" });
      const ang = Math.atan2(y2 - y1, x2 - x1), L = 11, l = 6;
      const p = (dx, dy) => `${x2 - L * Math.cos(ang) + dy * Math.sin(ang) * l},${y2 - L * Math.sin(ang) - dy * Math.cos(ang) * l}`;
      el("polygon", { points: `${x2},${y2} ${p(0, 1)} ${p(0, -1)}`, fill: couleur });
    };
    // fleche du temps + repere « maintenant » ; renvoie la fonction position -> x
    const axe = (y, xMaintenant, U, motMaintenant, gauche, droite) => {
      fleche(12, y, 330, y, GRIS, 2);
      el("line", { x1: xMaintenant, y1: y - 30, x2: xMaintenant, y2: y + 12, stroke: ROUGE, "stroke-width": 3 });
      texte(centre(xMaintenant, motMaintenant, 14), y + 32, motMaintenant, 14, ROUGE, "middle", true);
      if (gauche) texte(12, y + 32, gauche, 13, GRIS, "start");
      if (droite) texte(328, y + 32, droite, 13, GRIS, "end");
      return (m) => xMaintenant + m * U;
    };
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // ------------------------------------------------ CM1 : moment, habitude, personne (verbe modele « jouer »)
    if (a("personne") || a("habitude")) {
      const moment = borne(n("moment", 0), -3, 3), habitude = borne(n("habitude", 0), 0, 1);
      const p = borne(n("personne", 4), 1, 6) - 1;
      svg.setAttribute("viewBox", "0 0 340 280");
      const X = axe(56, 170, 44, "maintenant", "avant", "plus tard");
      const x = X(moment);
      const temps = moment === 0 ? 2 : moment > 0 ? 3 : habitude === 1 ? 1 : 0;
      if (temps === 1) {
        // habitude ou action qui dure : une bande de petits points repetes
        el("line", { x1: x - 22, y1: 38, x2: x + 22, y2: 38, stroke: BLEU, "stroke-width": 11, "stroke-linecap": "round", "stroke-dasharray": "1 14" });
      } else {
        el("circle", { cx: x, cy: 38, r: 10, fill: BLEU, stroke: "#FFFFFF", "stroke-width": 2 });
      }
      el("line", { x1: x, y1: 48, x2: x, y2: 56, stroke: BLEU, "stroke-width": 2 });
      const cases = [["passé", "composé"], ["imparfait"], ["présent"], ["futur"]];
      cases.forEach((lignes, i) => {
        const cx = 10 + i * 82, actif = i === temps;
        el("rect", { x: cx, y: 104, width: 76, height: 46, rx: 8, fill: actif ? "#E8EEF7" : "none",
          stroke: actif ? BLEU : GRIS, "stroke-width": actif ? 3 : 2 });
        lignes.forEach((l, j) => texte(cx + 38, 104 + (lignes.length === 1 ? 29 : 20 + j * 16), l, 13,
          actif ? BLEU : GRIS, "middle", actif));
      });
      // forme conjuguee, decoupee : radical (bleu), marque de temps (orange), marque de personne (vert)
      const pronoms = ["je", "tu", "il", "nous", "vous", "ils"];
      let morceaux;
      if (temps === 0) {
        const aux = ["ai", "as", "a", "avons", "avez", "ont"][p];
        morceaux = [[p === 0 ? "j'" : pronoms[p] + " ", ENCRE], [aux, VERT], [" joué", BLEU]];
      } else if (temps === 1) {
        morceaux = [[pronoms[p] + " ", ENCRE], ["jou", BLEU], [["ai", "ai", "ai", "i", "i", "ai"][p], ORANGE],
          [["s", "s", "t", "ons", "ez", "ent"][p], VERT]];
      } else if (temps === 2) {
        morceaux = [[pronoms[p] + " ", ENCRE], ["jou", BLEU], [["e", "es", "e", "ons", "ez", "ent"][p], VERT]];
      } else {
        morceaux = [[pronoms[p] + " ", ENCRE], ["joue", BLEU], ["r", ORANGE], [["ai", "as", "a", "ons", "ez", "ont"][p], VERT]];
      }
      const forme = texte(170, 206, "", 28, ENCRE, "middle", true);
      for (const [bout, couleur] of morceaux) {
        const s = el("tspan", { fill: couleur }, forme);
        s.textContent = bout;
      }
      const legende = temps === 0
        ? [["auxiliaire", VERT], ["+", GRIS], ["participe passé", BLEU]]
        : temps === 2 ? [["radical", BLEU], ["personne", VERT]] : [["radical", BLEU], ["temps", ORANGE], ["personne", VERT]];
      const leg = texte(170, 254, "", 15, ENCRE, "middle", true);
      legende.forEach(([mot, couleur], i) => {
        const s = el("tspan", { fill: couleur }, leg);
        s.textContent = (i ? "   " : "") + mot;
      });
      return { moment, habitude, personne: p + 1 };
    }

    // ------------------------------------------------ anglais 3e : discours direct -> indirect, un cran vers le passe
    if (a("indirect")) {
      const moment = borne(n("moment", 0), -1, 1), indirect = borne(n("indirect", 0), 0, 1);
      svg.setAttribute("viewBox", "0 0 340 270");
      fleche(328, 18, 14, 18, GRIS, 2);
      texte(170, 40, "vers le passé", 13, GRIS);
      const haut = [null, ["prétérit", "lost"], ["présent", "am"], ["will", "will"]];
      const bas = [["past perfect", "had lost"], ["prétérit", "was"], ["would", "would"], null];
      const ligne = (cellules, y, titre, yTitre, actif, couleur, visible) => {
        texte(12, yTitre, titre, 13, visible ? ENCRE : GRIS, "start", true);
        cellules.forEach((c, i) => {
          if (!c) return;
          const cx = 10 + i * 82, on = i === actif;
          el("rect", { x: cx, y, width: 76, height: 58, rx: 8, fill: on ? (couleur === BLEU ? "#E8EEF7" : "#FDF0E1") : "none",
            stroke: on ? couleur : GRIS, "stroke-width": on ? 3 : 2, opacity: visible || on ? 1 : 0.55 });
          texte(cx + 38, y + 22, c[0], 13, on ? couleur : GRIS, "middle", false);
          texte(cx + 38, y + 45, c[1], 16, on ? ENCRE : GRIS, "middle", true);
        });
      };
      const col = moment + 2; // -1 -> preterit (colonne 1), 0 -> present (2), 1 -> will (3)
      ligne(haut, 74, "discours direct : « I … »", 66, col, BLEU, true);
      ligne(bas, 184, "indirect : he said that he …", 262, indirect ? col - 1 : -1, ORANGE, indirect === 1);
      if (indirect) fleche(10 + col * 82 + 30, 136, 10 + (col - 1) * 82 + 46, 180, ORANGE, 3);
      return { moment, indirect };
    }

    // ------------------------------------------------ francais 3e : aspect (duree de l'action, accompli ou non)
    if (a("longueur")) {
      const duree = borne(n("longueur", 0), 0, 4), terminee = borne(n("fini", 0), 0, 1);
      svg.setAttribute("viewBox", "0 0 340 250");
      axe(176, 310, 0, "maintenant", "passé", null);
      const cx = 140, y = 136, L = [0, 22, 46, 80, 112][duree];
      const borneeV = duree <= 2;
      if (duree === 0) {
        el("circle", { cx, cy: y, r: 9, fill: BLEU });
      } else if (borneeV) {
        el("line", { x1: cx - L, y1: y, x2: cx + L, y2: y, stroke: BLEU, "stroke-width": 12 });
        for (const bx of [cx - L, cx + L]) el("line", { x1: bx, y1: y - 16, x2: bx, y2: y + 16, stroke: ENCRE, "stroke-width": 3 });
      } else {
        // non borne : le coeur est plein, les bords s'effacent en pointilles (ni debut ni fin visibles)
        const c = L * 0.55;
        el("line", { x1: cx - c, y1: y, x2: cx + c, y2: y, stroke: BLEU, "stroke-width": 12 });
        el("line", { x1: cx - L, y1: y, x2: cx - c, y2: y, stroke: BLEU, "stroke-width": 12, "stroke-dasharray": "6 6", opacity: 0.45 });
        if (!terminee) el("line", { x1: cx + c, y1: y, x2: cx + L, y2: y, stroke: BLEU, "stroke-width": 12, "stroke-dasharray": "6 6", opacity: 0.45 });
      }
      if (terminee && !borneeV) {
        el("line", { x1: cx + 0.55 * L, y1: y, x2: cx + L, y2: y, stroke: BLEU, "stroke-width": 12 });
        el("line", { x1: cx + L, y1: y - 16, x2: cx + L, y2: y + 16, stroke: ENCRE, "stroke-width": 3 });
      }
      // point de vue (orange) : dans l'action si elle est vue en cours, apres sa fin si elle est vue terminee
      const fin = duree === 0 ? cx + 9 : cx + L;
      const vx = terminee ? Math.min(fin + 28, 290) : cx;
      el("polygon", { points: `${vx},${y + 24} ${vx - 9},${y + 40} ${vx + 9},${y + 40}`, fill: ORANGE });
      el("line", { x1: vx, y1: y + 24, x2: vx, y2: 176, stroke: ORANGE, "stroke-width": 2, "stroke-dasharray": "3 3" });
      texte(centre(vx, "on regarde d'ici", 13), 236, "on regarde d'ici", 13, ORANGE, "middle", true);
      const titre = borneeV ? "action bornée" : "action non bornée";
      const sous = terminee ? "vue terminée : temps composé" : borneeV ? "passé simple : premier plan" : "imparfait : arrière-plan";
      texte(170, 34, titre, 18, BLEU, "middle", true);
      texte(170, 60, sous, 14, ENCRE);
      return { longueur: duree, fini: terminee };
    }

    // ------------------------------------------------ anglais 3e : preterit ou present perfect (lien avec maintenant)
    if (a("lien")) {
      const moment = borne(n("moment", -2), -3, 3), lien = borne(n("lien", 0), 0, 1);
      svg.setAttribute("viewBox", "0 0 340 230");
      const X = axe(150, 170, 46, "now", "passé", "avenir");
      const x = X(moment), y = 150;
      el("circle", { cx: x, cy: y, r: 9, fill: BLEU });
      let nom;
      if (moment < 0 && lien === 1) {
        // le pont : l'action passee touche maintenant
        el("path", { d: `M${x},${y - 10} Q${(x + 170) / 2},${y - 70} 170,${y - 14}`, fill: "none", stroke: VERT, "stroke-width": 4 });
        texte(Math.max((x + 170) / 2, x + 24), y - 52, "lien", 14, VERT, "middle", true);
        nom = "present perfect";
      } else if (moment < 0) {
        el("rect", { x: x - 22, y: y + 44, width: 44, height: 22, rx: 4, fill: "none", stroke: GRIS, "stroke-width": 2 });
        texte(x, y + 60, "date", 13, GRIS);
        nom = "prétérit";
      } else {
        nom = moment === 0 ? "présent" : "will / going to";
      }
      texte(centre(x, nom, 18), 44, nom, 18, BLEU, "middle", true);
      el("line", { x1: x, y1: 52, x2: x, y2: y - 12, stroke: BLEU, "stroke-width": 2, "stroke-dasharray": "3 4" });
      return { moment, lien };
    }

    // ------------------------------------------------ francais 3e (et discussion) : moment + action terminee ou non
    // lecture proposee dans la discussion : seules ces deux valeurs y sont declarees (extension.yaml)
    const moment = borne(Number(valeurs.moment ?? -1), -2, 2), terminee = borne(Number(valeurs.fini ?? 0), 0, 1);
    svg.setAttribute("viewBox", "0 0 340 230");
    const X = axe(170, 170, 60, "maintenant", "passé", "avenir");
    const x = X(moment), y = 130;
    if (terminee) {
      // action terminee : trait ferme qui s'acheve au moment choisi
      el("line", { x1: x - 40, y1: y, x2: x, y2: y, stroke: BLEU, "stroke-width": 10 });
      for (const bx of [x - 40, x]) el("line", { x1: bx, y1: y - 15, x2: bx, y2: y + 15, stroke: ENCRE, "stroke-width": 3 });
    } else {
      // action en cours : trait ouvert des deux cotes
      el("line", { x1: x - 26, y1: y, x2: x + 14, y2: y, stroke: BLEU, "stroke-width": 10 });
      el("line", { x1: x - 40, y1: y, x2: x - 26, y2: y, stroke: BLEU, "stroke-width": 10, "stroke-dasharray": "4 5", opacity: 0.5 });
      fleche(x + 14, y, x + 34, y, BLEU, 4);
    }
    el("line", { x1: x, y1: y + 12, x2: x, y2: 170, stroke: BLEU, "stroke-width": 2, "stroke-dasharray": "3 4" });
    el("circle", { cx: x, cy: 170, r: 6, fill: BLEU });
    let nom;
    if (!terminee) nom = moment < 0 ? "imparfait" : moment === 0 ? "présent" : "futur simple";
    else nom = moment <= -2 ? "plus-que-parfait" : moment <= 0 ? "passé composé" : "futur antérieur";
    texte(centre(x, nom, 18), 36, nom, 18, BLEU, "middle", true);
    const famille = terminee ? "temps composé : auxiliaire + participe passé" : "temps simple";
    texte(170, 66, famille, 14, terminee ? ENCRE : GRIS, "middle", !!terminee);
    return { moment, fini: terminee };
  },
};
