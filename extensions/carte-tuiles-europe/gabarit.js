// Jules - gabarit "carte-tuiles-europe" : l'Europe en carres (un carre par pays, a peu pres a sa place). Une couche
// choisie par le curseur « couche » colorie les pays membres d'un ensemble a l'annee choisie par « annee » ; la
// France est encadree. Les pays qui entrent l'annee choisie ont un contour epais ; un pays sorti (Royaume-Uni de l'UE
// en 2020, Russie du Conseil de l'Europe en 2022) garde un contour pointille de la couleur de la couche.
//   couche 1  Communautes europeennes puis Union europeenne (CECA 1951, CEE 1957, UE depuis Maastricht, en vigueur
//             le 1er novembre 1993) : 1951 les six fondateurs ; 1973 Royaume-Uni, Irlande, Danemark ; 1981 Grece ;
//             1986 Espagne, Portugal ; 1995 Autriche, Finlande, Suede ; 2004 Chypre, Estonie, Hongrie, Lettonie,
//             Lituanie, Malte, Pologne, Rep. tcheque, Slovaquie, Slovenie ; 2007 Bulgarie, Roumanie ; 2013 Croatie ;
//             sortie du Royaume-Uni le 31 janvier 2020. Source : programme d'histoire de 3e et fiche
//             « etapes-construction-europeenne » de la bibliotheque ; dates d'adhesion : site de l'UE (european-union).
//   couche 2  zone euro (monnaie a partir du 1er janvier de l'annee indiquee ; pieces et billets en 2002) : 1999
//             onze pays ; 2001 Grece ; 2007 Slovenie ; 2008 Chypre, Malte ; 2009 Slovaquie ; 2011 Estonie ;
//             2014 Lettonie ; 2015 Lituanie ; 2023 Croatie ; 2026 Bulgarie (21e pays, The Conversation et
//             Commission europeenne, « La Bulgarie adopte l'euro a compter du 1er janvier 2026 »).
//   couche 3  espace Schengen (suppression des controles, Ministere federal allemand des Affaires etrangeres,
//             « Accord de Schengen », et Touteleurope) : 1995 Allemagne, Belgique, Espagne, France, Luxembourg,
//             Pays-Bas, Portugal ; 1997 Italie, Autriche ; 2000 Grece ; 2001 Danemark, Finlande, Islande, Norvege,
//             Suede ; 2007 (21 decembre) neuf pays de 2004 sauf Chypre ; 2008 Suisse ; 2011 Liechtenstein ;
//             2023 Croatie ; 2025 Bulgarie, Roumanie (frontieres terrestres) : 29 pays.
//   couche 4  Conseil de l'Europe (1949, Strasbourg, Cour europeenne des droits de l'homme) : dates d'adhesion de
//             la liste officielle du Conseil (article « Member states of the Council of Europe ») ; Grece sortie de
//             1969 a 1974 ; Russie membre de 1996 au 16 mars 2022 (exclue) : 46 Etats aujourd'hui.
// Le Kosovo, le Vatican et la Bielorussie (membre d'aucun des quatre ensembles) : seule la Bielorussie est dessinee,
// en gris, pour montrer qu'un pays d'Europe peut n'appartenir a aucun.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["carte-tuiles-europe"] = {
  dessiner(svg, valeurs) {
    const NS = "http://www.w3.org/2000/svg";
    const BLEU = "#1F4E8C", GRIS = "#6B7686", ENCRE = "#14243B", VERT = "#2E7D32", ORANGE = "#E07B00";
    const VIDE = "#D5DAE1";
    const nombre = (v, d) => (Number.isFinite(Number(v)) ? Number(v) : d);
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };

    // code : [colonne, ligne, nom]
    const PAYS = {
      IS: [0, 0, "Islande"], NO: [5, 0, "Norvège"], SE: [6, 0, "Suède"], FI: [7, 0, "Finlande"], EE: [8, 0, "Estonie"],
      IE: [1, 1, "Irlande"], UK: [2, 1, "Royaume-Uni"], DK: [5, 1, "Danemark"], LV: [8, 1, "Lettonie"], RU: [9, 1, "Russie"],
      NL: [4, 2, "Pays-Bas"], DE: [5, 2, "Allemagne"], PL: [6, 2, "Pologne"], LT: [7, 2, "Lituanie"], BY: [8, 2, "Biélorussie"],
      BE: [3, 3, "Belgique"], LU: [4, 3, "Luxembourg"], CZ: [5, 3, "Tchéquie"], SK: [6, 3, "Slovaquie"], UA: [7, 3, "Ukraine"],
      FR: [2, 4, "France"], CH: [3, 4, "Suisse"], LI: [4, 4, "Liechtenstein"], AT: [5, 4, "Autriche"], HU: [6, 4, "Hongrie"],
      RO: [7, 4, "Roumanie"], MD: [8, 4, "Moldavie"],
      PT: [0, 5, "Portugal"], ES: [1, 5, "Espagne"], AD: [2, 5, "Andorre"], MC: [3, 5, "Monaco"], IT: [4, 5, "Italie"],
      SI: [5, 5, "Slovénie"], HR: [6, 5, "Croatie"], RS: [7, 5, "Serbie"], BG: [8, 5, "Bulgarie"], GE: [9, 5, "Géorgie"],
      AZ: [10, 5, "Azerbaïdjan"],
      SM: [4, 6, "Saint-Marin"], BA: [5, 6, "Bosnie"], ME: [6, 6, "Monténégro"], MK: [7, 6, "Macédoine du Nord"],
      TR: [8, 6, "Turquie"], AM: [9, 6, "Arménie"],
      MT: [4, 7, "Malte"], AL: [6, 7, "Albanie"], GR: [7, 7, "Grèce"], CY: [9, 7, "Chypre"],
    };
    const groupe = (liste, debut, fin) => Object.fromEntries(liste.split(" ").map((c) => [c, [[debut, fin]]]));
    const COUCHES = {
      1: {
        couleur: BLEU,
        nom: (an) => (an < 1957 ? "CECA" : an < 1993 ? "CEE" : "Union européenne"),
        membres: {
          ...groupe("FR DE IT BE NL LU", 1951, 9999), ...groupe("IE DK", 1973, 9999), UK: [[1973, 2019]],
          ...groupe("GR", 1981, 9999), ...groupe("ES PT", 1986, 9999), ...groupe("AT FI SE", 1995, 9999),
          ...groupe("CY EE HU LV LT MT PL CZ SK SI", 2004, 9999), ...groupe("BG RO", 2007, 9999),
          ...groupe("HR", 2013, 9999),
        },
        avant: [1951, "pas encore de Communauté (CECA, 1951)"],
      },
      2: {
        couleur: ORANGE,
        nom: () => "zone euro",
        membres: {
          ...groupe("AT BE DE ES FI FR IE IT LU NL PT", 1999, 9999), ...groupe("GR", 2001, 9999),
          ...groupe("SI", 2007, 9999), ...groupe("CY MT", 2008, 9999), ...groupe("SK", 2009, 9999),
          ...groupe("EE", 2011, 9999), ...groupe("LV", 2014, 9999), ...groupe("LT", 2015, 9999),
          ...groupe("HR", 2023, 9999), ...groupe("BG", 2026, 9999),
        },
        avant: [1999, "l'euro n'existe pas encore (1999)"],
      },
      3: {
        couleur: VERT,
        nom: () => "espace Schengen",
        membres: {
          ...groupe("DE BE ES FR LU NL PT", 1995, 9999), ...groupe("IT AT", 1997, 9999), ...groupe("GR", 2000, 9999),
          ...groupe("DK FI IS NO SE", 2001, 9999), ...groupe("EE HU LV LT MT PL CZ SK SI", 2007, 9999),
          ...groupe("CH", 2008, 9999), ...groupe("LI", 2011, 9999), ...groupe("HR", 2023, 9999),
          ...groupe("BG RO", 2025, 9999),
        },
        avant: [1995, "pas encore d'espace Schengen (1995)"],
      },
      4: {
        couleur: ENCRE,
        nom: () => "Conseil de l'Europe",
        membres: {
          ...groupe("BE DK FR IE IT LU NL NO SE UK", 1949, 9999), GR: [[1949, 1969], [1974, 9999]],
          ...groupe("IS TR DE", 1950, 9999), ...groupe("AT", 1956, 9999), ...groupe("CY", 1961, 9999),
          ...groupe("CH", 1963, 9999), ...groupe("MT", 1965, 9999), ...groupe("PT", 1976, 9999),
          ...groupe("ES", 1977, 9999), ...groupe("LI", 1978, 9999), ...groupe("SM", 1988, 9999),
          ...groupe("FI", 1989, 9999), ...groupe("HU", 1990, 9999), ...groupe("PL", 1991, 9999),
          ...groupe("BG", 1992, 9999), ...groupe("EE LT SI CZ SK RO", 1993, 9999), ...groupe("AD", 1994, 9999),
          ...groupe("LV MD AL UA MK", 1995, 9999), ...groupe("HR", 1996, 9999), RU: [[1996, 2021]],
          ...groupe("GE", 1999, 9999), ...groupe("AM AZ", 2001, 9999), ...groupe("BA", 2002, 9999),
          ...groupe("RS", 2003, 9999), ...groupe("MC", 2004, 9999), ...groupe("ME", 2007, 9999),
        },
        avant: null,
      },
    };

    const couche = COUCHES[Math.round(nombre(valeurs.couche, 1))] || COUCHES[1];
    const annee = Math.round(Math.min(2026, Math.max(1949, nombre(valeurs.annee, 2026))));
    const etat = (code) => {
      const periodes = couche.membres[code];
      if (!periodes) return "jamais";
      if (periodes.some(([d, f]) => annee >= d && annee <= f)) return periodes.some(([d]) => d === annee) ? "nouveau" : "membre";
      return periodes.some(([, f]) => annee > f) ? "sorti" : "pas-encore";
    };

    // --- mise en page --------------------------------------------------------------------------------------
    const PAS = 30, COTE = 27, X0 = 6, Y0 = 52;
    const H = Y0 + 8 * PAS + 34;
    svg.setAttribute("viewBox", `0 0 340 ${H}`);
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    let compte = 0;
    const nouveaux = [];
    for (const [code, [col, lig, nom]] of Object.entries(PAYS)) {
      const e = etat(code);
      const dedans = e === "membre" || e === "nouveau";
      if (dedans) compte += 1;
      if (e === "nouveau") nouveaux.push(nom);
      const x = X0 + col * PAS, y = Y0 + lig * PAS;
      const tuile = el("rect", {
        x, y, width: COTE, height: COTE, rx: 4,
        fill: dedans ? couche.couleur : VIDE,
        stroke: code === "FR" ? "#C8102E" : e === "sorti" ? couche.couleur : "none",
        "stroke-width": code === "FR" ? 3 : 2,
        "stroke-dasharray": e === "sorti" && code !== "FR" ? "4 3" : "none",
      });
      tuile.setAttribute("data-pays", code);
      if (e === "nouveau") {
        el("rect", { x: x + 3, y: y + 3, width: COTE - 6, height: COTE - 6, rx: 2, fill: "none", stroke: "#FFFFFF", "stroke-width": 2 });
      }
      el("text", { x: x + COTE / 2, y: y + COTE / 2 + 5, "font-size": 13, "text-anchor": "middle", fill: dedans ? "#FFFFFF" : GRIS, "font-weight": 700 }, code);
    }

    // Titre : ensemble, annee, nombre de pays (ou « pas encore »).
    const nomCouche = couche.nom(annee);
    const titre = couche.avant && annee < couche.avant[0] ? couche.avant[1] : `${nomCouche} en ${annee} : ${compte} pays`;
    el("text", { x: 170, y: 20, "font-size": 14, "text-anchor": "middle", fill: ENCRE, "font-weight": 700 }, titre);
    const sous = nouveaux.length ? (nouveaux.length <= 3 ? `entrent : ${nouveaux.join(", ")}` : `${nouveaux.length} pays entrent cette année`) : "";
    if (sous) el("text", { x: 170, y: 40, "font-size": 13, "text-anchor": "middle", fill: couche.couleur === ENCRE ? GRIS : couche.couleur, "font-weight": 700 }, sous);

    // Legende : France encadree en rouge, carre colore = membre.
    const yl = Y0 + 8 * PAS + 18;
    el("rect", { x: 6, y: yl - 12, width: 16, height: 16, rx: 3, fill: couche.couleur });
    el("text", { x: 28, y: yl + 1, "font-size": 13, fill: ENCRE }, "membre");
    el("rect", { x: 96, y: yl - 12, width: 16, height: 16, rx: 3, fill: VIDE, stroke: "#C8102E", "stroke-width": 3 });
    el("text", { x: 118, y: yl + 1, "font-size": 13, fill: ENCRE }, "France");
    el("rect", { x: 180, y: yl - 12, width: 16, height: 16, rx: 3, fill: VIDE, stroke: couche.couleur, "stroke-width": 2, "stroke-dasharray": "4 3" });
    el("text", { x: 202, y: yl + 1, "font-size": 13, fill: ENCRE }, "pays sorti");
    return { annee, membres: compte };
  },
};
