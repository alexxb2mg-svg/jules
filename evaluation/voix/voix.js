// Releve des voix de synthese vocale d'un navigateur (spec ADAPTATIONS, EX-006 : verification manuelle
// complementaire, non bloquante). Affiche chaque voix avec sa langue et localService, puis le verdict du
// filtre de jules/web/static/lecture-vocale.js : seules les voix localService === true comptent.
//
// Deux facons de le lancer :
//   1. Sur un ordinateur, avec Node 22 ou plus (fetch et WebSocket integres) et un navigateur de la
//      famille Chromium, en headless :
//        node evaluation/voix/voix.js "<chemin de l'executable du navigateur>" [--tout]
//      Attention : un navigateur headless peut ne voir aucune voix alors que le meme navigateur, ouvert
//      normalement, en voit (mesure du 26/09/2026). Le releve headless est un indice, pas une preuve.
//   2. Sur l'appareil de l'eleve (tablette...), dans le navigateur qu'il utilise : coller tout ce fichier
//      dans la console de developpement d'une page de Jules. Plus simple encore : ouvrir la page parent
//      sur cet appareil, la carte « Lecture vocale » donne le meme verdict (EX-007).
"use strict";

// Execute dans la page du navigateur : attend les voix (liste parfois vide avant voiceschanged).
function releverVoix() {
  return new Promise((fin) => {
    const releve = () => speechSynthesis.getVoices().map((v) => ({ nom: v.name, langue: v.lang, locale: v.localService === true }));
    const essai = () => { const v = releve(); if (v.length) fin(v); };
    speechSynthesis.addEventListener("voiceschanged", essai);
    essai();
    setTimeout(() => fin(releve()), 4000);
  });
}
const EXPRESSION = `(${releverVoix.toString()})()`;

// Noms et langues viennent du navigateur : retours a la ligne et caracteres de controle neutralises
// avant l'ecriture, pour qu'une valeur ne puisse pas fabriquer de fausses lignes dans le releve.
// Retours a la ligne supprimes (forme reconnue par CodeQL, js/log-injection), autres caracteres de
// controle et separateurs de ligne Unicode remplaces par « ? ».
function propre(texte) {
  return String(texte)
    .replace(/\r|\n/g, "")
    .replace(/[\u0000-\u001f\u007f-\u009f\u2028\u2029]/g, "?");
}

function afficher(voix) {
  const locales = voix.filter((v) => v.locale);
  // Par defaut : les voix locales et les voix francaises ; --tout pour la liste complete.
  const tout = typeof process !== "undefined" && process.argv && process.argv.includes("--tout");
  for (const v of voix) {
    if (tout || v.locale || /^fr\b/i.test(v.langue)) console.log(propre(`${v.locale ? "LOCALE  " : "EN LIGNE"}  ${v.langue}  ${v.nom}`));
  }
  const nbFr = locales.filter((v) => /^fr\b/i.test(v.langue)).length;
  console.log(propre(`total ${Number(voix.length)}, locales ${Number(locales.length)}, locales fr ${Number(nbFr)}`));
  console.log(locales.length ? "Verdict : lecture vocale DISPONIBLE" : "Verdict : lecture vocale INDISPONIBLE");
  return locales.length;
}

if (typeof window !== "undefined") {
  // Mode 2 : console du navigateur.
  releverVoix().then(afficher);
} else {
  // Mode 1 : Node pilote un navigateur headless par le protocole de debogage.
  const { spawn } = require("node:child_process");
  const os = require("node:os");
  const path = require("node:path");
  const fs = require("node:fs");

  const exe = process.argv[2];
  if (!exe) {
    console.error('usage : node voix.js "<chemin de l\'executable du navigateur>"');
    process.exit(2);
  }
  const port = 9300 + Math.floor(Math.random() * 600);
  const profil = fs.mkdtempSync(path.join(os.tmpdir(), "jules-voix-"));
  const navigateur = spawn(exe, ["--headless=new", `--remote-debugging-port=${port}`, `--user-data-dir=${profil}`, "about:blank"]);
  const pause = (ms) => new Promise((r) => setTimeout(r, ms));
  const quitter = (code) => { navigateur.kill(); process.exit(code); };
  setTimeout(() => { console.error("delai depasse (15 s)"); quitter(1); }, 15000);

  (async () => {
    let cible = null;
    for (let i = 0; i < 30 && !cible; i++) {
      try {
        const pages = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
        cible = pages.find((p) => p.type === "page");
      } catch (_) { /* le navigateur demarre */ }
      if (!cible) await pause(300);
    }
    if (!cible) { console.error("navigateur injoignable"); quitter(1); }
    const ws = new WebSocket(cible.webSocketDebuggerUrl);
    await new Promise((r) => { ws.onopen = r; });
    ws.onmessage = (m) => {
      const d = JSON.parse(m.data);
      if (d.id !== 1) return;
      afficher((d.result && d.result.result && d.result.result.value) || []);
      ws.close();
      quitter(0);
    };
    ws.send(JSON.stringify({ id: 1, method: "Runtime.evaluate", params: { expression: EXPRESSION, awaitPromise: true, returnByValue: true } }));
  })();
}
