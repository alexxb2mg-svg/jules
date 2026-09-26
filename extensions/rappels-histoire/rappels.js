// Extension rappels-histoire : bulles de rappel d'histoire, de geographie et d'EMC (famille `rappels`).
//   - siecles et millenaires en chiffres romains : « XIXe siècle » -> le 19e siecle, de 1801 a 1900
//     (a rebours avant Jesus-Christ) ; « Ve République » -> 5e ;
//   - numeros de regne : « Louis XIV » -> 14, « Napoléon Ier » -> premier ;
//   - av. J.-C., apr. J.-C. ; sigles (URSS, ONU, PIB, ZEE...).
"use strict";

(() => {
const HGE = ["histoire", "geographie", "emc"];
const o = Symboles.outils;
const VALEURS = { I: 1, V: 5, X: 10, L: 50, C: 100 };
const ROMAINS = [[100, "C"], [90, "XC"], [50, "L"], [40, "XL"], [10, "X"], [9, "IX"], [5, "V"], [4, "IV"], [1, "I"]];

// Un nombre romain valide (I a CCCXCIX), sinon null : « CIV » oui, « IIV » non.
function romain(s) {
  let n = 0;
  for (let i = 0; i < s.length; i++) {
    const v = VALEURS[s[i]], suivant = VALEURS[s[i + 1]] || 0;
    n += v < suivant ? -v : v;
  }
  let ecrit = "", reste = n;
  for (const [v, r] of ROMAINS) while (reste >= v) { ecrit += r; reste -= v; }
  return ecrit === s && n > 0 ? n : null;
}
const ordinal = (n) => (n === 1 ? "1er" : `${n}e`);

// « XIXe siècle », « IIIe millénaire », « Ve République », « Ier siècle av. J.-C. »
const motifSiecle = /(?<![\p{L}\p{N}])([IVXLC]+)(er|e|ème)(?![\p{L}\p{N}])(\s+(?:siècles?|millénaires?))?/gu;
Symboles.enregistrer({
  id: "siecles", rang: 2, matieres: HGE,
  trouver(texte) {
    const trouves = [];
    o.parcourir(motifSiecle, texte, (mot, i, m) => {
      const n = romain(m[1]);
      if (!n || (m[2] === "er" && n !== 1)) return;
      // « Le », « Ce » : une seule lettre n'est un nombre romain que si c'est I, V ou X, ou devant « siècle ».
      if (m[1].length === 1 && !m[3] && !"IVX".includes(m[1])) return;
      const suite = texte.slice(i + mot.length, i + mot.length + 14);
      const avantJC = /^\s*av(\.|ant)\s*J/.test(suite);
      let sens = `${ordinal(n)} (chiffres romains)`;
      if (m[3] && /siècle/.test(m[3])) {
        sens = avantJC
          ? `le ${ordinal(n)} siècle avant J.-C. : de ${n * 100} à ${(n - 1) * 100 + 1} av. J.-C. (on compte à rebours)`
          : `le ${ordinal(n)} siècle : de ${(n - 1) * 100 + 1} à ${n * 100}`;
      } else if (m[3]) {
        sens = avantJC
          ? `le ${ordinal(n)} millénaire avant J.-C. : de ${n * 1000} à ${(n - 1) * 1000 + 1} av. J.-C.`
          : `le ${ordinal(n)} millénaire : de ${(n - 1) * 1000 + 1} à ${n * 1000}`;
      }
      // La bulle porte sur le nombre romain seulement ; « siècle » reste un mot normal.
      trouves.push({ debut: i, fin: i + m[1].length + m[2].length, sens: `${m[1]}${m[2]} : ${sens}`, classe: "date" });
    });
    return trouves;
  },
});

// « Louis XIV », « Henri IV », « Charles V » : un nombre romain juste apres un nom propre.
const motifRegne = /(?<=\p{Lu}\p{Ll}+\s)([IVXLC]{2,}|[IVX])(?![\p{L}\p{N}])/gu;
Symboles.enregistrer({
  id: "numeros-de-regne", rang: 3, matieres: HGE,
  trouver(texte) {
    const trouves = [];
    o.parcourir(motifRegne, texte, (mot, i) => {
      const n = romain(mot);
      if (n) trouves.push({ debut: i, fin: i + mot.length, sens: `${mot} : ${n} (chiffres romains)`, classe: "date" });
    });
    return trouves;
  },
});

Symboles.dictionnaire({
  id: "ere-chretienne", matieres: HGE, rang: 1, classe: "date",
  entrees: {
    "av. J.-C.": "avant Jésus-Christ : on compte les années à rebours à partir de l'an 1",
    "apr. J.-C.": "après Jésus-Christ",
    "J.-C.": "Jésus-Christ : sa naissance sert de point de départ pour compter les années",
  },
});

Symboles.dictionnaire({
  id: "sigles-histoire-geo", matieres: HGE,
  entrees: {
    URSS: "Union des républiques socialistes soviétiques (1922-1991)",
    ONU: "Organisation des Nations unies (créée en 1945)",
    SDN: "Société des Nations (1920-1946)",
    OTAN: "Organisation du traité de l'Atlantique Nord : alliance militaire créée en 1949",
    CECA: "Communauté européenne du charbon et de l'acier (1951)",
    CEE: "Communauté économique européenne (1957)",
    UE: "Union européenne (depuis 1992)",
    RDA: "République démocratique allemande : l'Allemagne de l'Est (1949-1990)",
    RFA: "République fédérale d'Allemagne : l'Allemagne de l'Ouest, puis l'Allemagne réunifiée",
    USA: "États-Unis d'Amérique",
    STO: "Service du travail obligatoire (1943-1944)",
    FFI: "Forces françaises de l'intérieur : la Résistance armée (1944)",
    CNR: "Conseil national de la Résistance (1943)",
    FLN: "Front de libération nationale (Algérie)",
    PCF: "Parti communiste français",
    SFIO: "Section française de l'Internationale ouvrière : le parti socialiste",
    DDHC: "Déclaration des droits de l'homme et du citoyen (1789)",
    CIDE: "Convention internationale des droits de l'enfant (1989)",
    JDC: "Journée défense et citoyenneté",
    ONG: "organisation non gouvernementale",
    PIB: "produit intérieur brut : la richesse produite par un pays en un an",
    IDH: "indice de développement humain, de 0 à 1 (santé, éducation, revenu)",
    DROM: "département et région d'outre-mer",
    ZEE: "zone économique exclusive : bande de mer d'environ 370 km au large des côtes",
    FTN: "firme transnationale : entreprise implantée dans plusieurs pays",
    "hab./km²": "habitants par kilomètre carré (densité de population)",
  },
});
})();
