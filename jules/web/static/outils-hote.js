// Jules - page hote des outils : cree l'iframe isolee d'un outil et filtre ce qu'il envoie.
// Contrat : docs/OUTILS-CONTRAT.md, section 2 (« Origine opaque », « Adaptations ») et section 3.
//
// - L'iframe est en sandbox="allow-scripts" SANS allow-same-origin : origine opaque, l'outil n'a
//   acces ni au cookie de session, ni au DOM de la page, ni au localStorage du site.
// - Un message n'est accepte que si event.source === iframe.contentWindow (jamais event.origin,
//   qui vaut "null" pour une iframe sandboxee), puis si son schema est valide : objet,
//   type "evenement", evenement declare dans la fiche de l'outil. Tout le reste est ignore sans
//   erreur ni effet de bord.
// - Poignee de main des adaptations (EX-001 a 003, docs/spec/ADAPTATIONS.md) : a CHAQUE
//   {type: "pret"} venu de l'iframe (y compris apres un rechargement, meme contentWindow), l'hote
//   repond {type: "adaptations", leviers: {...}}. Un "pret" venu d'ailleurs n'a aucun effet.
// - Une action n'est envoyee que si elle est declaree dans la fiche de l'outil.
"use strict";

(() => {
  const SANDBOX = "allow-scripts";
  const RACINE = "/api/eleve/outils/";

  function estObjet(v) {
    return v !== null && typeof v === "object" && !Array.isArray(v);
  }

  function venuDeLIframe(event, iframe) {
    if (!iframe || !iframe.contentWindow || event.source !== iframe.contentWindow) return false;
    return true;
  }

  // Filtre d'un message recu par la page hote. Renvoie {evenement, donnees} ou null.
  function filtrer(event, iframe, outil) {
    if (!venuDeLIframe(event, iframe)) return null;
    const message = event.data;
    if (!estObjet(message) || message.type !== "evenement") return null;
    if (typeof message.evenement !== "string" || !(outil.evenements || []).includes(message.evenement)) return null;
    const donnees = estObjet(message.donnees) ? message.donnees : {};
    return { evenement: message.evenement, donnees };
  }

  // Message de poignee de main venu de CETTE iframe : "pret", "adaptations-absentes" ou null.
  function poignee(event, iframe) {
    if (!venuDeLIframe(event, iframe)) return null;
    const message = event.data;
    if (!estObjet(message)) return null;
    return message.type === "pret" || message.type === "adaptations-absentes" ? message.type : null;
  }

  // Monte l'outil `outil` (entree du catalogue : Outil.publique()) dans `conteneur`.
  // options.action / options.donnees : action a envoyer une fois l'outil charge (si declaree).
  // options.leviers : dictionnaire opaque des leviers d'adaptation de l'eleve ({} par defaut) ;
  //   l'hote ne l'interprete pas, l'outil ignore les leviers qu'il ne connait pas.
  // options.surEvenement(evenement, donnees) : appele pour chaque evenement valide de CET outil.
  // options.surAdaptationsAbsentes() : l'outil s'est affiche sans ses leviers (delai depasse).
  // Renvoie { iframe, envoyer(action, donnees), demonter() }.
  function monter(conteneur, outil, options = {}) {
    const leviers = estObjet(options.leviers) ? options.leviers : {};
    const iframe = document.createElement("iframe");
    iframe.setAttribute("sandbox", SANDBOX);
    iframe.setAttribute("referrerpolicy", "no-referrer");
    iframe.className = "outil-cadre";
    iframe.title = outil.titre || outil.id;
    // Barre finale obligatoire : l'entree charge ses fichiers en relatif (outil.css, outil.js).
    iframe.src = `${RACINE}${encodeURIComponent(outil.id)}/`;

    // "*" est le seul choix possible : l'origine de l'iframe est opaque (voir le contrat, §2).
    function poster(message) {
      if (iframe.contentWindow) iframe.contentWindow.postMessage(message, "*");
    }

    function envoyer(action, donnees) {
      if (!(outil.actions || []).includes(action) || !iframe.contentWindow) return false;
      // Le message ne contient que ce que la lecon transmet a l'outil.
      poster({ type: "action", action, donnees: estObjet(donnees) ? donnees : {} });
      return true;
    }

    function recu(event) {
      const etape = poignee(event, iframe);
      if (etape === "pret") {
        poster({ type: "adaptations", leviers });
        return;
      }
      if (etape === "adaptations-absentes") {
        if (typeof options.surAdaptationsAbsentes === "function") options.surAdaptationsAbsentes();
        return;
      }
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

  window.OutilsHote = { SANDBOX, monter, filtrer, poignee };
})();
