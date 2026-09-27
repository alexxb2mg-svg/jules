// Sonde EX-106 (docs/spec/ADAPTATIONS-LOT2.md) : aucun contenu coupe ni superpose.
// Chargee par tests/test_adaptations_robustesse.py a la fin d'une vraie page de Jules (ou d'une page
// d'essai qui contient les vrais outils dans des cadres de meme origine). Elle attend que la page ait
// demarre, joue l'action du cas (ouvrir une lecon, taper dans la calculatrice...), puis releve :
//
// - debordement : le bloc qui porte un texte n'a pas de contenu plus large que lui
//   (scrollWidth > clientWidth) ;
// - texte coupe : chaque ligne de texte visible (Range.getClientRects d'un noeud texte) doit rester
//   dans la boite de chaque ancetre qui coupe (overflow hidden/clip) et dans la largeur de la page ;
//   un ancetre a defilement horizontal (scrollWidth > clientWidth) compte aussi comme une faute, un
//   texte qu'il faut faire defiler de cote n'est pas lisible d'un coup d'oeil ;
// - superposition : deux lignes de texte de deux noeuds differents ne se recouvrent pas (deux lignes
//   du meme conteneur a defilement : en entier ; de conteneurs differents : partie visible seulement,
//   ce qui a defile hors d'un conteneur n'est pas a l'ecran) ;
// - valeurs WCAG 1.4.12 (cas « wcag » seulement) : le style utilisateur injecte est bien celui qui
//   s'applique (interligne, espacement lettres/mots, marge des paragraphes), sur <body> compris.
//
// Le resultat est pose en JSON dans l'attribut data-resultat de <html>, relu par --dump-dom.
"use strict";
(function () {
  var script = document.currentScript;
  var CAS = script.getAttribute("data-cas") || "";
  var WCAG = script.getAttribute("data-wcag") === "1";
  var LEVIERS = script.getAttribute("data-leviers") === "1";
  var TOL = 1; // px : arrondis de mise en page
  var ATTENTE = 3000;

  function attendre(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }

  function court(t) { t = t.replace(/\s+/g, " ").trim(); return t.length > 40 ? t.slice(0, 40) + "…" : t; }

  function chemin(el) {
    var p = [];
    while (el && el.nodeType === 1 && p.length < 5) {
      var s = el.tagName.toLowerCase();
      if (el.id) { p.unshift(s + "#" + el.id); break; }
      if (el.classList.length) s += "." + Array.prototype.join.call(el.classList, ".");
      p.unshift(s);
      el = el.parentElement;
    }
    return p.join(">");
  }

  // Texte masque volontairement (lecteur d'ecran seulement, cache, transparent) : hors releve.
  function masque(el, win) {
    if (el.checkVisibility && !el.checkVisibility({ opacityProperty: true, visibilityProperty: true })) return true;
    for (var a = el; a && a.nodeType === 1; a = a.parentElement) {
      var cs = win.getComputedStyle(a);
      if (cs.clip !== "auto" && cs.clip !== "" || cs.clipPath !== "none") return true;
    }
    return false;
  }

  // Tiroir ferme : un panneau deplace hors de l'ecran par transform (menu, parcours, retours de Jules
  // sur telephone). Son texte n'est pas affiche tant qu'on ne l'ouvre pas : hors releve.
  function tiroirFerme(el, win, largeur) {
    for (var a = el; a && a.nodeType === 1; a = a.parentElement) {
      if (win.getComputedStyle(a).transform === "none") continue;
      var b = a.getBoundingClientRect();
      if (b.right <= 1 || b.left >= largeur - 1) return true;
    }
    return false;
  }

  // Analyse un document (la page, ou le document d'un cadre d'outil).
  function analyser(doc, nom) {
    var win = doc.defaultView;
    var fautes = [];
    var styles = new Map();
    function cs(el) { var s = styles.get(el); if (!s) { s = win.getComputedStyle(el); styles.set(el, s); } return s; }
    function faute(type, el, texte, detail) {
      fautes.push({ doc: nom, type: type, element: chemin(el), texte: court(texte || ""), detail: detail || "" });
    }

    var racine = doc.documentElement;
    var largeurPage = racine.clientWidth;
    if (racine.scrollWidth > largeurPage + TOL) faute("defilement-page", racine, "", racine.scrollWidth + " > " + largeurPage);

    // Calque fixe (position: fixed) : bulles et chat flottants de Jules, barres. Ils flottent par
    // construction au-dessus du contenu qui defile : on ne compare que des lignes du meme calque.
    var couches = new Map();
    function coucheFixe(el) {
      if (couches.has(el)) return couches.get(el);
      var c = null;
      if (el && el.nodeType === 1 && el !== doc.body) c = cs(el).position === "fixed" ? el : coucheFixe(el.parentElement);
      couches.set(el, c);
      return c;
    }

    // Superposition : deux lignes qui defilent ensemble (meme conteneur a defilement le plus proche)
    // sont comparees en entier, meme hors de l'ecran (l'eleve peut y descendre). Deux lignes de
    // conteneurs differents (lecon qui defile sous l'en-tete, panneaux) ne sont comparees que sur la
    // partie visible de chacune : ce qui a defile hors d'un conteneur n'est pas a l'ecran.
    // (Un texte coupe par un ancetre « hidden » est deja une faute, relevee plus bas.)
    var defileurs = new Map();
    function defileur(el) {
      if (!el || el === doc.body || el === racine || el.nodeType !== 1) return null;
      if (defileurs.has(el)) return defileurs.get(el);
      var s = cs(el);
      var d = s.overflowX !== "visible" || s.overflowY !== "visible" ? el : defileur(el.parentElement);
      defileurs.set(el, d);
      return d;
    }
    function partieVisible(r, el) {
      var g = r.left, d = r.right, h = r.top, bas = r.bottom;
      for (var a = el; a && a !== doc.body && a !== racine; a = a.parentElement) {
        var s = cs(a);
        if (s.overflowX === "visible" && s.overflowY === "visible") continue;
        var b = a.getBoundingClientRect();
        var x0 = b.left + a.clientLeft, y0 = b.top + a.clientTop;
        g = Math.max(g, x0); d = Math.min(d, x0 + a.clientWidth);
        h = Math.max(h, y0); bas = Math.min(bas, y0 + a.clientHeight);
        if (d - g <= 0.5 || bas - h <= 0.5) return null;
      }
      return { left: g, right: d, top: h, bottom: bas, height: bas - h };
    }

    var lignes = [];
    var defilementsVus = new Set();
    var debordsVus = new Set();
    var marcheur = doc.createTreeWalker(doc.body, win.NodeFilter.SHOW_TEXT);
    var noeud, nbTextes = 0;
    while ((noeud = marcheur.nextNode())) {
      if (!/\S/.test(noeud.nodeValue)) continue;
      var el = noeud.parentElement;
      if (!el || el.closest("script, style, noscript, template, option, title")) continue;
      if (masque(el, win)) continue;
      var plage = doc.createRange();
      plage.selectNodeContents(noeud);
      var rects = Array.prototype.filter.call(plage.getClientRects(), function (r) { return r.width > 0.5 && r.height > 0.5; });
      if (!rects.length) continue;
      if (tiroirFerme(el, win, largeurPage)) continue;
      nbTextes++;
      var texte = noeud.nodeValue;
      var couche = coucheFixe(el);
      // Bloc qui porte le texte : son contenu ne deborde pas de sa boite (scrollWidth > clientWidth).
      var porteur = el;
      while (porteur !== doc.body && cs(porteur).display.indexOf("inline") === 0) porteur = porteur.parentElement;
      if (porteur !== doc.body && !debordsVus.has(porteur) && porteur.namespaceURI === "http://www.w3.org/1999/xhtml"
          && porteur.scrollWidth > porteur.clientWidth + TOL && porteur.clientWidth > 0) {
        debordsVus.add(porteur);
        faute("deborde", porteur, texte, porteur.scrollWidth + " > " + porteur.clientWidth);
      }
      for (var i = 0; i < rects.length; i++) {
        var r = rects[i];
        lignes.push({ r: r, vue: partieVisible(r, el), defileur: defileur(el), noeud: noeud, el: el, texte: texte, couche: couche });
        if (r.left < -TOL || r.right > largeurPage + TOL) faute("hors-page", el, texte, Math.round(r.left) + ".." + Math.round(r.right) + " / " + largeurPage);
        for (var a = el; a && a !== doc.body && a !== racine; a = a.parentElement) {
          var s = cs(a);
          var coupeX = s.overflowX === "hidden" || s.overflowX === "clip";
          var coupeY = s.overflowY === "hidden" || s.overflowY === "clip";
          var defileX = s.overflowX === "auto" || s.overflowX === "scroll";
          if (!coupeX && !coupeY && !defileX) continue;
          var b = a.getBoundingClientRect();
          var gauche = b.left + a.clientLeft, haut = b.top + a.clientTop;
          if ((coupeX || defileX) && (r.left < gauche - TOL || r.right > gauche + a.clientWidth + TOL)) {
            faute(coupeX ? "coupe-x" : "defile-x", el, texte, "par " + chemin(a) + " : " + Math.round(r.left) + ".." + Math.round(r.right) + " hors " + Math.round(gauche) + ".." + Math.round(gauche + a.clientWidth));
          }
          if (coupeY && (r.top < haut - TOL || r.bottom > haut + a.clientHeight + TOL)) {
            faute("coupe-y", el, texte, "par " + chemin(a) + " : " + Math.round(r.top) + ".." + Math.round(r.bottom) + " hors " + Math.round(haut) + ".." + Math.round(haut + a.clientHeight));
          }
          if (defileX && a.scrollWidth > a.clientWidth + TOL && !defilementsVus.has(a)) {
            defilementsVus.add(a);
            faute("defilement-x", a, texte, a.scrollWidth + " > " + a.clientWidth);
          }
        }
      }
    }

    // Superposition : balayage des lignes triees par le haut.
    lignes.sort(function (p, q) { return p.r.top - q.r.top; });
    var paires = 0;
    for (var m = 0; m < lignes.length; m++) {
      var l1 = lignes[m];
      for (var n = m + 1; n < lignes.length && lignes[n].r.top < l1.r.bottom; n++) {
        var l2 = lignes[n];
        if (l1.noeud === l2.noeud || l1.couche !== l2.couche) continue;
        var a1 = l1.r, a2 = l2.r;
        if (l1.defileur !== l2.defileur) {
          if (!l1.vue || !l2.vue) continue;
          a1 = l1.vue; a2 = l2.vue;
        }
        var ix = Math.min(a1.right, a2.right) - Math.max(a1.left, a2.left);
        var iy = Math.min(a1.bottom, a2.bottom) - Math.max(a1.top, a2.top);
        // Deux lignes voisines se touchent (demi-interligne) : seul un vrai recouvrement compte.
        if (ix > 2 && iy > 0.25 * Math.min(l1.r.height, l2.r.height)) {
          paires++;
          if (paires <= 20) faute("superposition", l1.el, l1.texte, "avec " + chemin(l2.el) + " « " + court(l2.texte) + " » (" + Math.round(ix) + "x" + Math.round(iy) + " px)");
        }
      }
    }

    // Valeurs WCAG 1.4.12 reellement appliquees (le style utilisateur n'est pas ecrase).
    var ecarts = 0;
    if (WCAG) {
      var verifies = new Set([doc.body]);
      lignes.forEach(function (l) { verifies.add(l.el); });
      verifies.forEach(function (e) {
        var s = cs(e), fs = parseFloat(s.fontSize);
        var attendu = { lineHeight: 1.5 * fs, letterSpacing: 0.12 * fs, wordSpacing: 0.16 * fs };
        Object.keys(attendu).forEach(function (prop) {
          var v = parseFloat(s[prop]);
          if (!(Math.abs(v - attendu[prop]) <= 0.5)) {
            ecarts++;
            if (ecarts <= 20) faute("wcag-ecrase", e, e.textContent, prop + " = " + s[prop] + ", attendu " + attendu[prop].toFixed(2) + "px");
          }
        });
        if (e.tagName === "P" && Math.abs(parseFloat(s.marginBottom) - 2 * fs) > 0.5) {
          ecarts++;
          if (ecarts <= 20) faute("wcag-ecrase", e, e.textContent, "margin-bottom = " + s.marginBottom + ", attendu " + (2 * fs).toFixed(2) + "px");
        }
      });
    }

    var attributs = doc.body.getAttributeNames().filter(function (x) { return x.indexOf("data-adapt-") === 0; }).sort();
    return { doc: nom, textes: nbTextes, lignes: lignes.length, attributs: attributs, fautes: fautes };
  }

  // Actions des cas : ramener la page dans l'etat a mesurer.
  var ACTIONS = {
    "cours-lecon": async function () {
      var b = document.querySelector(".notion-ligne:not([disabled])");
      if (!b) throw new Error("aucune notion a ouvrir");
      b.click();
      await attendre(2500);
      var lecon = document.getElementById("lecon");
      if (!lecon || lecon.classList.contains("cache") || !document.querySelector("#blocs .bloc")) {
        throw new Error("la lecon ne s'est pas ouverte");
      }
    },
  };

  // Page d'essai des outils : les cadres sont crees par la page, on attend leur demarrage.
  async function analyserOutils() {
    var cadres = Array.prototype.slice.call(document.querySelectorAll("iframe[data-outil]"));
    await attendre(ATTENTE);
    return cadres.map(function (c) {
      var doc = c.contentDocument;
      // calculatrice : un nombre de chaque rang a l'ecran
      Array.prototype.forEach.call("123456789".split(""), function (ch) {
        doc.querySelectorAll("#pave button").forEach(function (b) { if (b.textContent === ch) b.click(); });
      });
      return analyser(doc, c.getAttribute("data-outil"));
    });
  }

  async function lancer() {
    await attendre(ATTENTE);
    if (document.fonts && document.fonts.ready) await document.fonts.ready;
    var action = ACTIONS[CAS];
    if (action) await action();
    var resultats = CAS === "outils" ? await analyserOutils() : [analyser(document, CAS)];
    return { cas: CAS, wcag: WCAG, leviers: LEVIERS, largeur: document.documentElement.clientWidth, resultats: resultats };
  }

  function poser(r) { document.documentElement.setAttribute("data-resultat", JSON.stringify(r)); }
  lancer().then(poser, function (e) { poser({ cas: CAS, erreur: String(e && e.stack || e) }); });
})();
