// Lecture vocale (spec ADAPTATIONS, EX-006 et EX-007).
// Confidentialite : seules les voix installees sur l'appareil (localService === true) sont utilisees ;
// une voix « en ligne » enverrait le texte de l'eleve a un serveur tiers. Le filtre porte sur cette
// propriete et jamais sur le nom de la voix (les noms changent d'un appareil a l'autre).
// La liste des voix peut etre vide au chargement : elle est relue a chaque evenement voiceschanged.
// Aucun nom de navigateur n'apparait ici : on constate le resultat du filtre, rien d'autre.
"use strict";

const LectureVocale = (() => {
  const TEXTE_DISPONIBLE = "Lecture vocale disponible sur cet appareil (voix installées localement).";
  const TEXTE_INDISPONIBLE = "Lecture vocale indisponible sur cet appareil : aucune voix installée localement.";

  let synthese = null;
  let voix = [];
  const abonnes = [];

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

  function lire(texte) {
    const choisie = voixChoisie();
    if (!choisie || !texte || typeof SpeechSynthesisUtterance === "undefined") return false;
    const enonce = new SpeechSynthesisUtterance(texte);
    enonce.voice = choisie;
    enonce.lang = choisie.lang || "fr-FR";
    synthese.cancel();
    synthese.speak(enonce);
    return true;
  }

  return {
    TEXTE_DISPONIBLE, TEXTE_INDISPONIBLE,
    voixLocales, disponible, voixChoisie, initialiser, surChangement, brancherBouton, indiquer, lire,
  };
})();
