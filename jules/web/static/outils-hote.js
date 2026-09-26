// Jules - page hote des outils : cree l'iframe isolee d'un outil et filtre ce qu'il envoie.
// Contrat : docs/OUTILS-CONTRAT.md, section 2 (« Origine opaque ») et section 3 (isolement).
//
// - L'iframe est en sandbox="allow-scripts" SANS allow-same-origin : origine opaque, l'outil n'a
//   acces ni au cookie de session, ni au DOM de la page, ni au localStorage du site.
// - Un message n'est accepte que si event.source === iframe.contentWindow (jamais event.origin,
//   qui vaut "null" pour une iframe sandboxee), puis si son schema est valide : objet,
//   type "evenement", evenement declare dans la fiche de l'outil. Tout le reste est ignore sans
//   erreur ni effet de bord.
// - Une action n'est envoyee que si elle est declaree dans la fiche de l'outil.
"use strict";

(() => {
  const SANDBOX = "allow-scripts";
  const RACINE = "/api/eleve/outils/";

  function estObjet(v) {
    return v !== null && typeof v === "object" && !Array.isArray(v);
  }

  // Filtre d'un message recu par la page hote. Renvoie {evenement, donnees} ou null.
  function filtrer(event, iframe, outil) {
    if (!iframe || !iframe.contentWindow || event.source !== iframe.contentWindow) return null;
    const message = event.data;
    if (!estObjet(message) || message.type !== "evenement") return null;
    if (typeof message.evenement !== "string" || !(outil.evenements || []).includes(message.evenement)) return null;
    const donnees = estObjet(message.donnees) ? message.donnees : {};
    return { evenement: message.evenement, donnees };
  }

  // Monte l'outil `outil` (entree du catalogue : Outil.publique()) dans `conteneur`.
  // options.action / options.donnees : action a envoyer une fois l'outil charge (si declaree).
  // options.surEvenement(evenement, donnees) : appele pour chaque evenement valide de CET outil.
  // Renvoie { iframe, envoyer(action, donnees), demonter() }.
  function monter(conteneur, outil, options = {}) {
    const iframe = document.createElement("iframe");
    iframe.setAttribute("sandbox", SANDBOX);
    iframe.setAttribute("referrerpolicy", "no-referrer");
    iframe.className = "outil-cadre";
    iframe.title = outil.titre || outil.id;
    // Barre finale obligatoire : l'entree charge ses fichiers en relatif (outil.css, outil.js).
    iframe.src = `${RACINE}${encodeURIComponent(outil.id)}/`;

    function envoyer(action, donnees) {
      if (!(outil.actions || []).includes(action) || !iframe.contentWindow) return false;
      // "*" est le seul choix possible : l'origine de l'iframe est opaque (voir le contrat, §2).
      // Le message ne contient que ce que la lecon transmet a l'outil.
      iframe.contentWindow.postMessage({ type: "action", action, donnees: estObjet(donnees) ? donnees : {} }, "*");
      return true;
    }

    function recu(event) {
      const valide = filtrer(event, iframe, outil);
      if (valide && typeof options.surEvenement === "function") options.surEvenement(valide.evenement, valide.donnees);
    }

    window.addEventListener("message", recu);
    iframe.addEventListener("load", () => {
      if (options.action) envoyer(options.action, options.donnees);
    });
    conteneur.appendChild(iframe);

    function demonter() {
      window.removeEventListener("message", recu);
      iframe.remove();
    }
    return { iframe, envoyer, demonter };
  }

  window.OutilsHote = { SANDBOX, monter, filtrer };
})();
