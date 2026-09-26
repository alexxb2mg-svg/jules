// Extension rappels-anglais : bulles de rappel pour l'anglais (famille `rappels`, docs/EXTENSIONS.md).
//   - phonetique : une transcription entre barres obliques (/θ/, /θɪŋk/) explique ses sons ;
//   - abreviations : sb, sth, BV, V-ing, V-ed, niveaux du CECRL (A1 a C2), UK, US... ;
//   - structures : « BE + V-ing », « HAVE + participe passé » ressortent en gras, comme les formules.
"use strict";

(() => {
const ANGLAIS = ["anglais"];
const o = Symboles.outils;

// Sons de l'anglais (alphabet phonetique international), expliques par un mot connu.
const SONS = {
  "θ": "th sourd, comme dans think (langue entre les dents, sans voix)",
  "ð": "th sonore, comme dans this",
  "ʃ": "ch français, comme dans she",
  "ʒ": "j français, comme dans measure",
  "tʃ": "tch, comme dans chair",
  "dʒ": "dj, comme dans jump",
  "ŋ": "ng de sing (le g ne se prononce pas)",
  "h": "h expiré, comme dans house : on souffle",
  "j": "son y, comme dans yes",
  "w": "son ou bref, comme dans we",
  "r": "r anglais, langue en arrière sans toucher le palais, comme dans red",
  "ɪ": "i bref, comme dans sit",
  "iː": "i long, comme dans see",
  "ʊ": "ou bref, comme dans book",
  "uː": "ou long, comme dans food",
  "e": "è bref, comme dans bed",
  "æ": "a très ouvert, comme dans cat",
  "ʌ": "a bref et sourd, comme dans cup",
  "ɑː": "a long, comme dans car",
  "ɒ": "o bref, comme dans hot",
  "ɔː": "o long, comme dans door",
  "ə": "schwa : voyelle neutre et très brève, comme le a de about",
  "ɜː": "eu long, comme dans bird",
  "eɪ": "diphtongue éi, comme dans day",
  "aɪ": "diphtongue aï, comme dans my",
  "ɔɪ": "diphtongue oï, comme dans boy",
  "aʊ": "diphtongue aou, comme dans now",
  "əʊ": "diphtongue eu-ou, comme dans go",
  "ɪə": "diphtongue i-eu, comme dans here",
  "eə": "diphtongue è-eu, comme dans hair",
  "t": "son t, comme dans top (-ed après un son sourd : worked)",
  "d": "son d, comme dans dog (-ed après un son sonore : played)",
  "s": "son s, comme dans sun (-s après un son sourd : books)",
  "z": "son z, comme dans zoo (-s après un son sonore : dogs)",
  "p": "son p, comme dans pen", "b": "son b, comme dans big", "k": "son k, comme dans cat",
  "g": "son g, comme dans go", "f": "son f, comme dans fish", "v": "son v, comme dans very",
  "m": "son m, comme dans man", "n": "son n, comme dans no", "l": "son l, comme dans leg",
  "ɪz": "son iz : -es après s, z, ch, sh (buses, watches)",
  "ɪd": "son id : -ed après t ou d (wanted, needed)",
  "ˈ": "accent tonique : la syllabe qui suit se prononce plus fort",
  "ː": "voyelle longue",
};
const motifSons = o.motifDe(Object.keys(SONS));
const motifTranscription = /(?<![\p{L}\p{N}/])\/[^\/\s]{1,16}\/(?![\p{L}\p{N}/])/gu;
const SPECIAUX = /[θðʃʒŋɪʊæʌɑɒɔəɜˈː]/u; // au moins un signe phonetique : pas une date « 12/05 »

Symboles.enregistrer({
  id: "phonetique", rang: 1, matieres: ANGLAIS,
  trouver(texte) {
    const trouves = [];
    o.parcourir(motifTranscription, texte, (mot, i) => {
      const contenu = mot.slice(1, -1);
      if (!SPECIAUX.test(contenu) && !SONS[contenu]) return;
      let sens;
      if (SONS[contenu]) {
        sens = `${mot} : ${SONS[contenu]}`;
      } else {
        const sons = [];
        o.parcourir(motifSons, contenu, (s) => { if (SPECIAUX.test(s) && !sons.includes(s)) sons.push(s); });
        const detail = sons.slice(0, 3).map((s) => `${s} = ${SONS[s].split(",")[0]}`).join(" ; ");
        sens = `${mot} : prononciation (alphabet phonétique)${detail ? ` — ${detail}` : ""}`;
      }
      trouves.push({ debut: i, fin: i + mot.length, sens, classe: "phonetique" });
    });
    return trouves;
  },
});

Symboles.dictionnaire({
  id: "abreviations-anglais", matieres: ANGLAIS,
  entrees: {
    sb: "somebody : quelqu'un",
    sth: "something : quelque chose",
    BV: "base verbale : le verbe sans to (play, go, be)",
    "V-ing": "verbe + -ing (playing) : action en cours, ou verbe employé comme un nom",
    "V-ed": "verbe + -ed (played) : prétérit ou participe passé d'un verbe régulier",
    CECRL: "Cadre européen commun de référence pour les langues : il définit les niveaux A1 à C2",
    A1: "niveau A1 du CECRL (découverte) : expressions familières très simples",
    A2: "niveau A2 du CECRL (intermédiaire ou de survie) : échanges simples sur des sujets familiers",
    B1: "niveau B1 du CECRL (seuil) : se débrouiller, raconter, donner son avis simplement",
    B2: "niveau B2 du CECRL (avancé) : comprendre l'essentiel de textes complexes, s'exprimer avec aisance",
    C1: "niveau C1 du CECRL (autonome)",
    C2: "niveau C2 du CECRL (maîtrise)",
    LV1: "langue vivante 1 : la première langue étrangère étudiée",
    LV2: "langue vivante 2 : la deuxième langue étrangère étudiée",
    UK: "United Kingdom : le Royaume-Uni (Angleterre, Écosse, pays de Galles, Irlande du Nord)",
    US: "United States : les États-Unis",
    USA: "United States of America : les États-Unis d'Amérique",
  },
});

// Une structure de grammaire : des elements relies par « + », dont au moins un mot de grammaire
// (BE, HAVE, V-ing, BV...) : « sujet + BE + V-ing », « HAVE + participe passé ».
const ELEMENTS = [
  "participe passé", "base verbale", "complément", "adjectif", "sujet", "verbe", "nom",
  "BE", "HAVE", "DO", "DID", "WILL", "V-ing", "V-ed", "BV", "not", "to", "will", "would", "can",
  "could", "must", "should", "going to", "used to", "-ing", "-ed", "-s", "-er", "more", "the most",
];
const GRAMMAIRE = /BE|HAVE|DO|DID|WILL|V-ing|V-ed|BV|-ing|-ed|participe/;
const ELEMENT = String.raw`(?:${o.alternatives(ELEMENTS)})(?![\p{L}\p{N}])`;
const motifStructure = new RegExp(String.raw`(?<![\p{L}\p{N}-])${ELEMENT}(?:\s*\+\s*${ELEMENT})+`, "gu");
Symboles.enregistrer({
  id: "structures-anglais", matieres: ANGLAIS,
  mettreEnForme(texte) {
    const zones = [];
    o.parcourir(motifStructure, texte, (mot, i) => {
      if (GRAMMAIRE.test(mot)) zones.push({ debut: i, fin: i + mot.length, classe: "formule-texte" });
    });
    return zones;
  },
});
})();
