// Jules - gabarit "trace-programme" : un petit programme en blocs execute pas a pas, a cote de la boite
// « memoire » de la variable x. Le curseur etape fait avancer l'execution d'une instruction ; la ligne en cours
// s'allume et la valeur de x change dans la boite (l'ancienne valeur est remplacee, pas gardee).
// Curseurs : etape (0 a 12), repetitions (tours de boucle ou appels, 1 a 5), pas_var (valeur ajoutee, 1 a 5),
// modele (0 = boucle « repeter » + test « si », 1 = programme principal qui appelle un sous-programme).
// Deroulement (les deux modeles ont la meme longueur) : etape 0 = affectation x <- 0 ; puis, pour chaque tour,
// deux etapes (ligne « repeter » / « appel », puis l'instruction « ajouter ») ; puis la derniere instruction ;
// puis « fin ». Avec repetitions = n : la boucle occupe les etapes 1 a 2n, l'instruction finale l'etape 2n + 1,
// et le programme est fini a partir de 2n + 2 (au plus tard a l'etape 12, car n <= 5).
// Faits (EX-205) : affectation, boucle « repeter n fois », instruction conditionnelle « si … alors » et
// sous-programme (bloc « definir » de Scratch) sont au programme de technologie du cycle 4 (annexe du programme,
// BO n° 31 du 30 juillet 2020, « ecrire, mettre au point et executer un programme » ; Scratch, MIT, blocs
// « repeter », « si alors », « definir »). La valeur affichee est calculee : x = (tours faits) x pas_var.
// revele : la boite ecrit la valeur finale de x, reponse d'un exercice « que vaut x a la fin ? ».
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["trace-programme"] = {
  dessiner(svg, valeurs) {
    const borne = (v, d, mini, maxi) => {
      const n = Math.round(Number(v ?? d));
      return Math.min(maxi, Math.max(mini, Number.isFinite(n) ? n : d));
    };
    const etape = borne(valeurs.etape, 0, 0, 12);
    const n = borne(valeurs.repetitions, 3, 1, 5);
    const p = borne(valeurs.pas_var, 2, 1, 5);
    const modele = borne(valeurs.modele, 0, 0, 1);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    svg.setAttribute("viewBox", "0 0 340 340");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", ORANGE = "#E07B00", VERT = "#2E7D32";

    // --- Etat de l'execution a l'etape choisie ---
    // ligne active : "init", "boucle" (repeter / appel), "ajout", "fin_instr", "fin"
    let active, tour = 0, x = 0;
    if (etape === 0) {
      active = "init";
    } else if (etape <= 2 * n) {
      tour = Math.ceil(etape / 2);
      const surAjout = etape % 2 === 0;
      active = surAjout ? "ajout" : "boucle";
      x = (surAjout ? tour : tour - 1) * p;
    } else if (etape === 2 * n + 1) {
      active = "fin_instr";
      tour = n;
      x = n * p;
    } else {
      active = "fin";
      tour = n;
      x = n * p;
    }
    const gagne = modele === 0 && x > 10;

    // --- Une ligne de programme : bloc arrondi, allume (orange) si c'est l'instruction en cours ---
    const ligne = (xg, y, largeur, texte, allume, couleurBord) => {
      el("rect", {
        x: xg, y, width: largeur, height: 30, rx: 7,
        fill: allume ? "#FFE7C2" : "#FFFFFF",
        stroke: allume ? ORANGE : (couleurBord || GRIS), "stroke-width": allume ? 4 : 2,
      });
      el("text", { x: xg + 10, y: y + 20, "font-size": 14, fill: ENCRE, "font-weight": allume ? "bold" : "normal" }, texte);
      if (allume) el("path", { d: `M${xg - 14},${y + 7} l11,8 l-11,8 z`, fill: ORANGE });
    };

    if (modele === 0) {
      el("text", { x: 20, y: 22, "font-size": 14, fill: ENCRE, "font-weight": "bold" }, "programme");
      ligne(20, 32, 230, "mettre x à 0", active === "init");
      ligne(20, 70, 230, `répéter ${n} fois`, active === "boucle", BLEU);
      // corps de la boucle, en retrait, relie par le crochet bleu de la boucle
      el("path", { d: "M28,100 v42 h14", fill: "none", stroke: BLEU, "stroke-width": 3 });
      ligne(44, 108, 206, `ajouter ${p} à x`, active === "ajout");
      ligne(20, 146, 300, "si x > 10 alors dire « gagné »", active === "fin_instr");
    } else {
      el("text", { x: 20, y: 22, "font-size": 14, fill: ENCRE, "font-weight": "bold" }, "programme principal");
      ligne(20, 32, 210, "mettre x à 0", active === "init");
      ligne(20, 70, 210, `répéter ${n} fois`, false, BLEU);
      el("path", { d: "M28,100 v42 h14", fill: "none", stroke: BLEU, "stroke-width": 3 });
      ligne(44, 108, 186, "appeler avancer", active === "boucle");
      ligne(20, 146, 210, "dire x", active === "fin_instr");
      // sous-programme, a droite, cadre vert ; fleches d'appel et de retour pendant la boucle
      el("text", { x: 248, y: 64, "font-size": 13, fill: VERT, "font-weight": "bold" }, "sous-");
      el("text", { x: 248, y: 80, "font-size": 13, fill: VERT, "font-weight": "bold" }, "programme");
      el("rect", { x: 242, y: 88, width: 92, height: 74, rx: 9, fill: "none", stroke: VERT, "stroke-width": 2, "stroke-dasharray": "6 4" });
      el("text", { x: 250, y: 106, "font-size": 13, fill: VERT }, "avancer :");
      const dedans = active === "ajout";
      el("rect", {
        x: 248, y: 114, width: 80, height: 40, rx: 7, fill: dedans ? "#FFE7C2" : "#FFFFFF",
        stroke: dedans ? ORANGE : GRIS, "stroke-width": dedans ? 4 : 2,
      });
      el("text", { x: 288, y: 130, "font-size": 13, "text-anchor": "middle", fill: ENCRE, "font-weight": dedans ? "bold" : "normal" }, `ajouter ${p}`);
      el("text", { x: 288, y: 147, "font-size": 13, "text-anchor": "middle", fill: ENCRE, "font-weight": dedans ? "bold" : "normal" }, "à x");
      if (active === "boucle" || dedans) {
        // aller (appel) en haut, retour en bas : la fleche de l'etape en cours est pleine
        const fl = (y, versDroite, plein) => {
          const x1 = versDroite ? 232 : 246, x2 = versDroite ? 246 : 232;
          el("line", { x1, y1: y, x2, y2: y, stroke: ORANGE, "stroke-width": 3, "stroke-dasharray": plein ? "none" : "3 3" });
          el("path", { d: versDroite ? `M248,${y} l-8,-6 v12 z` : `M230,${y} l8,-6 v12 z`, fill: ORANGE });
        };
        fl(118, true, active === "boucle");
        fl(136, false, dedans);
      }
    }

    // --- Compteur de tours ---
    const motTour = modele === 0 ? "tour" : "appel";
    let compteur;
    if (active === "init") compteur = "avant la boucle";
    else if (active === "boucle" || active === "ajout") compteur = `${motTour} ${tour} sur ${n}`;
    else compteur = "boucle finie";
    el("text", { x: 20, y: 204, "font-size": 14, fill: BLEU, "font-weight": "bold" }, compteur);
    // petites cases : un carre par tour, plein quand le tour est commence
    for (let i = 1; i <= n; i++) {
      const fait = i <= tour && active !== "init";
      el("rect", { x: 20 + (i - 1) * 26, y: 214, width: 20, height: 20, rx: 4, fill: fait ? BLEU : "#FFFFFF", stroke: BLEU, "stroke-width": 2 });
    }

    // --- Boite memoire : une seule case, une seule valeur ---
    el("text", { x: 250, y: 204, "font-size": 14, "text-anchor": "middle", fill: ENCRE, "font-weight": "bold" }, "mémoire");
    el("rect", { x: 200, y: 212, width: 100, height: 62, rx: 8, fill: "#EEF3FA", stroke: BLEU, "stroke-width": 3 });
    el("text", { x: 214, y: 250, "font-size": 18, fill: GRIS, "font-weight": "bold" }, "x");
    el("text", { x: 262, y: 256, "font-size": 30, "text-anchor": "middle", fill: BLEU, "font-weight": "bold" }, String(x));

    // --- Sortie du programme et etat ---
    if (active === "fin_instr" || active === "fin") {
      let message;
      if (modele === 1) message = `affiche ${x}`;
      else message = gagne ? "dit « gagné »" : "ne dit rien (x ≤ 10)";
      el("text", { x: 20, y: 300, "font-size": 14, fill: gagne || modele === 1 ? VERT : GRIS, "font-weight": "bold" }, `le lutin ${message}`);
    }
    el("text", { x: 20, y: 328, "font-size": 13, fill: GRIS }, active === "fin" ? "programme terminé" : `étape ${etape}`);
    return { x, tour, ligne: active };
  },
};
