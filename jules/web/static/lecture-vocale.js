// Lecture vocale (spec ADAPTATIONS, EX-006 et EX-007 ; spec ADAPTATIONS-LOT2, EX-109).
// Confidentialite : seules les voix installees sur l'appareil (localService === true) sont utilisees ;
// une voix « en ligne » enverrait le texte de l'eleve a un serveur tiers. Le filtre porte sur cette
// propriete et jamais sur le nom de la voix (les noms changent d'un appareil a l'autre).
// La liste des voix peut etre vide au chargement : elle est relue a chaque evenement voiceschanged.
// Aucun nom de navigateur n'apparait ici : on constate le resultat du filtre, rien d'autre.
//
// EX-109, cote eleve. Le levier `lecture-vocale` (adaptations/leviers/lecture-vocale.yaml) vaut
// « absente », « proposee » ou « automatique ». Hors « absente », et seulement si une voix locale
// existe, chaque bulle de Jules et chaque consigne recoit un bouton de lecture. En « automatique » :
// - une NOUVELLE bulle de Jules est lue une fois, quand la page l'appelle (bulle affichee en entier) ;
// - les consignes ne sont lues qu'au clic ; les messages de l'eleve ne sont jamais equipes ;
// - une nouvelle bulle interrompt la lecture en cours ;
// - la lecture s'arrete des que l'eleve tape dans le champ de saisie ou clique sur « arreter » ;
// - « arreter » ne vaut que pour la bulle en cours : la bulle suivante sera lue.
"use strict";

