// Jules - bouton « Calculatrice » a cote de l'entree vers Jules (docs/spec/NAVIGATION.md, EX-217).
//
// - Le bouton n'existe que si l'outil `calculatrice` figure dans `outils.catalogue` de /api/infos (module
//   `outils` actif) et si OutilsHote est charge : jamais de bouton mort (EX-205). Aucun appel d'API ici
//   (EX-210) : le catalogue vient des infos deja lues par la page.
// - La calculatrice s'ouvre dans un panneau de la page, montee par OutilsHote.monter (outils-hote.js) :
//   iframe sandbox="allow-scripts" sans allow-same-origin, qui recoit les leviers de l'eleve (EX-001 a 003).
//   Les fichiers de l'outil ne sont demandes qu'a l'ouverture ; a la fermeture, l'iframe est demontee.
// - Bouton a bascule (aria-expanded) : une seule calculatrice ouverte a la fois, un second clic la ferme.
//   Fermeture aussi par « × » et par Echap ; le focus revient au bouton.
"use strict";

const Calculatrice = (() => {
  const OUTIL = "calculatrice";
  const ID_PANNEAU = "calculatrice-panneau";

  function outilDuCatalogue(infos) {
    const catalogue = infos && infos.outils && Array.isArray(infos.outils.catalogue) ? infos.outils.catalogue : [];
    return catalogue.find((o) => o && o.id === OUTIL) || null;
  }

  // options.voisin : l'element qui ouvre Jules ; options.place : "avant" ou "apres" ce voisin.
  // options.leviers : valeurs brutes des leviers (MS.appliquerLeviers), transmises telles quelles a l'outil.
  // options.variante : classe de forme du bouton (ex. "rond" a cote du J de /). options.bande : conteneur de Jules
  // qui passe dans le flux sur telephone (#jules-bulles de /). Renvoie le bouton, ou null.
  function monter(infos, options = {}) {
    const outil = outilDuCatalogue(infos);
    const voisin = options.voisin;
    if (!outil || typeof OutilsHote === "undefined" || !voisin || !voisin.parentNode) return null;

    const bouton = document.createElement("button");
    bouton.type = "button";
    bouton.id = "bouton-calculatrice";
    bouton.className = "bouton-calculatrice" + (options.variante ? ` bouton-calculatrice-${options.variante}` : "");
    bouton.setAttribute("aria-label", "Calculatrice");
    bouton.setAttribute("aria-expanded", "false");
    bouton.setAttribute("aria-controls", ID_PANNEAU);
    bouton.title = "Calculatrice";
    const icone = document.createElement("span");
    icone.setAttribute("aria-hidden", "true");
    icone.textContent = "🧮";
    bouton.appendChild(icone);
    voisin.parentNode.insertBefore(bouton, options.place === "apres" ? voisin.nextSibling : voisin);

    const panneau = document.createElement("section");
    panneau.id = ID_PANNEAU;
    panneau.className = "calculatrice-panneau" + (options.variante ? ` calculatrice-panneau-${options.variante}` : "");
    panneau.setAttribute("aria-label", "Calculatrice");
    panneau.hidden = true;
    const tete = document.createElement("div");
    tete.className = "calculatrice-tete";
    const titre = document.createElement("span");
    titre.className = "calculatrice-titre";
    titre.textContent = outil.titre || "Calculatrice";
    const fermer = document.createElement("button");
    fermer.type = "button";
    fermer.className = "calculatrice-fermer";
    fermer.setAttribute("aria-label", "Fermer la calculatrice");
    fermer.textContent = "×";
    tete.append(titre, fermer);
    const zone = document.createElement("div");
    zone.className = "calculatrice-zone";
    panneau.append(tete, zone);
    document.body.appendChild(panneau);
    document.body.classList.add("avec-calculatrice");

    let monte = null;

    // Bande de Jules dans le flux (telephone, EX-213) : le panneau s'ouvre juste au-dessus d'elle, a la hauteur
    // mesuree a l'ouverture (la bulle change sa hauteur). Sinon, positions du CSS.
    function placer() {
      panneau.style.bottom = "";
      panneau.style.maxHeight = "";
      const bande = options.bande;
      if (!bande || getComputedStyle(bande).position !== "static") return;
      const haut = bande.getBoundingClientRect().top;
      panneau.style.bottom = `${Math.max(0, innerHeight - haut) + 8}px`;
      panneau.style.maxHeight = `${Math.max(0, haut - 16)}px`;
    }

    function ouvrir() {
      if (monte) return;
      monte = OutilsHote.monter(zone, outil, { leviers: options.leviers || {}, surEvenement });
      placer();
      panneau.hidden = false;
      bouton.setAttribute("aria-expanded", "true");
      fermer.focus();
    }

    function refermer() {
      if (!monte) return;
      monte.demonter();
      monte = null;
      panneau.hidden = true;
      bouton.setAttribute("aria-expanded", "false");
      bouton.focus();
    }

    // Evenement reserve « fermer » (docs/OUTILS-CONTRAT.md, §2) : Echap tape alors que le focus est dans l'iframe.
    // Deja filtre par OutilsHote (source = cette iframe, evenement declare dans la fiche).
    function surEvenement(evenement) {
      if (evenement === "fermer") refermer();
    }

    bouton.addEventListener("click", () => (monte ? refermer() : ouvrir()));
    fermer.addEventListener("click", refermer);
    document.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape" && monte) refermer();
    });
    return bouton;
  }

  return { monter, OUTIL };
})();
