// Jules - page d'accueil « Mes fiches » : rail a gauche (notions), fiche visuelle au centre,
// Jules en bulles preecrites a droite (aucun appel IA sur cette page : voir jules_cadrage_interface.md).
"use strict";

(() => {
  const $ = (id) => document.getElementById(id);

  const etat = {
    infos: null,
    notions: [],
    notionActive: null,
    fiche: null,
    bulles: [],
  };

  // --- rail : liste des notions qui ont une fiche visuelle ------------------
  async function chargerNotions() {
    const zone = $("rail-notions");
    zone.innerHTML = "";
    let matieres = [];
    try {
      const r = await MS.api("/api/eleve/fiches_visuelles/notions");
      matieres = r.matieres || [];
    } catch (err) {
      zone.appendChild(creer("p", "avertissement", `Impossible de charger tes fiches : ${err.message}`));
      return;
    }
    etat.notions = [];
    for (const m of matieres) {
      const titre = document.createElement("h4");
      titre.textContent = m.nom;
      zone.appendChild(titre);
      for (const n of m.notions) {
        etat.notions.push(n);
        const bouton = document.createElement("button");
        bouton.type = "button";
        bouton.dataset.id = n.id;
        bouton.textContent = n.titre;
        bouton.addEventListener("click", () => ouvrirFiche(n.id));
        zone.appendChild(bouton);
      }
    }
  }

  // Texte d'une fiche ou les notions cles sont marquees **ainsi** (controle cote serveur : peu nombreuses,
  // courtes). Jamais d'innerHTML : noeuds texte et <strong> crees un par un.
  function ecrireRiche(el, texte) {
    String(texte || "").split(/\*\*(.+?)\*\*/).forEach((morceau, i) => {
      if (!morceau) return;
      if (i % 2) el.appendChild(creer("strong", "cle", morceau));
      else el.appendChild(document.createTextNode(morceau));
    });
    return el;
  }

  function creerRiche(balise, classe, texte) {
    return ecrireRiche(creer(balise, classe), texte);
  }

  function creer(balise, classe, texte) {
    const el = document.createElement(balise);
    if (classe) el.className = classe;
    if (texte !== undefined) el.textContent = texte;
    return el;
  }

  function marquerNotionActive() {
    for (const b of $("rail-notions").querySelectorAll("button")) {
      b.classList.toggle("actif", etat.notionActive && b.dataset.id === etat.notionActive);
    }
  }

  // --- ouverture d'une fiche -------------------------------------------------
  async function ouvrirFiche(notionId) {
    $("fiche-vide").classList.add("cache");
    $("fiche").classList.add("cache");
    $("fiche-erreur").classList.add("cache");
    $("fiche-attente").classList.remove("cache");
    fermerRail();
    try {
      const fiche = await MS.api(`/api/eleve/fiches_visuelles/notions/${encodeURIComponent(notionId)}`);
      etat.fiche = fiche;
      etat.notionActive = notionId;
      marquerNotionActive();
      // Rappels au survol propres a la notion (lettres, abreviations : symboles.js), fiche et bulles.
      if (typeof Symboles !== "undefined") {
        const rappels = { matiere: fiche.matiere, variables: fiche.variables, abreviations: fiche.abreviations };
        Symboles.contexte($("fiche"), rappels);
        Symboles.contexte($("bulles"), rappels);
      }
      afficherFiche(fiche);
      $("fiche").classList.remove("cache");
      // Nouvelle fiche : on repart de son titre, pas de la position de defilement de la precedente.
      document.querySelector(".fiche-zone").scrollTop = 0;
      window.scrollTo(0, 0);
      $("chat-flottant-notion").textContent = " · " + fiche.titre;
      $("chat-flottant-lien").href = `/discuter?notion=${encodeURIComponent(notionId)}`;
    } catch (err) {
      $("fiche-erreur").textContent = `Impossible d'ouvrir cette fiche : ${err.message}`;
      $("fiche-erreur").classList.remove("cache");
    } finally {
      $("fiche-attente").classList.add("cache");
    }
  }

  function afficherFiche(fiche) {
    $("fiche-fil").textContent = `${fiche.nom_matiere} › ${fiche.niveau}`;
    $("fiche-titre").textContent = fiche.titre;
    if (fiche.relecture_a_relire) {
      $("fiche-avertissement").textContent =
        "Fiche expérimentale, pas encore relue par un adulte : sers-t'en comme appui, pas comme vérité absolue.";
      $("fiche-avertissement").classList.remove("cache");
    } else {
      $("fiche-avertissement").classList.add("cache");
    }
    const blocsFiche = fiche.blocs || [];
    const blocAttendus = blocsFiche.find((b) => b.type === "attendus");
    const zoneAttendus = $("fiche-attendus");
    zoneAttendus.innerHTML = "";
    (blocAttendus ? blocAttendus.attendus || [] : []).forEach((a, i) => {
      const span = document.createElement("span");
      span.className = "fiche-attendu";
      const b = document.createElement("b");
      b.textContent = `Attendu ${i + 1} `;
      span.appendChild(b);
      span.appendChild(document.createTextNode(a));
      zoneAttendus.appendChild(span);
    });
    const zoneBlocs = $("fiche-blocs");
    zoneBlocs.innerHTML = "";
    for (const bloc of blocsFiche) {
      if (bloc.type === "attendus") continue;
      zoneBlocs.appendChild(construireBloc(bloc));
    }
    const sources = (fiche.sources || []).map((s) => s.titre).join(" · ");
    $("fiche-sources").textContent = sources ? `Sources : ${sources} (${fiche.licence})` : "";
  }

  // --- construction des 8 types de blocs -------------------------------------
  function construireBloc(bloc) {
    const section = document.createElement("section");
    section.className = "fiche-bloc";
    section.dataset.adresse = `fiche/${bloc.id}`;
    const titre = document.createElement("h2");
    titre.textContent = bloc.titre || TITRES_TYPE[bloc.type] || bloc.type;
    section.appendChild(titre);

    const constructeur = CONSTRUCTEURS[bloc.type];
    if (constructeur) section.appendChild(constructeur(bloc));

    section.addEventListener("click", (evenement) => activerBloc(section, bloc, evenement.target));
    return section;
  }

  const TITRES_TYPE = {
    formule: "L'essentiel en une ligne",
    carte: "Comment les notions s'articulent",
    graphe: "Vois la notion bouger",
    methode: "La méthode, étape par étape",
    piege: "Le piège classique",
    exemple: "Dans la vraie vie",
    renfort: "Ensuite, pour ancrer",
    schema: "Un schéma pour s'y retrouver",
  };

  // Couleurs declarees dans les fiches (mots francais) -> couleurs CSS fixes. Inconnu -> bleu Jules.
  const COULEURS = { bleu: "#1D4E89", orange: "#D9480F", vert: "#2B8A3E", rouge: "#C92A2A", violet: "#7048E8", gris: "#6B7686" };
  function couleurCss(nom) {
    return COULEURS[nom] || "#1D4E89";
  }

  const CONSTRUCTEURS = {
    formule(bloc) {
      const div = creer("div", "bloc-formule");
      const expr = creer("div", "formule-expression");
      // "[a]" dans l'expression = terme colore (couleur declaree dans termes) ; le reste en texte brut.
      const termesDecl = bloc.termes || {};
      for (const morceau of String(bloc.expression || "").split(/(\[[^\]]+\])/)) {
        const m = morceau.match(/^\[([^\]]+)\]$/);
        if (m) {
          const span = document.createElement("span");
          span.textContent = m[1];
          span.style.color = couleurCss((termesDecl[m[1]] || {}).couleur);
          span.style.fontWeight = "700";
          expr.appendChild(span);
        } else if (morceau) {
          expr.appendChild(document.createTextNode(morceau));
        }
      }
      div.appendChild(expr);
      const termes = creer("div", "formule-termes");
      for (const [nom, info] of Object.entries(bloc.termes || {})) {
        const ligne = document.createElement("div");
        ligne.style.borderColor = couleurCss(info.couleur);
        const b = document.createElement("b");
        b.textContent = nom + " ";
        b.style.color = couleurCss(info.couleur);
        ligne.appendChild(b);
        ecrireRiche(ligne, info.legende);
        termes.appendChild(ligne);
      }
      div.appendChild(termes);
      return div;
    },

    carte(bloc) {
      const div = creer("div", "bloc-carte");
      const svgns = "http://www.w3.org/2000/svg";
      const svg = document.createElementNS(svgns, "svg");
      svg.setAttribute("role", "img");
      svg.setAttribute("aria-label", "Carte des notions");
      const noeuds = bloc.noeuds || [];
      const secondaires = noeuds.filter((n) => !n.principal);
      const g = (nom, attrs) => {
        const e = document.createElementNS(svgns, nom);
        for (const k in attrs) e.setAttribute(k, attrs[k]);
        return e;
      };
      // Texte coupe en lignes selon la largeur de la boite (estimation : un caractere ~ 0,58 em).
      const lignes = (texte, largeur, taille) => {
        const max = Math.max(8, Math.floor(largeur / (taille * 0.58)));
        const sortie = [];
        let courante = "";
        for (const mot of String(texte || "").split(/\s+/).filter(Boolean)) {
          if (courante && (courante + " " + mot).length > max) { sortie.push(courante); courante = mot; }
          else courante = courante ? courante + " " + mot : mot;
        }
        if (courante) sortie.push(courante);
        return sortie;
      };
      const T_TITRE = 16, T_SOUS = 14, T_LIEN = 13, H_TITRE = 20, H_SOUS = 18;
      // Jusqu'a 4 notions : en eventail sous le noeud principal. Au-dela : le principal a gauche et
      // les notions en colonne a droite, pour que rien ne se chevauche (2 a 8 noeuds permis).
      const enColonne = secondaires.length > 4;
      const largeur = (n) => (enColonne ? (n.principal ? 230 : 380) : n.principal ? 260 : Math.min(220, 860 / Math.max(secondaires.length, 1) - 16));
      const contenu = new Map();
      for (const n of noeuds) {
        const l = largeur(n) - 20;
        const titre = lignes(n.titre, l, T_TITRE), sous = n.sous_titre ? lignes(n.sous_titre, l, T_SOUS) : [];
        contenu.set(n.id, { titre, sous, hauteur: 22 + titre.length * H_TITRE + sous.length * H_SOUS });
      }
      const hMax = Math.max(...secondaires.map((n) => contenu.get(n.id).hauteur), 56);
      const positions = new Map();
      let hauteurTotale;
      if (enColonne) {
        const pasY = hMax + 18;
        hauteurTotale = secondaires.length * pasY + 10;
        secondaires.forEach((n, i) => positions.set(n.id, { x: 650, y: 10 + pasY * i + pasY / 2 }));
        noeuds.filter((n) => n.principal).forEach((n) => positions.set(n.id, { x: 125, y: hauteurTotale / 2 }));
      } else {
        const hPrincipal = Math.max(...noeuds.filter((n) => n.principal).map((n) => contenu.get(n.id).hauteur), 56);
        const pas = 860 / Math.max(secondaires.length, 1);
        const yBas = hPrincipal + 130 + hMax / 2;
        hauteurTotale = yBas + hMax / 2 + 6;
        noeuds.filter((n) => n.principal).forEach((n) => positions.set(n.id, { x: 430, y: 4 + hPrincipal / 2 }));
        secondaires.forEach((n, i) => positions.set(n.id, { x: pas * i + pas / 2, y: yBas }));
      }
      // Un lien entre deux notions du meme rang passerait sous les boites (et son libelle avec) :
      // il fait un coude, sous la ligne (disposition en eventail) ou a droite de la colonne.
      const principaux = new Set(noeuds.filter((n) => n.principal).map((n) => n.id));
      const lateraux = (bloc.liens || []).filter((l) => !principaux.has(l.de) && !principaux.has(l.vers) && positions.has(l.de) && positions.has(l.vers));
      const largeurTotale = enColonne && lateraux.length ? 1000 : 860;
      if (!enColonne && lateraux.length) hauteurTotale += 22 + 26 * lateraux.length;
      svg.setAttribute("viewBox", `0 0 ${largeurTotale} ${Math.ceil(hauteurTotale)}`);
      const boite = (n) => {
        const pos = positions.get(n.id), h = n.principal ? contenu.get(n.id).hauteur : hMax, w = largeur(n);
        return { gauche: pos.x - w / 2, droite: pos.x + w / 2, haut: pos.y - h / 2, bas: pos.y + h / 2 };
      };
      for (const lien of bloc.liens || []) {
        const a = noeuds.find((n) => n.id === lien.de), b = noeuds.find((n) => n.id === lien.vers);
        if (!a || !b || !positions.has(a.id) || !positions.has(b.id)) continue;
        const pa = positions.get(a.id), pb = positions.get(b.id), ba = boite(a), bb = boite(b);
        const libelle = (x, y, ancre = "middle") => {
          if (!lien.libelle) return;
          const texte = g("text", { x, y, "font-size": T_LIEN, fill: "#4A5566", "text-anchor": ancre, "paint-order": "stroke", stroke: "#FFFFFF", "stroke-width": 5 });
          texte.textContent = lien.libelle;
          svg.appendChild(texte);
        };
        const rang = lateraux.indexOf(lien);
        if (rang >= 0) {  // coude entre deux notions du meme rang
          if (enColonne) {
            const x = ba.droite + 24 + 14 * rang;
            svg.appendChild(g("polyline", { points: `${ba.droite},${pa.y} ${x},${pa.y} ${x},${pb.y} ${bb.droite},${pb.y}`, fill: "none", stroke: "#8A94A3", "stroke-width": 2 }));
            libelle(x + 6, (pa.y + pb.y) / 2 + 4, "start");
          } else {
            const y = Math.max(ba.bas, bb.bas) + 14 + 26 * rang;
            svg.appendChild(g("polyline", { points: `${pa.x},${ba.bas} ${pa.x},${y} ${pb.x},${y} ${pb.x},${bb.bas}`, fill: "none", stroke: "#8A94A3", "stroke-width": 2 }));
            libelle((pa.x + pb.x) / 2, y + 16);
          }
          continue;
        }
        let x1, y1, x2, y2;
        if (enColonne) {  // du bord droit de l'un au bord gauche de l'autre
          [x1, y1, x2, y2] = pa.x < pb.x ? [ba.droite, pa.y, bb.gauche, pb.y] : [ba.gauche, pa.y, bb.droite, pb.y];
        } else if (pa.y === pb.y) {  // meme ligne : bords lateraux
          [x1, y1, x2, y2] = pa.x < pb.x ? [ba.droite, pa.y, bb.gauche, pb.y] : [ba.gauche, pa.y, bb.droite, pb.y];
        } else {  // bas du noeud du haut vers le haut du noeud du bas
          [x1, y1, x2, y2] = pa.y < pb.y ? [pa.x, ba.bas, pb.x, bb.haut] : [pa.x, ba.haut, pb.x, bb.bas];
        }
        svg.appendChild(g("line", { x1, y1, x2, y2, stroke: "#8A94A3", "stroke-width": 2 }));
        if (lien.libelle) {
          // Un peu plus pres de l'arrivee : les libelles s'ecartent. Entre deux boites d'une meme ligne,
          // le libelle passe au-dessus des boites (l'espace entre elles est trop etroit).
          const t = enColonne ? 0.62 : 0.55, memeLigne = !enColonne && pa.y === pb.y;
          const yLibelle = memeLigne ? Math.min(ba.haut, bb.haut) - 8 : y1 + (y2 - y1) * t - 6;
          const texte = g("text", { x: x1 + (x2 - x1) * t, y: yLibelle, "font-size": T_LIEN, fill: "#4A5566", "text-anchor": "middle", "paint-order": "stroke", stroke: "#FFFFFF", "stroke-width": 5 });
          texte.textContent = lien.libelle;
          svg.appendChild(texte);
        }
      }
      for (const n of noeuds) {
        const pos = positions.get(n.id), c = contenu.get(n.id), b = boite(n);
        const groupe = g("g", { class: "carte-noeud", "data-adresse": `carte/${n.id}` });
        groupe.appendChild(g("rect", {
          x: b.gauche, y: b.haut, width: b.droite - b.gauche, height: b.bas - b.haut,
          rx: 14, fill: n.principal ? "#1F4E8C" : "#EAF1FA", stroke: n.principal ? "#1F4E8C" : "#B7C8DE",
        }));
        let y = pos.y - (c.titre.length * H_TITRE + c.sous.length * H_SOUS) / 2 + 15;
        for (const l of c.titre) {
          const e = g("text", { x: pos.x, y, "font-size": T_TITRE, "font-weight": 700, "text-anchor": "middle", class: "carte-titre", fill: n.principal ? "#FFFFFF" : "#14243B" });
          e.textContent = l;
          groupe.appendChild(e);
          y += H_TITRE;
        }
        for (const l of c.sous) {
          const e = g("text", { x: pos.x, y: y + 1, "font-size": T_SOUS, "text-anchor": "middle", fill: n.principal ? "#DBE7F5" : "#4A5566" });
          e.textContent = l;
          groupe.appendChild(e);
          y += H_SOUS;
        }
        svg.appendChild(groupe);
      }
      div.appendChild(svg);
      return div;
    },

    graphe(bloc) {
      const div = creer("div", "bloc-graphe");
      const svgns = "http://www.w3.org/2000/svg";
      const svg = document.createElementNS(svgns, "svg");
      svg.setAttribute("class", "figure");
      svg.setAttribute("role", "img");
      svg.setAttribute("aria-label", "Figure interactive");
      div.appendChild(svg);

      const reglages = creer("div", "curseur-bloc-conteneur");
      const valeurs = {};
      const curseurs = bloc.curseurs || [];
      const champsValeur = {};
      for (const c of curseurs) {
        valeurs[c.nom] = Number(c.depart ?? c.min ?? 0);
        const zone = creer("div", "curseur-bloc");
        const label = document.createElement("label");
        const spanValeur = creer("span");
        spanValeur.textContent = String(valeurs[c.nom]).replace(".", ",");
        champsValeur[c.nom] = spanValeur;
        label.textContent = `${c.nom} = `;
        label.appendChild(spanValeur);
        zone.appendChild(label);
        const input = document.createElement("input");
        input.type = "range";
        input.min = String(c.min);
        input.max = String(c.max);
        input.step = String(c.pas ?? 1);
        input.value = String(valeurs[c.nom]);
        input.dataset.adresse = `graphe/${c.id}`;
        input.addEventListener("input", () => {
          valeurs[c.nom] = Number(input.value);
          champsValeur[c.nom].textContent = input.value.replace(".", ",");
          redessiner();
        });
        zone.appendChild(input);
        reglages.appendChild(zone);
      }
      const lecture = creer("div", "lecture-graphe");
      reglages.appendChild(lecture);
      div.appendChild(reglages);

      function redessiner() {
        const gabarit = window.GABARITS && window.GABARITS[bloc.gabarit];
        if (gabarit) gabarit.dessiner(svg, valeurs);
        lecture.innerHTML = ""; // vide la zone (aucune donnee inseree ici) ; les <p> suivants sont crees via createElement puis textContent
        for (const l of bloc.lectures || []) {
          if (evaluerCondition(l.si, valeurs)) {
            const p = document.createElement("p");
            p.style.margin = "0 0 6px";
            ecrireRiche(p, l.texte);
            lecture.appendChild(p);
          }
        }
      }
      redessiner();
      return div;
    },

    methode(bloc) {
      const ol = document.createElement("ol");
      ol.className = "methode-etapes";
      (bloc.etapes || []).forEach((etape, i) => {
        const li = document.createElement("li");
        const num = creer("span", "methode-num", String(i + 1));
        li.appendChild(num);
        const texte = document.createElement("div");
        ecrireRiche(texte, etape);
        li.appendChild(texte);
        ol.appendChild(li);
      });
      return ol;
    },

    piege(bloc) {
      const div = creer("div", "bloc-piege");
      const mauvais = creer("div", "piege-non");
      ecrireRiche(mauvais, "✗ " + (bloc.mauvaise_idee || ""));
      div.appendChild(mauvais);
      const bon = creer("div", "piege-oui");
      ecrireRiche(bon, "✓ " + (bloc.bonne_idee || ""));
      div.appendChild(bon);
      if (bloc.pourquoi_faux) {
        const pourquoi = creerRiche("p", "muet", bloc.pourquoi_faux);
        pourquoi.style.gridColumn = "1 / -1";
        div.appendChild(pourquoi);
      }
      return div;
    },

    exemple(bloc) {
      const div = creer("div", "bloc-exemple");
      if (bloc.situation) div.appendChild(creerRiche("p", null, bloc.situation));
      if (bloc.calcul) div.appendChild(creerRiche("p", null, bloc.calcul));
      if (bloc.figure) {
        const svgns = "http://www.w3.org/2000/svg";
        const svg = document.createElementNS(svgns, "svg");
        svg.setAttribute("class", "figure");
        svg.setAttribute("width", "300");
        svg.setAttribute("height", "180");
        div.appendChild(svg);
        const gabarit = window.GABARITS && window.GABARITS[bloc.figure.gabarit];
        if (gabarit) {
          const valeurs = {};
          for (const c of bloc.figure.curseurs || []) valeurs[c.nom] = c.depart;
          gabarit.dessiner(svg, valeurs);
        }
      }
      if (bloc.conclusion) div.appendChild(creerRiche("p", "exemple-conclusion", bloc.conclusion));
      return div;
    },

    renfort(bloc) {
      const div = creer("div", "renfort-tuiles");
      for (const lien of bloc.liens || []) {
        const tuile = creer("div", "renfort-tuile");
        const icone = creer("span", "icone", lien.icone || "🔧");
        tuile.appendChild(icone);
        tuile.appendChild(document.createTextNode(lien.titre || ""));
        if (lien.description) tuile.appendChild(creer("small", null, lien.description));
        div.appendChild(tuile);
      }
      return div;
    },

    // Le SVG a deja ete nettoye cote serveur par liste blanche (jules/svg_sur.py, jamais de
    // <script>, de gestionnaire on*, ni de lien externe). On l'importe par DOMParser + import de
    // noeuds plutot que innerHTML : chaque noeud est verifie par le parseur XML du navigateur et
    // seuls les noeuds du document XML sont copies, jamais une chaine executee telle quelle.
    schema(bloc) {
      const div = creer("div", "bloc-schema");
      const analyseur = new DOMParser();
      const document_svg = analyseur.parseFromString(String(bloc.svg || ""), "image/svg+xml");
      const racine = document_svg.documentElement;
      if (racine && racine.tagName === "svg" && !document_svg.querySelector("parsererror")) {
        // Le SVG nettoye n'a plus d'attribut "height" fixe (garde sa taille responsive) : le
        // navigateur calcule alors sa hauteur a partir du ratio naturel du viewBox, sans besoin
        // de fixer nous-memes un style — a condition de ne pas forcer "height: auto" en CSS.
        div.appendChild(document.importNode(racine, true));
      } else {
        div.appendChild(creer("p", "avertissement", "Schéma illisible."));
      }
      return div;
    },
  };

  // Petit evaluateur SUR de "si" (le serveur a deja valide la syntaxe, mais on revalide ici :
  // jamais d'eval() cote client non plus). Grammaire : (variable operateur nombre) (&& ...)*
  function evaluerCondition(expression, valeurs) {
    if (!expression) return false;
    return String(expression).split("&&").every((partie) => {
      const m = partie.trim().match(/^([a-zA-Z_][a-zA-Z0-9_]*)\s*(<=|>=|==|!=|<|>)\s*(-?\d+(?:\.\d+)?)$/);
      if (!m) return false;
      const [, variable, operateur, nombreTexte] = m;
      const valeur = valeurs[variable];
      const nombre = Number(nombreTexte);
      if (valeur === undefined) return false;
      switch (operateur) {
        case "<": return valeur < nombre;
        case "<=": return valeur <= nombre;
        case ">": return valeur > nombre;
        case ">=": return valeur >= nombre;
        case "==": return valeur === nombre;
        case "!=": return valeur !== nombre;
        default: return false;
      }
    });
  }

  // --- Jules : bulles preecrites, 2 maximum, la plus ancienne s'estompe -----
  function activerBloc(section, bloc, cible) {
    document.querySelectorAll(".fiche-bloc.actif").forEach((b) => b.classList.remove("actif"));
    section.classList.add("actif");
    if (bloc.jules) ajouterBulle(bloc.jules);
    // Point d'accroche « bloc_consulte » des extensions : l'adresse la plus precise touchee (un
    // noeud de carte, un curseur) ou, a defaut, celle du bloc. Rien n'est attendu en retour.
    const cibleAdresse = cible && cible.closest ? cible.closest("[data-adresse]") : null;
    signalerBlocConsulte((cibleAdresse || section).dataset.adresse);
  }

  function signalerBlocConsulte(adresse) {
    if (!adresse) return;
    MS.api("/api/seance/bloc_consulte", MS.json({ adresse, notion: etat.notionActive })).catch(() => {});
  }

  // Une seule bulle a la fois : une nouvelle explication remplace la precedente. Elle reste le temps
  // de la lire (plus longue si le texte est long, en pause tant que la souris est dessus), puis
  // s'efface completement ; un clic la ferme tout de suite.
  let minuterieBulle = null;
  function ajouterBulle(texte) {
    const pile = $("bulles");
    clearTimeout(minuterieBulle);
    pile.replaceChildren();
    const bulle = creerRiche("div", "bulle-jules", texte);
    bulle.title = "Clique pour fermer";
    pile.appendChild(bulle);
    const fermer = () => {
      clearTimeout(minuterieBulle);
      bulle.classList.add("sortie");
      setTimeout(() => bulle.remove(), 400);
    };
    const armer = () => {
      clearTimeout(minuterieBulle);
      minuterieBulle = setTimeout(fermer, Math.min(20000, 6000 + 60 * String(texte).length));
    };
    bulle.addEventListener("click", fermer);
    bulle.addEventListener("mouseenter", () => clearTimeout(minuterieBulle));
    bulle.addEventListener("mouseleave", armer);
    armer();
  }


  function fermerRail() {
    $("rail").classList.remove("ouvert");
    $("menu-rail").classList.remove("cache");
  }

  function basculerChat(ouvrir) {
    const c = $("chat-flottant");
    const o = ouvrir === undefined ? !c.classList.contains("ouvert") : ouvrir;
    c.classList.toggle("ouvert", o);
  }

  async function demarrage() {
    await MS.porte("eleve", { porte: $("porte"), contenu: $("contenu"), formulaire: $("porte-form"), champ: $("porte-code"), erreur: $("porte-erreur") });
    etat.infos = await MS.api("/api/infos");
    MS.appliquerCouleurs(etat.infos.persona.couleurs);
    document.title = etat.infos.persona.nom + " - Mes fiches";
    $("nom-persona").textContent = etat.infos.persona.nom;
    $("menu-rail").addEventListener("click", () => {
      $("rail").classList.toggle("ouvert");
      $("menu-rail").classList.toggle("cache", $("rail").classList.contains("ouvert"));
    });
    MS.signalerFinDeSeance();
    $("avatar-jules").addEventListener("click", () => basculerChat());
    $("chat-flottant-reduire").addEventListener("click", () => basculerChat(false));
    ajouterBulle("Clique sur un bloc de la fiche : je t'explique ce qu'il faut en retenir.");
    await chargerNotions();
    // Lien direct vers une fiche : /#<identifiant de la notion> ; sinon la premiere de la liste.
    const demandee = decodeURIComponent(location.hash.slice(1));
    const aOuvrir = etat.notions.find((n) => n.id === demandee) || etat.notions[0];
    if (aOuvrir) ouvrirFiche(aOuvrir.id);
  }

  demarrage().catch((err) => {
    document.body.innerHTML = `<p class="erreur-page">Erreur : ${MS.echapper(err.message)}</p>`;
  });
})();
