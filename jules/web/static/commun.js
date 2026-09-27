// Jules - fonctions communes aux pages eleve et parent.
// Securite : tout contenu venant du serveur ou du modele passe par MS.echapper (ou MS.markdown,
// qui echappe avant de mettre en forme) avant d'aller dans innerHTML.
"use strict";

const MS = {
  // Cache de lecture (docs/spec/NAVIGATION.md, EX-210) : la page et la barre de navigation demandent les memes
  // listes sans se connaitre ; une seule requete reseau par couple (chemin, parametres) et par chargement de page.
  // - liste blanche : seuls ces trois chemins, en GET, sont gardes (cle = chemin + parametres) ;
  // - toute requete qui n'est pas un GET vide le cache (sans `method`, c'est un GET) ;
  // - une erreur n'est jamais gardee ; une requete en cours est partagee ;
  // - chaque lecture rend une copie (structuredClone) : personne ne partage le meme objet.
  CHEMINS_EN_CACHE: Object.freeze([
    "/api/eleve/fiches_visuelles/notions",
    "/api/eleve/cours/parcours",
    "/api/eleve/studio/notions",
  ]),
  _cache: new Map(),

  async api(chemin, options = {}) {
    const methode = String(options.method || "GET").toUpperCase();
    if (methode !== "GET") {
      MS._cache.clear();
      return MS._appel(chemin, options);
    }
    const url = new URL(chemin, location.href);
    if (url.origin !== location.origin || !MS.CHEMINS_EN_CACHE.includes(url.pathname)) {
      return MS._appel(chemin, options);
    }
    const cle = url.pathname + url.search;
    let promesse = MS._cache.get(cle);
    if (!promesse) {
      promesse = MS._appel(chemin, options);
      MS._cache.set(cle, promesse);
      promesse.catch(() => { if (MS._cache.get(cle) === promesse) MS._cache.delete(cle); });
    }
    return structuredClone(await promesse);
  },

  async _appel(chemin, options) {
    const reponse = await fetch(chemin, { credentials: "same-origin", ...options });
    if (reponse.status === 401) {
      const err = new Error("code requis");
      err.code = 401;
      throw err;
    }
    let corps = null;
    try { corps = await reponse.json(); } catch (_) { corps = null; }
    if (!reponse.ok) {
      const err = new Error((corps && corps.detail) || `Erreur ${reponse.status}`);
      err.code = reponse.status;
      throw err;
    }
    return corps;
  },

  // Adresse d'une liste par matiere : ecrite ici une seule fois, pour que la page et la barre demandent la meme
  // cle au cache (EX-210).
  cheminMatiere(base, matiere) {
    return base + (matiere ? `?matiere=${encodeURIComponent(matiere)}` : "");
  },

  // Matiere retenue d'une page a l'autre (EX-209) : cle `jules.matiere`, valeur = l'id de matiere seul.
  CLE_MATIERE: "jules.matiere",
  matiereRetenue() {
    try { return localStorage.getItem(MS.CLE_MATIERE) || null; } catch (_) { return null; }
  },
  retenirMatiere(id) {
    try { localStorage.setItem(MS.CLE_MATIERE, String(id)); } catch (_) { /* stockage indisponible : rien */ }
  },

  json(corps, methode = "POST") {
    return { method: methode, headers: { "Content-Type": "application/json" }, body: JSON.stringify(corps) };
  },

  // Point d'accroche « fin_de_seance » : a la fermeture de la page, un signal sans corps part vers
  // le serveur (sendBeacon survit a la fermeture d'un onglet, contrairement a fetch). Le serveur
  // ignore les signaux quand aucune seance n'est ouverte : plusieurs envois ne coutent rien.
  signalerFinDeSeance() {
    addEventListener("pagehide", () => {
      if (navigator.sendBeacon) navigator.sendBeacon("/api/seance/fin");
    });
  },

  appliquerCouleurs(couleurs) {
    const correspondance = {
      principale: "--p-principale", secondaire: "--p-secondaire", fond: "--p-fond",
      bulle_bot: "--p-bulle-bot", bulle_eleve: "--p-bulle-eleve",
    };
    for (const [cle, variable] of Object.entries(correspondance)) {
      if (couleurs && couleurs[cle]) document.documentElement.style.setProperty(variable, couleurs[cle]);
    }
  },

  // Leviers de l'eleve (EX-105, adaptations.css), lus dans /api/infos : `leviers` (valeurs brutes des
  // leviers regles, non neutres) et `leviers_css` (variables --adapt-* derivees par le serveur). Pose
  // sur <body> les variables et un attribut data-adapt-<levier> par levier regle ; tout est retire
  // d'abord, donc un second appel remplace le premier. Rien n'est pose quand tout est neutre (EX-102).
  // Renvoie les valeurs brutes, a transmettre telles quelles aux outils.
  appliquerLeviers(infos) {
    const corps = document.body;
    for (const nom of [...corps.getAttributeNames()]) if (nom.startsWith("data-adapt-")) corps.removeAttribute(nom);
    for (const nom of [...corps.style]) if (nom.startsWith("--adapt-")) corps.style.removeProperty(nom);
    const objet = (v) => (v && typeof v === "object" && !Array.isArray(v) ? v : {});
    const leviers = objet(infos && infos.leviers);
    for (const [variable, valeur] of Object.entries(objet(infos && infos.leviers_css))) {
      if (/^--adapt-[a-z-]+$/.test(variable)) corps.style.setProperty(variable, String(valeur));
    }
    const retenus = {};
    for (const [levier, valeur] of Object.entries(leviers)) {
      if (!/^[a-z][a-z-]*$/.test(levier)) continue;
      corps.setAttribute(`data-adapt-${levier}`, String(valeur));
      retenus[levier] = valeur;
    }
    return retenus;
  },

  sansAccents(texte) {
    return String(texte).toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  },

  echapper(texte) {
    return String(texte).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  },

  // Markdown minimal et sur : le texte est echappe AVANT toute mise en forme.
  markdown(source) {
    const enLigne = (t) => MS.echapper(t)
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/(^|[^*])\*([^*\s][^*]*?)\*/g, "$1<em>$2</em>")
      .replace(/`([^`]+)`/g, "<code>$1</code>");
    const lignes = String(source || "").replace(/\r/g, "").split("\n");
    const html = [];
    let liste = null;
    let paragraphe = [];
    let tableau = [];
    const fermerParagraphe = () => {
      if (paragraphe.length) html.push(`<p>${paragraphe.map(enLigne).join("<br>")}</p>`);
      paragraphe = [];
    };
    const fermerListe = () => { if (liste) { html.push(`</${liste}>`); liste = null; } };
    const fermerTableau = () => {
      if (!tableau.length) return;
      const rangs = tableau.filter((l) => !/^\s*\|?\s*:?-{2,}/.test(l));
      html.push("<table>" + rangs.map((l, i) => {
        const cellules = l.trim().replace(/^\||\|$/g, "").split("|");
        const balise = i === 0 ? "th" : "td";
        return "<tr>" + cellules.map((c) => `<${balise}>${enLigne(c.trim())}</${balise}>`).join("") + "</tr>";
      }).join("") + "</table>");
      tableau = [];
    };
    for (const brute of lignes) {
      const ligne = brute.replace(/^#{1,6}\s+/, "");
      const puce = ligne.match(/^\s*[-*•]\s+(.*)$/);
      const numero = ligne.match(/^\s*\d+[.)]\s+(.*)$/);
      if (/^\s*\|.*\|\s*$/.test(ligne)) { fermerParagraphe(); fermerListe(); tableau.push(ligne); continue; }
      fermerTableau();
      if (puce || numero) {
        fermerParagraphe();
        const type = puce ? "ul" : "ol";
        if (liste !== type) { fermerListe(); html.push(`<${type}>`); liste = type; }
        html.push(`<li>${enLigne((puce || numero)[1])}</li>`);
      } else if (!ligne.trim()) {
        fermerParagraphe(); fermerListe();
      } else {
        fermerListe(); paragraphe.push(ligne);
      }
    }
    fermerParagraphe(); fermerListe(); fermerTableau();
    return html.join("");
  },

  heure(iso) {
    if (!iso) return "";
    const d = new Date(iso);
    return d.toLocaleString("fr-FR", { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
  },

  // Ecran de code partage : resout quand l'acces est accorde, avec l'etat de session lu
  // (`etat` si l'acces etait deja accorde, sinon `nouvel`, relu apres la saisie du code). La barre de
  // navigation s'en sert pour l'espace parent (EX-206) sans rappeler /api/session.
  async porte(role, elements) {
    const etat = await MS.api("/api/session");
    if (etat[role]) return etat;
    elements.porte.classList.remove("cache");
    elements.contenu.classList.add("cache");
    elements.champ.focus();
    return new Promise((resoudre) => {
      elements.formulaire.addEventListener("submit", async (ev) => {
        ev.preventDefault();
        elements.erreur.textContent = "";
        try {
          await MS.api("/api/session", MS.json({ code: elements.champ.value }));
          const nouvel = await MS.api("/api/session");
          if (!nouvel[role]) { elements.erreur.textContent = "Ce code n'ouvre pas cette page."; return; }
          elements.porte.classList.add("cache");
          elements.contenu.classList.remove("cache");
          resoudre(nouvel);
        } catch (err) {
          elements.erreur.textContent = err.message === "code requis" ? "Code incorrect" : err.message;
          elements.champ.select();
        }
      });
    });
  },
};