const LectureVocale = (() => {
  const TEXTE_DISPONIBLE = "Lecture vocale disponible sur cet appareil (voix installées localement).";
  const TEXTE_INDISPONIBLE = "Lecture vocale indisponible sur cet appareil : aucune voix installée localement.";
  const MODES = ["absente", "proposee", "automatique"];
  const LIBELLE_LIRE = "🔊 Écouter";
  const LIBELLE_ARRETER = "⏹ Arrêter";
  const CLASSE_BOUTON = "lecture-vocale-bouton";

  let synthese = null;
  let voix = [];
  const abonnes = [];
  let mode = "absente";
  let enCours = null; // { enonce, bouton } : la lecture en cours et le bouton qui la montre
  const textes = new WeakMap(); // bouton -> texte qu'il lit

  function voixLocales(liste) {
    return Array.from(liste || []).filter((v) => v && v.localService === true);
  }

  function disponible() {
    return voix.length > 0;
  }

  // Voix choisie parmi les locales : d'abord une voix francaise (langue, pas nom), sinon la voix par
  // defaut, sinon la premiere.
  function voixChoisie() {
    return voix.find((v) => /^fr\b/i.test(v.lang || "")) || voix.find((v) => v.default) || voix[0] || null;
  }

  function relire() {
    voix = synthese ? voixLocales(synthese.getVoices()) : [];
    for (const rappel of abonnes) rappel(disponible());
  }

  // Branche le module sur une synthese vocale (window.speechSynthesis par defaut ; les tests en
  // passent une simulee). Sans synthese, la lecture est indisponible.
  function initialiser(source) {
    synthese = source === undefined ? (typeof speechSynthesis === "undefined" ? null : speechSynthesis) : source;
    if (synthese && typeof synthese.addEventListener === "function") {
      synthese.addEventListener("voiceschanged", relire);
    }
    relire();
  }

  function surChangement(rappel) {
    abonnes.push(rappel);
    rappel(disponible());
  }

  // Bouton de lecture : masque (classe « cache ») tant qu'aucune voix locale n'est disponible.
  function brancherBouton(bouton, texte) {
    surChangement((ok) => {
      bouton.hidden = !ok;
      bouton.classList.toggle("cache", !ok);
    });
    bouton.addEventListener("click", () => lire(typeof texte === "function" ? texte() : texte));
  }

  // Indicateur de la page parent (EX-007).
  function indiquer(element) {
    surChangement((ok) => {
      element.textContent = ok ? TEXTE_DISPONIBLE : TEXTE_INDISPONIBLE;
      element.dataset.disponible = ok ? "oui" : "non";
    });
  }

  // Lit un texte avec la voix locale choisie ; interrompt toute lecture precedente. Renvoie l'enonce
  // ou null si rien n'a ete lu.
  function enoncer(texte) {
    const choisie = voixChoisie();
    if (!choisie || !texte || typeof SpeechSynthesisUtterance === "undefined") return null;
    const enonce = new SpeechSynthesisUtterance(texte);
    enonce.voice = choisie;
    enonce.lang = choisie.lang || "fr-FR";
    synthese.cancel();
    synthese.speak(enonce);
    return enonce;
  }

  function lire(texte) {
    return enoncer(texte) !== null;
  }

  // --- EX-109 : mode et boutons cote eleve ------------------------------------------------------------

  // Valeur du levier telle que la page la recoit ; toute valeur inconnue vaut « absente ».
  function definirMode(valeur) {
    mode = MODES.includes(valeur) ? valeur : "absente";
    majBoutons(disponible());
  }

  function modeActuel() {
    return mode;
  }

  // Le levier est lu dans /api/infos, sous `leviers` (valeurs effectives des leviers de l'eleve).
  function modeDepuis(infos) {
    const leviers = infos && infos.leviers;
    return leviers && typeof leviers === "object" ? leviers["lecture-vocale"] : undefined;
  }

  const boutonsVisibles = (ok) => mode !== "absente" && ok;

  function majBoutons(ok) {
    if (typeof document === "undefined") return;
    for (const bouton of document.querySelectorAll(`button.${CLASSE_BOUTON}`)) {
      bouton.hidden = !boutonsVisibles(ok);
      bouton.classList.toggle("cache", bouton.hidden);
    }
  }

  function montrer(bouton, lecture) {
    bouton.textContent = lecture ? LIBELLE_ARRETER : LIBELLE_LIRE;
    bouton.setAttribute("aria-pressed", lecture ? "true" : "false");
    bouton.setAttribute("aria-label", lecture ? "Arrêter la lecture" : "Écouter ce texte");
  }

  function terminer(enonce) {
    if (!enCours || (enonce && enCours.enonce !== enonce)) return; // fin d'une lecture deja remplacee
    montrer(enCours.bouton, false);
    enCours = null;
  }

  // Arrete la lecture en cours, et seulement elle : le mode n'est pas touche.
  function arreter() {
    if (!enCours) return;
    const courant = enCours;
    enCours = null;
    montrer(courant.bouton, false);
    if (synthese) synthese.cancel();
  }

  function lireAvec(bouton, texte) {
    const precedent = enCours;
    enCours = null;
    if (precedent) montrer(precedent.bouton, false);
    const enonce = enoncer(texte);
    if (!enonce) return false;
    enCours = { enonce, bouton };
    montrer(bouton, true);
    const fin = () => terminer(enonce);
    if (typeof enonce.addEventListener === "function") {
      enonce.addEventListener("end", fin);
      enonce.addEventListener("error", fin);
    } else {
      enonce.onend = fin;
      enonce.onerror = fin;
    }
    return true;
  }

  // Ajoute le bouton de lecture a `element` (texte lu = texte visible de l'element, pris avant l'ajout
  // du bouton, sauf `texte` explicite). Ne fait rien en mode « absente » : le rendu reste celui
  // d'aujourd'hui (EX-102).
  function equiper(element, texte) {
    if (!element || mode === "absente") return null;
    const aLire = String(texte === undefined ? element.textContent : texte).trim();
    if (!aLire) return null;
    const bouton = document.createElement("button");
    bouton.type = "button";
    bouton.className = CLASSE_BOUTON;
    bouton.setAttribute("data-sans-symboles", ""); // pas de rappel au survol sur le libelle du bouton
    textes.set(bouton, aLire);
    montrer(bouton, false);
    bouton.hidden = !boutonsVisibles(disponible());
    bouton.classList.toggle("cache", bouton.hidden);
    bouton.addEventListener("click", (ev) => {
      ev.stopPropagation(); // une bulle qui se ferme au clic ne doit pas se fermer ici
      if (enCours && enCours.bouton === bouton) arreter();
      else lireAvec(bouton, aLire);
    });
    element.appendChild(bouton);
    return bouton;
  }

  // Bulle de Jules. `nouvelle` : la bulle vient d'etre affichee en entier (pas une bulle d'historique).
  // En mode automatique, une nouvelle bulle est lue une fois et interrompt la lecture en cours.
  function equiperBulle(element, options = {}) {
    const bouton = equiper(element, options.texte);
    if (!bouton || !options.nouvelle || mode !== "automatique" || !disponible()) return bouton;
    lireAvec(bouton, textes.get(bouton));
    return bouton;
  }

  // Consigne : bouton seulement, jamais lue sans clic.
  function equiperConsigne(element, texte) {
    return equiper(element, texte);
  }

  // Saisie de l'eleve : taper (evenement input) dans un champ de texte arrete la lecture en cours.
  // Une touche qui ne modifie pas le champ (Tab, fleches) ne l'arrete pas, ni une case cochee.
  // `racine` : le champ lui-meme ou un conteneur (document pour tous les champs de la page).
  function brancherSaisie(racine) {
    if (!racine) return;
    racine.addEventListener("input", (ev) => {
      const cible = ev.target;
      const texte = cible && (cible.tagName === "TEXTAREA" || (cible.tagName === "INPUT" && !["radio", "checkbox"].includes(cible.type)));
      if (texte) arreter();
    });
  }

  surChangement(majBoutons);

  return {
    TEXTE_DISPONIBLE, TEXTE_INDISPONIBLE, MODES, LIBELLE_LIRE, LIBELLE_ARRETER, CLASSE_BOUTON,
    voixLocales, disponible, voixChoisie, initialiser, surChangement, brancherBouton, indiquer, lire,
    definirMode, modeActuel, modeDepuis, equiperBulle, equiperConsigne, brancherSaisie, arreter,
  };
})();
