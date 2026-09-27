// Extension rappels-musique : nuances (p, mf, ff...), figures de notes et signes de la portee
// (famille `rappels`, docs/EXTENSIONS.md). Matiere : education musicale.
"use strict";

const MUSIQUE = ["education-musicale"];

// Nuances : une ou quelques lettres isolees. « p. 12 » (une page) ou « l'f » ne sont pas des nuances.
const NUANCES = {
  ppp: "pianississimo : le plus doucement possible",
  pp: "pianissimo : très doucement",
  p: "piano : doucement",
  mp: "mezzo piano : assez doucement",
  mf: "mezzo forte : assez fort",
  f: "forte : fort",
  ff: "fortissimo : très fort",
  fff: "fortississimo : le plus fort possible",
};

Symboles.enregistrer({
  id: "nuances", matieres: MUSIQUE, rang: 2,
  trouver(texte) {
    const trouves = [];
    const motif = /(?<![\p{L}\p{N}_'’.])(ppp|pp|p|mp|mf|fff|ff|f)(?![\p{L}\p{N}_'’.])/gu;
    for (const m of texte.matchAll(motif)) {
      trouves.push({ debut: m.index, fin: m.index + m[0].length, sens: `${m[0]} : ${NUANCES[m[0]]}`, classe: "abreviation" });
    }
    return trouves;
  },
});

Symboles.dictionnaire({
  id: "signes-musicaux", matieres: MUSIQUE, classe: "abreviation",
  entrees: {
    "cresc.": "crescendo : de plus en plus fort",
    "decresc.": "decrescendo : de moins en moins fort",
    "dim.": "diminuendo : de moins en moins fort",
    "rit.": "ritardando : en ralentissant",
    "accel.": "accelerando : en accélérant",
    BPM: "battements par minute : la vitesse de la pulsation (le tempo)",
    "𝄞": "clé de sol : les notes se lisent à partir du sol, sur la 2e ligne",
    "𝄢": "clé de fa : les notes se lisent à partir du fa, sur la 4e ligne",
    "𝅝": "ronde : dure 4 temps",
    "𝅗𝅥": "blanche : dure 2 temps",
    "♩": "noire : dure 1 temps",
    "♪": "croche : dure un demi-temps",
    "♫": "deux croches : un temps en tout",
    "𝄽": "soupir : un silence d'un temps",
    "𝄼": "demi-pause : un silence de deux temps",
    "𝄻": "pause : un silence de quatre temps",
    "♯": "dièse : la note est jouée un demi-ton plus haut",
    "♭": "bémol : la note est jouée un demi-ton plus bas",
    "♮": "bécarre : annule le dièse ou le bémol",
    "𝄐": "point d'orgue : on tient la note plus longtemps",
  },
});
