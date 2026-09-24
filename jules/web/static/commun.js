// Jules - fonctions communes aux pages eleve et parent.
// Securite : tout contenu venant du serveur ou du modele passe par MS.echapper (ou MS.markdown,
// qui echappe avant de mettre en forme) avant d'aller dans innerHTML.
"use strict";

const MS = {
  async api(chemin, options = {}) {
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

  json(corps, methode = "POST") {
    return { method: methode, headers: { "Content-Type": "application/json" }, body: JSON.stringify(corps) };
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

  // Ecran de code partage : resout quand l'acces est accorde.
  async porte(role, elements) {
    const etat = await MS.api("/api/session");
    if (etat[role]) return;
    elements.porte.classList.remove("cache");
    elements.contenu.classList.add("cache");
    elements.champ.focus();
    await new Promise((resoudre) => {
      elements.formulaire.addEventListener("submit", async (ev) => {
        ev.preventDefault();
        elements.erreur.textContent = "";
        try {
          await MS.api("/api/session", MS.json({ code: elements.champ.value }));
          const nouvel = await MS.api("/api/session");
          if (!nouvel[role]) { elements.erreur.textContent = "Ce code n'ouvre pas cette page."; return; }
          elements.porte.classList.add("cache");
          elements.contenu.classList.remove("cache");
          resoudre();
        } catch (err) {
          elements.erreur.textContent = err.message === "code requis" ? "Code incorrect" : err.message;
          elements.champ.select();
        }
      });
    });
  },
};
