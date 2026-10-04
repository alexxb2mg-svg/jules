// Jules - gabarit "arbre-multiplication" : un arbre qui se multiplie a chaque etape, dessine en anneaux autour du
// point de depart (anneau k = etape k). motif 1 = personnes : un message (rond rouge) part du centre et chacun le
// transmet a `facteur` personnes ; motif 2 = cellules ou bacteries : chaque cellule se divise en DEUX (facteur
// est alors ignore). Le frein (frein = 1) : motif 1, les personnes qui recoivent verifient avant de partager et ne
// transmettent pas (vert), la propagation s'arrete ; motif 2, un traitement (antiseptique, antibiotique) agit a
// partir de la 2e division : les cellules sensibles meurent (gris, croix) et seule la lignee resistante (orange)
// continue a se diviser. Lisibilite : au-dela de 64 elements sur un anneau (ou de la place disponible), l'anneau
// devient une bande grise et un compteur prend le relais (« Au total : N personnes ») ; il ne sert qu'au motif 1
// (motif 2 : au plus 2^6 = 64 cellules, toutes dessinees).
// Sources : programme d'enseignement moral et civique (arrete du 29/05/2024, BO n° 24 du 13/06/2024) : information,
// desinformation, cyberviolences et harcelement en ligne ; programme de SVT du cycle 4 (BO n° 31 du 30/07/2020) :
// monde microbien, « mesures d'hygiene, vaccination, action des antiseptiques et des antibiotiques » ;
// Wikipedia « Scissiparite » : une bacterie se divise en deux cellules filles identiques ; « Resistance aux
// antibiotiques » : l'antibiotique elimine les bacteries sensibles, les resistantes survivent et se multiplient.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["arbre-multiplication"] = {
  dessiner(svg, valeurs) {
    const borne = (v, mini, maxi, defaut) => {
      const n = Number(v ?? defaut);
      return Math.round(Math.min(maxi, Math.max(mini, Number.isFinite(n) ? n : defaut)));
    };
    const etapes = borne(valeurs.etapes, 0, 6, 3);
    const motif = borne(valeurs.motif, 1, 2, 1);
    const facteur = motif === 2 ? 2 : borne(valeurs.facteur, 1, 5, 2);
    const frein = borne(valeurs.frein, 0, 1, 0);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", ROUGE = "#C8102E", VERT = "#2E7D32", ORANGE = "#E07B00";
    const CX = 170, CY = 152;
    const rayon = (k) => 18 + k * 20;
    const capacite = (k) => Math.min(64, Math.floor((2 * Math.PI * rayon(k)) / 11));
    const angle = (j, n) => -Math.PI / 2 + (2 * Math.PI * (j + 0.5)) / n;
    const position = (k, j, n) => (k === 0 ? { x: CX, y: CY } : { x: CX + rayon(k) * Math.cos(angle(j, n)), y: CY + rayon(k) * Math.sin(angle(j, n)) });

    svg.setAttribute("viewBox", "0 0 340 340");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // Anneaux : pour chaque etape, la liste des noeuds dessines {j, parent, etat} sur n places.
    // etat : "recu" (bleu), "stop" (vert : verifie, ne partage pas), "mort" (gris), "resistant" (orange).
    // effectif = nombre reel d'elements de l'anneau, meme quand il n'est plus dessine (compteur).
    const anneaux = [{ n: 1, effectif: 1, noeuds: [{ j: 0, parent: -1, etat: "recu" }] }];
    let arret = false; // motif 1 avec frein : plus rien apres le 1er anneau
    let bande = false; // un anneau trop plein a ete remplace par une bande grise
    for (let k = 1; k <= etapes; k++) {
      const prec = anneaux[k - 1];
      const n = prec.n * facteur;
      const noeuds = [];
      if (prec.trop) {
        anneaux.push({ n, effectif: prec.effectif * facteur, noeuds, trop: true });
        continue;
      }
      for (const p of prec.noeuds) {
        if (p.etat === "stop" || p.etat === "mort") continue; // ne transmet pas, ne se divise pas
        for (let c = 0; c < facteur; c++) {
          const j = p.j * facteur + c;
          let etat = p.etat;
          if (frein === 1 && motif === 1) etat = "stop";
          if (frein === 1 && motif === 2 && k === 2) etat = j === 0 ? "resistant" : "mort";
          noeuds.push({ j, parent: p.j, etat });
        }
      }
      if (frein === 1 && motif === 1 && k >= 2) arret = true;
      const trop = noeuds.length > capacite(k);
      if (trop) bande = true;
      anneaux.push({ n, effectif: noeuds.length, noeuds: trop ? [] : noeuds, trop });
    }

    // Guides : cercles pales des etapes (pointilles quand le message s'est arrete).
    for (let k = 1; k <= etapes; k++) {
      const vide = anneaux[k].noeuds.length === 0 && !anneaux[k].trop;
      el("circle", {
        cx: CX, cy: CY, r: rayon(k), fill: "none", stroke: vide ? "#B8C0CB" : "#E3E7EC", "stroke-width": 2,
        "stroke-dasharray": vide ? "4 6" : "none",
      });
    }
    // Bandes grises des anneaux trop pleins (« et encore plus »).
    for (let k = 1; k <= etapes; k++) {
      if (anneaux[k].trop) el("circle", { cx: CX, cy: CY, r: rayon(k), fill: "none", stroke: GRIS, "stroke-width": 12, "stroke-opacity": 0.45 });
    }
    // Liens parent -> enfant.
    for (let k = 1; k <= etapes; k++) {
      const { n, noeuds } = anneaux[k];
      for (const c of noeuds) {
        const a = position(k - 1, c.parent, anneaux[k - 1].n), b = position(k, c.j, n);
        el("line", { x1: a.x, y1: a.y, x2: b.x, y2: b.y, stroke: "#B8C0CB", "stroke-width": 2 });
      }
    }
    // Noeuds.
    const COULEUR = { recu: BLEU, stop: VERT, mort: "#B8C0CB", resistant: ORANGE };
    for (let k = 1; k <= etapes; k++) {
      const { n, noeuds } = anneaux[k];
      for (const c of noeuds) {
        const { x, y } = position(k, c.j, n);
        if (motif === 2) el("ellipse", { cx: x, cy: y, rx: 5.5, ry: 4, fill: COULEUR[c.etat], stroke: ENCRE, "stroke-width": 1 });
        else el("circle", { cx: x, cy: y, r: 4.5, fill: COULEUR[c.etat] });
        if (c.etat === "mort") {
          el("line", { x1: x - 5, y1: y - 5, x2: x + 5, y2: y + 5, stroke: GRIS, "stroke-width": 2 });
          el("line", { x1: x - 5, y1: y + 5, x2: x + 5, y2: y - 5, stroke: GRIS, "stroke-width": 2 });
        }
      }
    }
    // Le depart, au centre.
    if (motif === 2) el("ellipse", { cx: CX, cy: CY, rx: 10, ry: 7, fill: BLEU, stroke: ENCRE, "stroke-width": 2 });
    else el("circle", { cx: CX, cy: CY, r: 10, fill: ROUGE });

    let phrase;
    if (etapes === 0) phrase = motif === 2 ? "Une seule cellule au départ" : "Le message n'est pas encore parti";
    else if (motif === 1 && frein === 1) phrase = "On vérifie avant de partager : ça s'arrête";
    else if (motif === 1) phrase = facteur === 1 ? "Chacun transmet à une seule personne" : "Chacun transmet : ça grossit vite";
    else if (frein === 1 && etapes >= 2) phrase = "Traitement : les résistantes survivent";
    else phrase = "Chaque cellule se divise en deux";
    el("text", { x: 170, y: 314, "font-size": 16, "font-weight": 700, "text-anchor": "middle", fill: ENCRE }, phrase);
    // Compteur (seulement quand une bande grise remplace des ronds) : toutes les personnes touchees, depart exclu.
    let total = 0;
    for (let k = 1; k <= etapes; k++) total += anneaux[k].effectif;
    const enClair = String(total).replace(/\B(?=(\d{3})+(?!\d))/g, " ");
    let legende;
    if (motif === 1 && frein === 1) legende = "rouge = départ · vert = vérifie, ne partage pas";
    else if (motif === 1) legende = bande ? `Au total : ${enClair} personnes ont reçu` : "rouge = départ · bleu = a reçu le message";
    else if (frein === 1 && etapes >= 2) legende = "gris = tuées · orange = résistantes";
    else legende = "bleu = cellules identiques";
    el("text", { x: 170, y: 334, "font-size": bande ? 14 : 13, "font-weight": bande ? 700 : 400, "text-anchor": "middle", fill: bande ? ROUGE : GRIS }, legende);
    return { etapes, facteur, frein, motif, arret, bande, total };
  },
};
