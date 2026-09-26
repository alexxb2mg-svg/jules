// Extension rappels-sciences : les bulles de rappel des sciences (famille `rappels`, docs/EXTENSIONS.md).
//   - unites (s, kg, N, km/h...) apres un nombre, apres « en », ou nommees : « watts (W) » ;
//   - especes chimiques (CO₂, Cu²⁺, NaCl...) avec leur composition, et les 118 elements ;
//   - formules ecrites dans le texte (« P = m × g ») mises en gras, leurs lettres et unites annotees.
// Des donnees (DICOS) et des regles enregistrees aupres du coeur (jules/web/static/symboles.js).
// Code execute dans la page de l'eleve : controle au chargement comme un gabarit de figure.
"use strict";

(() => {
const SCIENCES = ["physique-chimie", "svt", "mathematiques", "technologie"];
const DICOS = {
  // Unites. Celles d'une seule lettre (m, s, g, N...) ne sont reconnues qu'apres un nombre
  // (« 98 N ») ou apres « en » (« en m ») : jamais le « m » d'une formule ni un mot.
  unites: {
    "s": "secondes",
    "ms": "millisecondes",
    "min": "minutes",
    "h": "heures",
    "m": "mètres",
    "km": "kilomètres",
    "cm": "centimètres",
    "mm": "millimètres",
    "µm": "micromètres",
    "nm": "nanomètres",
    "m²": "mètres carrés",
    "cm²": "centimètres carrés",
    "km²": "kilomètres carrés",
    "m³": "mètres cubes",
    "dm³": "décimètres cubes",
    "cm³": "centimètres cubes",
    "L": "litres",
    "dL": "décilitres",
    "cL": "centilitres",
    "mL": "millilitres",
    "g": "grammes",
    "kg": "kilogrammes",
    "mg": "milligrammes",
    "N": "newtons (unité de force et de poids)",
    "J": "joules (unité d'énergie)",
    "kJ": "kilojoules : 1 000 joules",
    "Wh": "wattheures (unité d'énergie)",
    "kWh": "kilowattheures (unité d'énergie) : 1 kWh = 3 600 000 J",
    "W": "watts (unité de puissance)",
    "kW": "kilowatts : 1 000 watts",
    "MW": "mégawatts : un million de watts",
    "V": "volts (unité de tension)",
    "mV": "millivolts",
    "kV": "kilovolts : 1 000 volts",
    "A": "ampères (unité d'intensité)",
    "mA": "milliampères : un millième d'ampère",
    "Ω": "ohms (unité de résistance)",
    "kΩ": "kilo-ohms : 1 000 ohms",
    "Hz": "hertz (unité de fréquence) : nombre de vibrations par seconde",
    "kHz": "kilohertz : 1 000 hertz",
    "MHz": "mégahertz : un million de hertz",
    "°C": "degrés Celsius",
    "K": "kelvins (unité de température)",
    "Pa": "pascals (unité de pression)",
    "hPa": "hectopascals : 100 pascals",
    "dB": "décibels (niveau sonore)",
    "m/s": "mètres par seconde",
    "km/h": "kilomètres par heure",
    "km/s": "kilomètres par seconde",
    "m/min": "mètres par minute",
    "g/cm³": "grammes par centimètre cube",
    "g/mL": "grammes par millilitre",
    "g/L": "grammes par litre",
    "kg/L": "kilogrammes par litre",
    "kg/m³": "kilogrammes par mètre cube",
    "N/kg": "newtons par kilogramme",
    "ua": "unité astronomique : environ 150 millions de km (distance Terre-Soleil)",
    "al": "année-lumière : environ 9 500 milliards de km",
  },

  // Les 118 elements : symbole -> nom.
  elements: {
    H: "hydrogène", He: "hélium", Li: "lithium", Be: "béryllium", B: "bore", C: "carbone", N: "azote",
    O: "oxygène", F: "fluor", Ne: "néon", Na: "sodium", Mg: "magnésium", Al: "aluminium", Si: "silicium",
    P: "phosphore", S: "soufre", Cl: "chlore", Ar: "argon", K: "potassium", Ca: "calcium", Sc: "scandium",
    Ti: "titane", V: "vanadium", Cr: "chrome", Mn: "manganèse", Fe: "fer", Co: "cobalt", Ni: "nickel",
    Cu: "cuivre", Zn: "zinc", Ga: "gallium", Ge: "germanium", As: "arsenic", Se: "sélénium", Br: "brome",
    Kr: "krypton", Rb: "rubidium", Sr: "strontium", Y: "yttrium", Zr: "zirconium", Nb: "niobium",
    Mo: "molybdène", Tc: "technétium", Ru: "ruthénium", Rh: "rhodium", Pd: "palladium", Ag: "argent",
    Cd: "cadmium", In: "indium", Sn: "étain", Sb: "antimoine", Te: "tellure", I: "iode", Xe: "xénon",
    Cs: "césium", Ba: "baryum", La: "lanthane", Ce: "cérium", Pr: "praséodyme", Nd: "néodyme",
    Pm: "prométhium", Sm: "samarium", Eu: "europium", Gd: "gadolinium", Tb: "terbium", Dy: "dysprosium",
    Ho: "holmium", Er: "erbium", Tm: "thulium", Yb: "ytterbium", Lu: "lutécium", Hf: "hafnium",
    Ta: "tantale", W: "tungstène", Re: "rhénium", Os: "osmium", Ir: "iridium", Pt: "platine", Au: "or",
    Hg: "mercure", Tl: "thallium", Pb: "plomb", Bi: "bismuth", Po: "polonium", At: "astate", Rn: "radon",
    Fr: "francium", Ra: "radium", Ac: "actinium", Th: "thorium", Pa: "protactinium", U: "uranium",
    Np: "neptunium", Pu: "plutonium", Am: "américium", Cm: "curium", Bk: "berkélium", Cf: "californium",
    Es: "einsteinium", Fm: "fermium", Md: "mendélévium", No: "nobélium", Lr: "lawrencium",
    Rf: "rutherfordium", Db: "dubnium", Sg: "seaborgium", Bh: "bohrium", Hs: "hassium", Mt: "meitnérium",
    Ds: "darmstadtium", Rg: "roentgenium", Cn: "copernicium", Nh: "nihonium", Fl: "flérovium",
    Mc: "moscovium", Lv: "livermorium", Ts: "tennesse", Og: "oganesson",
  },

  // Symboles d'elements qui sont aussi des mots (« Au debut », « Si tu... ») : reconnus seulement
  // hors d'une phrase (entre parentheses, dans une liste, avant un nombre).
  elementsAmbigus: ["Au", "La", "Ne", "Si", "Ce", "Se", "Te", "Es", "Os", "Ni", "No", "In", "As", "At", "Ta", "Ra", "Pu", "Ho", "Er", "Pa", "Po", "Am", "Bi", "Ba", "Ma", "Fr", "Mt", "Md", "Ds", "Db", "Mc", "Cm", "Tm", "Nd", "Pr", "Ts", "Eu", "Lu", "Re", "Nb", "Sn"],

  // Especes chimiques courantes : formule -> nom (la composition est ajoutee automatiquement).
  especes: {
    "H₂O": "eau", "CO₂": "dioxyde de carbone", "CO": "monoxyde de carbone (gaz toxique)",
    "O₂": "dioxygène", "O₃": "ozone", "N₂": "diazote", "H₂": "dihydrogène", "Cl₂": "dichlore",
    "CH₄": "méthane (gaz de ville)", "C₃H₈": "propane", "C₄H₁₀": "butane", "C₂H₆O": "éthanol (alcool)",
    "C₆H₁₂O₆": "glucose", "C₁₂H₂₂O₁₁": "saccharose (sucre)", "N₂O": "protoxyde d'azote",
    "NO₂": "dioxyde d'azote", "SO₂": "dioxyde de soufre", "NH₃": "ammoniac", "NaCl": "chlorure de sodium (sel)",
    "HCl": "chlorure d'hydrogène (acide chlorhydrique en solution)", "NaOH": "hydroxyde de sodium (soude)",
    "CaCO₃": "carbonate de calcium (calcaire)", "Ca(OH)₂": "hydroxyde de calcium (eau de chaux)",
    "Fe₂O₃": "oxyde de fer III (rouille)", "Fe₃O₄": "oxyde magnétique de fer", "CuO": "oxyde de cuivre II",
    "CuSO₄": "sulfate de cuivre", "H⁺": "ion hydrogène (rend une solution acide)",
    "HO⁻": "ion hydroxyde (rend une solution basique)", "OH⁻": "ion hydroxyde (rend une solution basique)",
    "H₃O⁺": "ion oxonium", "Na⁺": "ion sodium", "Cl⁻": "ion chlorure", "K⁺": "ion potassium",
    "Ca²⁺": "ion calcium", "Mg²⁺": "ion magnésium", "Cu²⁺": "ion cuivre II (bleu en solution)",
    "Fe²⁺": "ion fer II", "Fe³⁺": "ion fer III", "Zn²⁺": "ion zinc", "Ag⁺": "ion argent",
    "Al³⁺": "ion aluminium", "SO₄²⁻": "ion sulfate", "NO₃⁻": "ion nitrate", "CO₃²⁻": "ion carbonate",
  },
};

const o = Symboles.outils;
const INDICES = "₀₁₂₃₄₅₆₇₈₉", EXPOSANTS = "⁰¹²³⁴⁵⁶⁷⁸⁹";
const AMBIGUS = new Set(DICOS.elementsAmbigus);
const motifUnites = o.motifDe(Object.keys(DICOS.unites));
const motifChimie = /\(?(?:[A-Z][a-z]?[₀-₉]*|\((?:[A-Z][a-z]?[₀-₉]*)+\)[₀-₉]*)+[⁰¹²³⁴⁵⁶⁷⁸⁹]*[⁺⁻]?/gu;

// --- unites ------------------------------------------------------------------------------------
Symboles.enregistrer({
  id: "unites", rang: 3, matieres: [...SCIENCES, "geographie"],
  trouver(texte, ctx) {
    const trouves = [];
    o.parcourir(motifUnites, texte, (mot, i) => {
      const fin = i + mot.length;
      if ((i > 0 && /[\p{L}_'’]/u.test(texte[i - 1])) || (fin < texte.length && o.COLLE.test(texte[fin]))) return;
      const courte = mot.length === 1 || DICOS.elements[mot]; // « m », « N », « Pa » : il faut un nombre ou « en »
      const precede = o.avant(texte, i - 1);
      const nomme = o.designe(o.motDevantParenthese(texte, i, fin), DICOS.unites[mot]); // « watts (W) »
      if (courte && !/\d/.test(precede) && !nomme && !["en", "des", "les", "par"].includes(o.motAvant(texte, i))) return;
      // Dans une formule, « mg » fait de lettres de la formule (m × g) n'est pas une unite.
      const variables = ctx.variables || {};
      if (ctx.formule && !/\d/.test(precede) && [...mot].every((c) => variables[c] || !/\p{L}/u.test(c))) return;
      trouves.push({ debut: i, fin, sens: `${mot} : ${DICOS.unites[mot]}`, classe: "unite" });
    });
    return trouves;
  },
});

// --- chimie : especes (composition) et elements ------------------------------------------------
const chiffres = (s, table) => Number([...s].map((c) => table.indexOf(c)).join("")) || 1;
const elision = (nom) => (/^[aeiouyéèêh]/i.test(nom) ? `d'${nom}` : `de ${nom}`);

function composition(formule) {
  const corps = formule.replace(/[⁰¹²³⁴⁵⁶⁷⁸⁹]*[⁺⁻]$/u, "");
  const compte = new Map();
  const lire = (morceau, facteur) => {
    for (const m of morceau.matchAll(/\(([^)]+)\)([₀-₉]*)|([A-Z][a-z]?)([₀-₉]*)/gu)) {
      if (m[1]) lire(m[1], facteur * (m[2] ? chiffres(m[2], INDICES) : 1));
      else compte.set(m[3], (compte.get(m[3]) || 0) + facteur * (m[4] ? chiffres(m[4], INDICES) : 1));
    }
  };
  lire(corps, 1);
  if ([...compte.keys()].some((s) => !DICOS.elements[s])) return null;
  return [...compte].map(([s, n]) => `${n} atome${n > 1 ? "s" : ""} ${elision(DICOS.elements[s])}`).join(", ");
}

function charge(formule) {
  const m = formule.match(/([⁰¹²³⁴⁵⁶⁷⁸⁹]*)([⁺⁻])$/u);
  if (!m) return "";
  const n = m[1] ? chiffres(m[1], EXPOSANTS) : 1;
  return `${n} charge${n > 1 ? "s" : ""} ${m[2] === "⁺" ? "positive" : "négative"}${n > 1 ? "s" : ""}`;
}

function sensChimique(formule) {
  const nom = DICOS.especes[formule];
  const compo = composition(formule);
  if (!compo) return null;
  const ion = /[⁺⁻]$/.test(formule);
  if (!nom && !ion && !compo.includes(", ") && compo.startsWith("1 ")) return null; // un element seul
  const detail = [compo, ion ? charge(formule) : ""].filter(Boolean).join(" ; ");
  return nom ? `${nom} : ${detail}` : `${ion ? "ion" : "molécule"} : ${detail}`;
}

Symboles.enregistrer({
  id: "chimie-especes", rang: 2, matieres: ["physique-chimie", "svt"],
  trouver(texte) {
    const trouves = [];
    o.parcourir(motifChimie, texte, (mot, i) => {
      if (mot.startsWith("(") || !o.isole(texte, i, i + mot.length)) return;
      const multiple = /[₀-₉⁺⁻]/u.test(mot) || DICOS.especes[mot] || ((mot.match(/[A-Z]/g) || []).length > 1 && /[a-z]/.test(mot));
      if (!multiple) return;
      const sens = sensChimique(mot);
      if (sens) trouves.push({ debut: i, fin: i + mot.length, sens: `${mot} : ${sens}`, classe: "chimie" });
    });
    return trouves;
  },
});

Symboles.enregistrer({
  id: "chimie-elements", rang: 4, matieres: ["physique-chimie", "svt"],
  trouver(texte, ctx) {
    const trouves = [];
    o.parcourir(/[A-Z][a-z]?/gu, texte, (mot, i) => {
      const nom = DICOS.elements[mot];
      if (!nom || !o.isole(texte, i, i + mot.length)) return;
      if (mot.length === 1 || AMBIGUS.has(mot)) {
        // « watts (W) » : c'est l'unite, pas le tungstene.
        if (DICOS.unites[mot] && o.designe(o.motDevantParenthese(texte, i, i + mot.length), DICOS.unites[mot])) return;
        // Jamais suivi d'un mot : « Au début » et « Si tu » ne sont ni de l'or ni du silicium.
        if (/\p{L}/u.test(o.apres(texte, i + mot.length))) return;
        const precedent = o.avant(texte, i - 1);
        const equationChimique = Boolean(ctx.zone && /[₀-₉→]/u.test(ctx.zone.textContent));
        if (mot.length === 1) {
          // Une lettre seule (O, C, N...) : dans une equation chimique, ou dans une liste hors formule.
          if (ctx.formule ? !equationChimique : !precedent || !"(,;:/+".includes(precedent)) return;
        } else if (precedent && !"(,;:/+→".includes(precedent)) {
          return;
        }
      }
      trouves.push({ debut: i, fin: i + mot.length, sens: `${mot} : ${nom} (élément chimique)`, classe: "chimie" });
    });
    return trouves;
  },
});

// --- formules ecrites dans le texte : en gras --------------------------------------------------
// Des termes courts relies par des operateurs, avec au moins un « = », « → » ou « ≈ ». Termes :
// nombre (avec son unite), unite seule (km/h → m/s), lettre(s) de grandeur, espece chimique.
const UNITES = o.alternatives(Object.keys(DICOS.unites));
const NOMBRE = String.raw`\d+(?:[  ]\d{3})*(?:,\d+)?(?:[  ]?(?:${UNITES})(?![\p{L}\p{N}]))?`;
const UNITE_SEULE = String.raw`(?:${o.alternatives(Object.keys(DICOS.unites).filter((u) => u.length > 1))})(?![\p{L}\p{N}])`;
const TERME = String.raw`(?:${NOMBRE}|${UNITE_SEULE}|(?:\d+[  ])?(?:[A-Z][a-z]?[₀-₉]*)+[⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻]*(?![\p{L}\p{N}])|[½¼¾]|[\p{L}][\p{L}0-9₀-₉]{0,2}[²³]?(?![\p{L}\p{N}])|\([^()\n]{1,30}\))`;
const motifFormule = new RegExp(String.raw`(?<![\p{L}\p{N}])${TERME}(?:\s*[=×÷+−→≈≤≥<>]\s*${TERME})+`, "gu");

Symboles.enregistrer({
  id: "formules", formule: true, matieres: SCIENCES,
  mettreEnForme(texte) {
    const zones = [];
    o.parcourir(motifFormule, texte, (mot, i) => {
      if (/[=→≈≤≥<>]/.test(mot)) zones.push({ debut: i, fin: i + mot.length, classe: "formule-texte" });
    });
    return zones;
  },
});
})();
